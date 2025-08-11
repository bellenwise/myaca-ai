import boto3
import logging
import dotenv
import langchain_openai
from fastapi import Header
from boto3.dynamodb.conditions import Key
from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from src.model.assignment_model import AssignmentAnalysisRequest
from src.model.outputParser import AssignmentAnalysisResult
from src.model.response_model import BaseResponse, SuccessResponse, UnauthorizedResponse
from src.utils.extract_claim_sub import extract_claim_sub

logger = logging.getLogger(__name__)
dotenv.load_dotenv()

def analyze_assignment(a_a_request: AssignmentAnalysisRequest, authorization: str = Header(None)) -> BaseResponse:
    """
    학생들이 제출한 과제들에 대한 AI 분석 및 통계를 내는 함수
    Args:
        a_a_request: 과제 분석 요청
            - acaId
            - assignmentId

        authorization: 헤더

    Returns:
        if success : SuccessResponse
            {
                "acaId": str,                   # 학원 ID
                "assignmentId": str,            # 과제 ID
                "score_avg": float 또는 str,     # 과제 평균 점수 (LLM 분석 결과)
                "analysis": str,                # 과제 성취도 및 개선점 분석 요약
                "IncorrectReasons": dict       # 틀린 이유별 통산 카운트 맵, 예: {"개념 부족": 3, "오타": 1}
            }
        Otherwise, return InternalConflictResponse

    """

    # init


    llm = langchain_openai.ChatOpenAI(
        model="gpt-4o",
        temperature=0.5,
    )

    ddb = boto3.resource(
        service_name="dynamodb",
        region_name="ap-northeast-2"
    )

    # Authentification
    sub, ok, e = extract_claim_sub(authorization)
    if not ok:
        logger.error(e)
        return UnauthorizedResponse()

    # Get Assignment Meta form ddb-assignment_submits
    # assignment_meta = ddb.Table("assignment_submits").get_item(
    #     Key={
    #         "PK": f"ASSIGNMENT#{a_a_request.assignmentId}",
    #     },
    # )

    #  Get all Assignments from ddb-academies
    assignment_submissions = ddb.Table("academies").query(
        KeyConditionExpression = Key('PK').eq(f"ASSIGNMENT#{a_a_request.assignmentId}")
    )

    # Request to LLM to analyze Assignment
    parser = PydanticOutputParser(pydantic_object=AssignmentAnalysisResult)

    assignment_analysis_template = """
    당신은 수학 교사 중, 상급자입니다.
    역할은 학생들의 통계치와 과제 내용을 바탕으로 과제 수준이나 반의 성취도를 분석하는 것입니다.
    과제의 총점은 과제 내의 문제 개수와 같습니다.
    
    제출물: {assignment_submissions}
    
    제출물과 과제 메타 데이터를 바탕으로 다음 지침에 따라 과제를 분석해 주세요.
    1. 과제들의 평균 점수를 내고, 그 평균을 통해 학생들의 과제에 대한 성취 수준을 평가해 주세요.
    2. 과제 내 문제들의 틀린 수와 틀린 이유를 통산해 틀린 이유 별로 카운트 해주세요.
    3. 과제의 틀린 이유 통산 값을 바탕으로 다음에 과제를 낼 때 주의하거나 개선해야 할 사항을 분석해 주세요.
    4. 과제의 성취 수준 분석 결과와 과제 분석 사항을 순서대로 요약해 주세요.
    5. 요약된 분석과 과제의 문제들의 틀린 총 개수, 과제에서 틀린 이유의 통산 맵,과제 평균 점수, 총점을 차레로 전달해 주세요.
    
    {format_instructions}
    """

    assignment_analysis_prompt = PromptTemplate(
        template=assignment_analysis_template,
        input_variables=["assignment_submissions"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(
        llm=llm,
        prompt=assignment_analysis_prompt,
    )

    llm_response = chain.run(
        assignment_submissions=assignment_submissions,
    )

    assignment_analysis_result = parser.parse(llm_response)

    # update item ddb-academies
    ddb.Table("assignment_submits").put_item(
        Item={
            "PK": f"ASSIGNMENT#{a_a_request.assignmentId}",
            "SK": "INFO",
            "IncorrectCount": assignment_analysis_result.incorrect_count,
            "IncorrectReason": assignment_analysis_result.incorrect_reasons,  # 변수명 확인 필요
            "Analysis": assignment_analysis_result.analysis,
            "Avg": f"{assignment_analysis_result.score_avg}/{assignment_analysis_result.total_count}",
        },
    )

    return SuccessResponse(
            data={
                "acaId": a_a_request.acaId,
                "assignmentId": a_a_request.assignmentId,
                "score_avg": assignment_analysis_result.score_avg,
                "analysis": assignment_analysis_result.analysis,
                "IncorrectReasons": assignment_analysis_result.incorrect_reasons,
            }
        )
