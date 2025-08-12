import logging
import boto3
import dotenv
import os
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain.chains import SequentialChain, LLMChain
from langchain_core.messages import HumanMessage

from src.model.image_model import ImageProcessRequest
from src.model.response_model import (
    UnauthorizedResponse, BadRequestResponse,
    InternalServerErrorResponse, SuccessResponse
)
from src.model.outputParser import (
    AnalysisResult, ReasonResult,
    ModifyResult, ValidResult
)
from src.model.categories import categories
from src.model.utils_model import TextResponse
from src.utils.encode_image import encode_image_from_url, encode_image
from src.utils.extract_claim_sub import extract_claim_sub
from src.utils.validate_image import validate_image_url

logger = logging.getLogger(__name__)
dotenv.load_dotenv()

# ---- 공통 LLM ----
llm = ChatOpenAI(model="gpt-4o", temperature=0.5)


# ---- 이미지 → 텍스트 변환 ----
def get_image_text(image_b64: str) -> str:
    image2text_prompt = """
    아래 이미지에서 모든 텍스트를 추출해 주세요.

    - 여러 줄이면 순서 지켜서 추출
    - 필기 방향/기울기 무시하고 올바른 순서로 읽기
    - 오타 최소화
    - 수학 풀이 수식은 Latex 문법으로 변환 후 텍스트로 변환
    """
    message = HumanMessage(
        content=[
            {"type": "text", "text": image2text_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]
    )
    return llm.invoke([message]).content


# ---- 텍스트 수정 + 유효성 검증 ----
def validate_and_modify_text(text: str) -> TextResponse:
    # 1. 수정 체인
    modify_parser = PydanticOutputParser(pydantic_object=ModifyResult)
    modify_prompt = PromptTemplate(
        template="""
        당신은 수학 보조강사입니다.
        다음은 학생이 제출한 답안의 풀이과정입니다.
        풀이과정: {text}

        분석 과정:
        1. 텍스트의 오탈자를 수정
        2. 잘못 수정된 부분이 있다면 원복

        {format_instructions}
        """,
        input_variables=["text"],
        partial_variables={"format_instructions": modify_parser.get_format_instructions()}
    )
    modify_chain = LLMChain(llm=llm, prompt=modify_prompt, output_parser=modify_parser)
    modify_result = modify_chain.run(text=text)

    # 2. 유효성 검증 체인
    valid_parser = PydanticOutputParser(pydantic_object=ValidResult)
    validate_prompt = PromptTemplate(
        template="""
        당신은 수학 보조강사입니다.
        다음은 학생이 제출한 답안의 풀이과정입니다.
        풀이과정: {text}

        아래 기준으로 채점 가능 여부를 1 또는 0으로 판단:
        1. 백지 여부
        2. 문맥 파악 가능 여부
        3. 엉뚱한 문자/숫자가 너무 많아 읽기 어려운지 여부

        {format_instructions}
        """,
        input_variables=["text"],
        partial_variables={"format_instructions": valid_parser.get_format_instructions()}
    )
    validate_chain = LLMChain(llm=llm, prompt=validate_prompt, output_parser=valid_parser)
    validate_result = validate_chain.run(text=modify_result.text)

    if validate_result.validity:
        return TextResponse(True, modify_result.text)
    else:
        return TextResponse(False, "")


# ---- 분석 체인 ----
def create_analysis_chain() -> LLMChain:
    parser = PydanticOutputParser(pydantic_object=AnalysisResult)
    prompt = PromptTemplate(
        template="""
        당신은 수학 교사입니다.
        다음은 학생의 문제 풀이와 솔루션입니다.
        학생 풀이: {explanation}
        솔루션: {solution}

        분석:
        1. 학생 풀이 과정 상세 설명
        2. 솔루션과 비교하여 차이/오류 요약

        {format_instructions}
        """,
        input_variables=["explanation", "solution"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return LLMChain(llm=llm, prompt=prompt, output_parser=parser)


# ---- 분류 체인 ----
def create_categorization_chain() -> LLMChain:
    parser = PydanticOutputParser(pydantic_object=ReasonResult)
    prompt = PromptTemplate(
        template="""
        당신은 수학 교사입니다.
        다음은 문제 풀이 분석과 틀린 이유 카테고리입니다.
        분석 결과: {analysis_result}
        카테고리: {categories}

        분석 결과에 가장 근접한 틀린 이유(한글) 선택
        예: 추론 실패, 계산 실수

        {format_instructions}
        """,
        input_variables=["analysis_result", "categories"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return LLMChain(llm=llm, prompt=prompt, output_parser=parser)


# ---- 메인 프로세스 ----
def image_process(i_p_request: ImageProcessRequest, authorization: str):
    # DynamoDB init
    ddb = boto3.resource('dynamodb', region_name='ap-northeast-2')

    # 1. 인증
    sub, ok, e = extract_claim_sub(authorization)
    if not ok:
        logger.error(e)
        return UnauthorizedResponse(message="failed to authorize cognito claims")

    # 2. 이미지 URL 체크
    if not validate_image_url(i_p_request.imageURL):
        return BadRequestResponse(message="invalid URL")

    # 3. 이미지 → 텍스트
    try:
        if i_p_request.imageURL.startswith(("http://", "https://")):
            base64_image = encode_image_from_url(i_p_request.imageURL)
        else:
            if not os.path.exists(i_p_request.imageURL):
                return BadRequestResponse(message="invalid file path")
            base64_image = encode_image(i_p_request.imageURL)
        extracted_text = get_image_text(base64_image)
    except Exception as e:
        logger.error(f"Image to text failed: {e}")
        return InternalServerErrorResponse(message="failed to convert image to text")

    # 4. 텍스트 유효성 검증/수정
    validation_result = validate_and_modify_text(extracted_text)
    if not validation_result.validity:
        return InternalServerErrorResponse(message="invalid extracted text")

    # 5. DDB 데이터 로드
    try:
        submission = ddb.Table("assignment_submits").get_item(
            Key={"PK": f"ASSIGNMENT#{i_p_request.assignmentUuid}",
                 "SK": f"{sub}#{i_p_request.problemId}"}
        )
        problem = ddb.Table("problems").get_item(
            Key={"PK": i_p_request.acaId,
                 "SK": f"PROBLEM#{i_p_request.problemId}"}
        )
        solution = problem.get("Item", {}).get('Solution', '')
    except Exception as e:
        logger.error(f"DDB fetch failed: {e}")
        return InternalServerErrorResponse(message="failed to get item from ddb")

    # 6. 분석 + 분류 실행
    try:
        analysis_chain = create_analysis_chain()
        categorization_chain = create_categorization_chain()

        pipeline = SequentialChain(
            chains=[analysis_chain, categorization_chain],
            input_variables=["explanation", "solution", "categories"],
            output_variables=["analysis", "reason"],
            verbose=True
        )

        result = pipeline({
            "explanation": validation_result.text,
            "solution": solution,
            "categories": json.dumps(categories)
        })

        analysis_result = result["analysis"]
        categorize_result = result["reason"]

    except Exception as e:
        logger.error(f"LangChain pipeline failed: {e}")
        return InternalServerErrorResponse(message="failed to process analysis")

    # 7. DDB 업데이트
    try:
        ddb.Table("assignment_submits").update_item(
            Key={"PK": f"ASSIGNMENT#{i_p_request.assignmentUuid}",
                 "SK": f"{sub}#{i_p_request.problemId}"},
            UpdateExpression="SET Analysis = :a, IncorrectReason = :ir",
            ExpressionAttributeValues={
                ":a": analysis_result,
                ":ir": categorize_result
            }
        )

        item = problem.get("Item", {})
        inc = item.get("IncorrectCount", {})
        inc[categorize_result] = inc.get(categorize_result, 0) + 1

        ddb.Table("problems").update_item(
            Key={"PK": i_p_request.acaId,
                 "SK": f"PROBLEM#{i_p_request.problemId}"},
            UpdateExpression="SET IncorrectCount = :inc",
            ExpressionAttributeValues={":inc": inc}
        )
    except Exception as e:
        logger.error(f"DDB update failed: {e}")
        return InternalServerErrorResponse(message="failed to update item to ddb")

    return SuccessResponse()
