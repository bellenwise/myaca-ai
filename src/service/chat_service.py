import boto3
import logging
import dotenv
from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from src.model.outputParser import *
from src.model.chat_model import ChatRequest, ChatResponse
from src.utils.extract_claim_sub import extract_claim_sub
from src.utils.guard_injection import guard_injection
from fastapi import HTTPException

logger = logging.getLogger(__name__)
dotenv.load_dotenv()

ddb = boto3.resource(
    'dynamodb',
    region_name='ap-northeast-2'
)


def response_chat(chat_request: ChatRequest, authorization: str) -> ChatResponse:
    """
    학생의 질문 사항과 문제, 학생의 제출물을 기반으로 학생의 질문에 대한 답을 리턴하는 함수
    Args:
        authorization:
        chat_request:

    Returns:

    """

    sub, ok, e = extract_claim_sub(authorization)
    if not ok:
        logger.error(e)
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing authorization token")

    # injection Guard
    if not guard_injection(chat_request.message):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Bad input detected"
        )

    # Get problem from ddb-problems
    problem = ddb.Table("problems").get_item(
        Key={"PK": chat_request.acaSubdomain, "SK": f"PROBLEM#{chat_request.problemId}"}
    ).get("Item", {})

    # Get submission from ddb-assignment_submits
    submission = get_submission(chat_request, sub)

    # Request to LLM to get response with problem and submission
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3
    )

    chat_template = """
        당신은 수학 교사입니다.
        다음은 학생이 제출한 답변과 문제, 그리고 학생의 질문 사항입니다.
        문제: {problem}
        학생이 제출한 풀이: {explanation}
        학생 풀이 분석: {analysis}
        학생의 질문 사항: {question}

        문제와 학생이 제출한 답을 바탕으로 학생의 질문 사항을 다음과 같은 지침에 따라 분석해 주세요.
        단 질문 내용이 직접적으로 답변에 존재해서는 안됩니다. 
        
        1. 만약 학생의 제출 풀이나 풀이 분석이 있다면 문제의 솔루션과 해당 내용을 기반으로 학생의 질문 내용에 답해주세요.
        2. 답변한 내용을 간결하게 핵심 위주로 요약해 주세요.

        {format_instructions}    
    """

    verify_template = """
        당신은 AI 질문의 답변을 정제하는 AI 답변 수정 부서의 사람입니다.
        다음은 AI가 생성한 답변과 학생의 질문입니다.
        
        학생의 질문: {question}
        AI 답변: {ai_response}

        다음의 내용에 따라 답변을 정제해 주세요.
        1. 답변이 학생의 질문 내용을 묻고 답하는 형식이 아닌 답변만을 포함하고 있는지 확인해 주세요.
        2. 답변의 설명이 너무 길거나 짧지 않은지 검토해 주세요.
        3. 답변 내용이 적절하다면 그대로 출력해 주세요.
        
        {format_instructions}
        [개선된 최종 답변]         
    """

    format_template = """
    당신은 콘텐츠 편집 전문가입니다. 다음 텍스트를 학생들이 읽기 쉽도록 명확하고 간결한 마크다운 형식으로 변환해주세요.
    - 중요한 개념이나 키워드는 **볼드체**로 강조해 주세요.
    - 목록이 필요하다면 순서 없는 리스트(-)를 사용해 주세요.
    - 전체적으로 친절하고 이해하기 쉬운 톤을 유지해 주세요.
    
    원본 텍스트: {verified_response}
    
    [마크 다운 형식의 최종 결과]
    """

    parser = PydanticOutputParser(pydantic_object=ChatResult)

    chat_prompt = PromptTemplate(
        template=chat_template,
        input_variables=["problem", "explanation", "analysis", "question"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    verification_prompt = PromptTemplate.from_template(
        template=verify_template,
    )
    format_prompt = PromptTemplate.from_template(
        template=format_template,
    )

    chat_chain = chat_prompt | llm | parser

    verification_chain = verification_prompt | llm | StrOutputParser()

    formatting_chain = format_prompt | llm | StrOutputParser()

    full_chain = (
        RunnablePassthrough.assign(
            chat_result=chat_chain
        ) | RunnablePassthrough.assign(
            verified_chat = (
                RunnableLambda(
                    lambda x: {
                        "problem": x["problem"],
                        "explanation": x["explanation"],
                        "generated_chat": x["generated_result"].chat,
                    }
                )
                | verification_chain
            )
        ) | RunnablePassthrough.assign(
            # 3. formatting_chain을 실행
            #    - 이전 단계에서 검증된 결과(verified_chat)를 포매팅 체인의 입력으로 전달
            formatted_message= (
                RunnableLambda(lambda x: {"verified_chat": x["verified_chat"]})
                | formatting_chain
            )
        )
    )

    result = full_chain.invoke(
        {
            "problem": problem,
            "explanation": submission["explanation"],
            "analysis": submission["analysis"],
            "question": chat_request.question,
        }
    )

    final_message = result['formatted_message']

    return ChatResponse(
        message=final_message,
    )


def get_submission(chat_request: ChatRequest, sub: str):
    submission = ddb.Table("assignment_submits").get_item(
        Key={
            "PK": f"ASSIGNMENT#{chat_request.assignmentUuid}",
            "SK": f"{sub}#{chat_request.problemId}"}
    )
    if 'Item' not in submission:
        logger.error(f"No submission found for user {sub} and problem {chat_request.problemId}")
        raise HTTPException(status_code=404, detail="Submission not found")

    return submission['Item']