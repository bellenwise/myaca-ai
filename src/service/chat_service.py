import boto3
import logging
import dotenv
from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
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
    )

    # Get submission from ddb-assignment_submits
    submission = get_submission(chat_request, sub)

    # Request to LLM to get response with problem and submission
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5
    )

    parser = PydanticOutputParser(pydantic_object=ChatResult)

    chat_prompt = """
            당신은 수학 교사입니다.
            다음은 학생이 제출한 답변과 문제, 그리고 학생의 질문 사항입니다.
            문제: {problem}
            학생이 제출한 답변: {submission}
            학생의 질문 사항: {question}

            문제와 학생이 제출한 답을 바탕으로 학생의 질문 사항을 다음과 같은 지침에 따라 분석해 주세요.
            단 질문 내용이 직접적으로 답변에 존재해서는 안됩니다. 
            1. 만약 학생이 제출한 답이 없거나 문제 풀이 분석 내용이 없다면 질문 사항에 답이 없다고 말하고, 질문 사항과 답에 대해서 적절히 답변을 생성해 주세요.
            2. 제출 사항이 있다면 문제의 정답과 솔루션을 바탕으로 학생의 질문에 상세히 답변해 주세요.
            3. 질문의 답변을 학생의 풀이 과정에 대한 분석 내용과 틀린 이유에 맞춰 요약해 주세요.
            4. 요약한 답변이 여전히 문제의 솔루션과 정답에 반하지 않는지 확인해 주세요.
            5. 문제의 정답과 학생의 정답이 같더라도 풀이과정이 틀렸다면, 학생의 풀이과정에 대한 분석 내용을 포함하여 답변해 주세요.
            6. 검증한 답변을 문장 단위로 행간 처리 하고 정리한 후 요약해 주세요.
            7. 요약한 내용을 마크다운 형식으로 수정해 주세요.

            {format_instructions}    
            """
    prompt = PromptTemplate(
        template=chat_prompt,
        input_variables=["problem", "submission", "question"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    llm_response = chain.run(
        problem=problem,
        submission=submission,
        question=chat_request.message,
    )

    chat_result = parser.parse(llm_response)

    return ChatResponse(
        message=chat_result.chat
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