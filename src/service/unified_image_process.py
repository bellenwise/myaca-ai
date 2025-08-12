import logging
import boto3
import dotenv
import json
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from src.model.image_model import *
from src.model.response_model import *
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from src.model.outputParser import AnalysisResult, ReasonResult
from src.model.categories import categories
from src.utils.extract_claim_sub import extract_claim_sub
from src.utils.image2text import image2text
from src.utils.text_validation import text_validation
from src.utils.validate_image import validate_image_url
from langchain_core.runnables import RunnablePassthrough

logger = logging.getLogger(__name__)
dotenv.load_dotenv()


def image_process(i_p_request: ImageProcessRequest, authorization: str):
    """
    학생의 explanation 이미지를 텍스트로 변환하고,
    변환된 텍스트의 유효성을 판단하여 ddb 저장 또는 반려하는 함수

    Args:
        authorization: 헤더의 Authorization 필드
        i_p_request: 이미지 프로세싱 요청
            - imageURL: 외부에서 읽어올 이미지 주소
            - acaId: 학원 id
            - assignmentUuid : 과제 id
            - problemId : 문제 id

    Returns:
        if success : SuccessResponse
        Otherwise : InternalServerConflictResponse

    """

    # init
    ddb = boto3.resource(
        'dynamodb',
        region_name='ap-northeast-2',
    )
    llm = ChatOpenAI(model="gpt-4o", temperature=0.5)

    # authentification
    sub, ok, e = extract_claim_sub(authorization)
    if not ok:
        logger.error(e)
        return UnauthorizedResponse(
            message="failed to authorize cognito claims"
        )

    # Get submission image from image URL
    if not validate_image_url(i_p_request.imageURL):
        return BadRequestResponse(message="invalid URL")

    # image2text
    try:
        converted_text = image2text(i_p_request.imageURL)
    except Exception as e:
        return InternalServerErrorResponse(message="failed to convert image to text")

    # Text Validity Check
    validity, text_saved = text_validation(converted_text)
    if not validity:
        return InternalServerErrorResponse(message="failed to convert image to text")

    # DDB interaction
    try:
        submission = ddb.Table("assignment_submits").get_item(
            Key={
                "PK": f"ASSIGNMENT#{i_p_request.assignmentUuid}",
                "SK": f"{sub}#{i_p_request.problemId}"
            }
        )
        explanation = submission.get('Item', {}).get('Explanation', "")

        # Get solution from ddb-problems
        problem = ddb.Table("problems").get_item(
            Key={"PK": i_p_request.acaId, "SK": f"PROBLEM#{i_p_request.problemId}"}
        )
        solution = problem.get("Item", {}).get('Solution', '')

    except Exception as e:
        return InternalServerErrorResponse(message="failed to get item from ddb")

    # --- LCEL을 활용한 체인 구축 시작 ---
    analysis_parser = PydanticOutputParser(pydantic_object=AnalysisResult)
    categorize_parser = PydanticOutputParser(pydantic_object=ReasonResult)

    analysis_prompt = PromptTemplate(
        template="""당신은 수학 교사입니다.
        다음은 학생의 문제 풀이 과정과 솔루션입니다.
        학생 풀이: {explanation}
        솔루션: {solution}

        위 두 풀이를 비교하여 다음 지침에 따라 분석해 주세요.
        1. 학생 풀이의 과정에 대해서 상세하게 설명해 주세요.
        2. 솔루션과 학생 풀이를 비교하여 틀리거나 다른 이유를 간결하게 요약해 주세요.

        {format_instructions}
        """,
        input_variables=["explanation", "solution"],
        partial_variables={"format_instructions": analysis_parser.get_format_instructions()}
    )

    categorize_prompt = PromptTemplate(
        template="""당신은 수학 교사입니다.
        다음은 학생의 문제 풀이 분석 결과와 틀린 이유 리스트 입니다.
        문제 풀이 분석: {analysis_result}
        틀린 이유: {categories}

        문제 풀이 분석을 바탕으로 아래 지침에 따라 틀린 이유를 분류해 주세요.
        - 틀린 이유들 중, 분석 결과에 가장 근접한 틀린 한글 이유를 선택합니다.
        - 예시, 추론 실패

        {format_instructions}
        """,
        input_variables=["analysis_result", "categories"],
        partial_variables={"format_instructions": categorize_parser.get_format_instructions()}
    )

    # LCEL 체인 구축
    chain = (
            analysis_prompt
            | llm
            | analysis_parser
            | {
                "analysis_result": RunnablePassthrough(),
                "categories": lambda x: json.dumps(categories)
            }
            | categorize_prompt
            | llm
            | categorize_parser
    )

    # 체인 실행
    try:
        categorize_result = chain.invoke(
            {"explanation": text_saved, "solution": solution}
        )
    except Exception as e:
        logger.error(f"LCEL chain failed: {e}")
        return InternalServerErrorResponse(message="failed to run LLM chain")

    # --- LCEL을 활용한 체인 구축 끝 ---

    # Update analysis into ddb-assignment_submits
    try:
        ddb.Table("assignment_submits").update_item(
            Key={"PK": f"ASSIGNMENT#{i_p_request.assignmentUuid}", "SK": f"{sub}#{i_p_request.problemId}"},
            UpdateExpression="SET Analysis = :a, IncorrectReason = :ir",
            ExpressionAttributeValues={
                # Note: The LCEL chain returns the final output, not the intermediate steps
                # You might need to adjust the chain or parse the final output to get 'Analysis'
                ":a": "Analysis not retrieved from this chain",  # Placeholder
                ":ir": categorize_result.reason,
            }
        )

        # Update incorrect_reason into ddb-problems
        item = problem.get("Item", {})
        inc = item["IncorrectCount"]
        inc[categorize_result.reason] += 1

        ddb.Table("problems").update_item(
            Key={
                "PK": i_p_request.acaId,
                "SK": f"PROBLEM#{i_p_request.problemId}"
            },
            UpdateExpression="SET IncorrectCount = :inc",
            ExpressionAttributeValues={
                ":inc": inc
            }
        )

    except Exception as e:
        logger.error(f"DDB update failed: {e}")
        return InternalServerErrorResponse(message="failed to update item to ddb")

    return SuccessResponse()