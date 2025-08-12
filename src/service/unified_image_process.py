import logging
import boto3
import dotenv
import json
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from src.model.image_model import *
from src.model.response_model import *
from langchain_openai import ChatOpenAI
from src.model.outputParser import AnalysisResult, ReasonResult
from src.model.categories import categories
from src.utils.image2text import image2text
from src.utils.text_validation import text_validation
from src.model.utils_model import TextResponse

logger = logging.getLogger(__name__)
dotenv.load_dotenv()


def unififed_image_process(i_p_request: ImageProcessRequest):
    """
    학생의 explanation 이미지를 텍스트로 변환하고,
    변환된 텍스트를 단일 체인으로 분석 및 분류하여 ddb에 저장하는 함수
    (LCEL 단일 체인 방식으로 리팩토링됨)

    Args:
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
    ddb = boto3.resource('dynamodb', region_name='ap-northeast-2')
    llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
    sub = i_p_request.studentId
    data = {}

    # image2text
    try:
        converted_text = image2text(i_p_request.imageURL)
    except Exception as e:
        logger.error(f"Image to text conversion failed: {e}")
        return InternalServerErrorResponse(message="failed to convert image to text")

    # Text Validity Check
    text_response: TextResponse = text_validation(converted_text)
    if not text_response.ok:
        return InternalServerErrorResponse(message="failed to convert image to text")
    data["text_response_ok"] = "true" # Todo

    # DDB interaction
    try:
        problem = ddb.Table("problems").get_item(
            Key={"PK": i_p_request.acaId, "SK": f"PROBLEM#{i_p_request.problemId}"}
        )
        solution = problem.get("Item", {}).get('Solution', '')
    except Exception as e:
        logger.error(f"Failed to get item from ddb: {e}")
        return InternalServerErrorResponse(message="failed to get item from ddb")

    # --- LCEL 단일 체인 구성 ---

    # 1. 분석(Analysis) 단계의 구성요소 정의
    analysis_parser = PydanticOutputParser(pydantic_object=AnalysisResult)
    analysis_prompt = PromptTemplate(
        template="""
        당신은 수학 교사입니다.
        다음은 학생의 문제 풀이 과정과 솔루션입니다.
        학생 풀이: {explanation}
        솔루션: {solution}

        만약 문제 풀이 내용이 없다면 분석을 종료하고 빈 문자열로 주세요.
        위 두 풀이를 비교하여 다음 지침에 따라 분석해 주세요.
        1. 학생 풀이의 과정에 대해서 상세하게 설명해 주세요.
        2. 솔루션과 학생 풀이를 비교하여 틀리거나 다른 이유를 간결하게 요약해 주세요.

        {format_instructions}
        """,
        input_variables=["explanation", "solution"],
        partial_variables={"format_instructions": analysis_parser.get_format_instructions()}
    )
    analysis_sub_chain = analysis_prompt | llm | analysis_parser
    data["anal_chain"] = "true"  # Todo
    # 2. 분류(Categorization) 단계의 구성요소 정의
    reason_parser = PydanticOutputParser(pydantic_object=ReasonResult)
    categorized_prompt = PromptTemplate(
        template="""
        당신은 수학 교사입니다.
        다음은 학생의 문제 풀이 분석 결과와 틀린 이유 리스트 입니다.
        문제 풀이 분석: {analysis_result}
        틀린 이유: {categories}

        문제 풀이 분석을 바탕으로 아래 지침에 따라 틀린 이유를 분류해 주세요.
        문제 풀이 내용이 없다면 틀린 이유를 기타로 주세요.
        - 틀린 이유들 중, 분석 결과에 가장 근접한 틀린 한글 이유를 선택합니다.
            "개념 부족", "적용 오류", "문제 해석 오류", "정보 누락/오독", "계산 실수",
            "논리적 오류", "선택지 오해", "추론 실패", "오타", "기타"

        {format_instructions}
        """,
        input_variables=["analysis_result", "categories"],
        partial_variables={"format_instructions": reason_parser.get_format_instructions()}
    )
    categorization_sub_chain = categorized_prompt | llm | reason_parser
    data["cat_chain"] = "true"  # Todo
    # 3. 두 단계를 RunnablePassthrough.assign을 사용하여 하나의 체인으로 연결
    combined_chain = RunnablePassthrough.assign(
        analysis_data=analysis_sub_chain
    ).assign(
        reason_data=lambda x: {
            "analysis_result": x["analysis_data"].analysis,
            "categories": x["categories"]
            } | categorization_sub_chain
    )
    data["runnable_through"] = "true"  # Todo

    # 단일 체인 실행
    result = combined_chain.invoke({
        "explanation": text_response.text,
        "solution": solution,
        "categories": json.dumps(categories)
    })

    analysis_result = result['analysis_data']
    categorize_result = result['reason_data']

    data["complete"] = "true"  # Todo
    # Update analysis into ddb-assignment_submits
    try:
        ddb.Table("assignment_submits").update_item(
            Key={"PK": f"ASSIGNMENT#{i_p_request.assignmentUuid}", "SK": f"{sub}#{i_p_request.problemId}"},
            UpdateExpression="SET Analysis = :a, IncorrectReason = :ir, Explanation = :ex",
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
            Key={"PK": i_p_request.acaId, "SK": f"PROBLEM#{i_p_request.problemId}"},
            UpdateExpression="SET IncorrectCount = :inc",
            ExpressionAttributeValues={":inc": inc}
        )
    except Exception as e:
        logger.error(f"Failed to update item to ddb: {e}")
        return InternalServerErrorResponse(message="failed to update item to ddb")

    return SuccessResponse(
        data=data,
    )