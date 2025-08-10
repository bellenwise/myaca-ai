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

    ddb = boto3.resource(
        'dynamodb',
        region_name='ap-northeast-2',
        endpoint_url='http://localhost:8000'
    )

    sub, ok, e = extract_claim_sub(authorization)
    if not ok:
        logger.error(e)
        return UnauthorizedResponse

    # Get submission image from URL link
    submission = ddb.Table("assignment_submits").get_item(
        Key={"PK": f"ASSIGNMENT#{i_p_request.assignmentUuid}", "SK": f"{sub}#{i_p_request.problemId}"}
    )
    explanation = submission.get('Item', {}).get('Explanation', "")

    # Get solution from ddb-problems
    problem = ddb.Table("problems").get_item(
        Key={"PK": i_p_request.acaId, "SK": f"PROBLEM#{i_p_request.problemId}"}
    )
    solution = problem.get("Item", {}).get('Solution', '')

    # Request analysis to LLM with submission and solution
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5
    )

    parser = PydanticOutputParser(pydantic_object=AnalysisResult)

    analysis_prompt = """
        당신은 수학 교사입니다.
        다음은 학생의 문제 풀이 과정과 솔루션입니다.
        학생 풀이: {explanation}
        솔루션: {solution}

        위 두 풀이를 비교하여 다음 지침에 따라 분석해 주세요.
        1. 학생 풀이의 과정에 대해서 상세하게 설명해 주세요.
        2. 솔루션과 학생 풀이를 비교하여 틀리거나 다른 이유를 간결하게 요약해 주세요.

        {format_instructions}
    """
    prompt = PromptTemplate(
        template=analysis_prompt,
        input_variables=["explanation", "solution"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    llm_response = chain.run(
        explanation=explanation,
        solution=solution,
    )

    analysis_result = parser.parse(llm_response)

    # Request LLM to categorize incorrect_reason from submission_analysis
    parser = PydanticOutputParser(pydantic_object=ReasonResult)

    categorized_prompt = """
        당신은 수학 교사입니다.
        다음은 학생의 문제 풀이 분석 결과와 틀린 이유 리스트 입니다.
        문제 풀이 분석: {analysis_result}
        틀린 이유: {categories}

        문제 풀이 분석을 바탕으로 아래 지침에 따라 틀린 이유를 분류해 주세요.
        - 틀린 이유들 중, 분석 결과에 가장 근접한 틀린 한글 이유를 선택합니다.
        - 예시, 추론 실패

        {format_instructions}
        """
    prompt = PromptTemplate(
        template=categorized_prompt,
        input_variables=["analysis_result", "categories"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    llm_response = chain.run(
        analysis_result=analysis_result,
        categories=json.dumps(categories),
    )

    categorize_result = parser.parse(llm_response)


    # Update analysis into ddb-assignment_submits
    ddb.Table("assignment_submits").update_item(
        Key={"PK": f"ASSIGNMENT#{i_p_request.assignmentUuid}", "SK": f"sub1#{i_p_request.problemId}"},
        UpdateExpression="SET Analysis = :a, IncorrectReason = :ir",
        ExpressionAttributeValues={
            ":a": analysis_result.analysis,
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

    return SuccessResponse()



