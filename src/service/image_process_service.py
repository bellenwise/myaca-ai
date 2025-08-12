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
from src.utils.image2text import image2text
from src.utils.text_validation import text_validation
from src.model.utils_model import TextResponse

logger = logging.getLogger(__name__)
dotenv.load_dotenv()

def image_process(i_p_request: ImageProcessRequest):
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

    sub = i_p_request.studentId

    logger.info("text2image")

    # image2text
    try :
        converted_text = image2text(i_p_request.imageURL)
    except Exception as e :
        return InternalServerErrorResponse(message="failed to convert image to text")

    # Text Validity Check
    text_response : TextResponse = text_validation(converted_text)
    if not text_response.ok :
        logger.error(f"failed to text_validity {text_response.ok}")
        return InternalServerErrorResponse(message="failed to convert image to text")

    logger.info(f"text_response: {text_response}")

    # DDB interaction
    try :
        # Get solution from ddb-problems
        problem = ddb.Table("problems").get_item(
            Key={"PK": i_p_request.acaId, "SK": f"PROBLEM#{i_p_request.problemId}"}
        )
        solution = problem.get("Item", {}).get('Solution', '')

    except Exception as e :
        return InternalServerErrorResponse(message="failed to get item from ddb")

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

        만약 문제 풀이 내용이 없다면 분석을 종료하고 빈 문자열로 주세요.
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
        explanation=text_response.text,
        solution=solution,
    )

    analysis_result = parser.parse(llm_response)

    # Request LLM to categorize incorrect_reason from submission_analysis
    parser = PydanticOutputParser(pydantic_object=ReasonResult)

    categorized_prompt = """
        당신은 수학 교사입니다.
        다음은 학생의 문제 풀이 분석 결과와 이유 리스트 입니다.
        문제 풀이 분석: {analysis_result}
        이유: {categories}

        문제 풀이 분석을 바탕으로 아래 지침에 따라 이유를 분류해 주세요.
        맞았다면 정답으로 주세요.
        - 이유들 중, 분석 결과에 가장 근접한 한글 이유를 선택합니다.
            "개념 부족"
            "적용 오류"
            "문제 해석 오류" 
            "정보 누락/오독"
            "계산 실수"
            "논리적 오류"
            "선택지 오해"
            "추론 실패"
            "오타"
            "정답"
                    
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
        analysis_result=analysis_result.analysis,
        categories=json.dumps(categories),
    )

    categorize_result = parser.parse(llm_response)

    logger.info("chain complete")

    # Update analysis into ddb-assignment_submits
    try :
        ddb.Table("assignment_submits").update_item(
            Key={"PK": f"ASSIGNMENT#{i_p_request.assignmentUuid}", "SK": f"{sub}#{i_p_request.problemId}"},
            UpdateExpression="SET Analysis = :a, Reason = :ir, Explanation = :ex",
            ExpressionAttributeValues={
                ":a": analysis_result.analysis,
                ":ir": categorize_result.reason,
                ":ex": text_response.text,
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

    except Exception as e :
        return InternalServerErrorResponse(message="failed to update item to ddb")

    return SuccessResponse()



