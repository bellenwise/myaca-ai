from pyexpat.errors import messages

import boto3
import logging

from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.model.outputParser import *
from src.model.generate_model import GenerateRequest
from src.model.response_model import *
from src.utils.extract_claim_sub import extract_claim_sub

logger = logging.getLogger(__name__)

def  generate_problem(generateRequest: GenerateRequest, authorization: str):
    """
        AWS DynamoDB에서 학생의 과제 제출 결과를 조회하여 반환합니다.

        Args:
            analysisRequest: 과제 제출 정보가 담긴 AnalysisRequest 객체

        Returns:
            조회된 과제 제출 결과 데이터
        """

    ddb = boto3.resource('dynamodb')

    sub, ok, e = extract_claim_sub(authorization)
    if not ok:
        logger.error(e)
        return UnauthorizedResponse

    # Get Problem with acaID & problemID from ddb-problems
    problem = ddb.Table("problems").get_item(
        Key={"PK": generateRequest.acaID, "SK": f"PROBLEM#{generateRequest.problemId}"}
    )

    # Request to LLM that a kind of problem of selected problem
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5
    )

    parser = PydanticOutputParser(pydantic_object=GenerateResult)

    generate_prompt = """
        당신은 수학 교사입니다.
        다음은 문제, 문제를 틀린 학생들의 틀린 이유와 그 수입니다.
        문제: {problem}
        틀린 이유와 그 수: {incorrect_count}

        문제, 정답률, 틀린 이유를 바탕으로 다음과 같은 지침에 따라 문제와 비슷한 문제를 생성해 주세요.
        1. 총 제출자와 틀린 이유의 수를 기반으로 정답률을 고려해 문제의 복잡도를 전체 학생 수준의 중간으로 조정해 주세요.
        2. 틀린 이유와 그 수를 고려하여 가장 많이 틀린 이유를 훈련할 수 있도록 동일한 분야의 새 문제를 생성해 주세요.
        3. 새롭게 생성한 문제가 오류 혹은 잘못된 구조로 이루어졌는지 점검해 주세요.
        4. 정상적으로 점검된 문제를 정리하여 기존 문제와 같은 형식으로 만들어 주세요.

        {format_instructions}    
    """
    prompt = PromptTemplate(
        template=generate_prompt,
        input_variables=[problem, problem.IncorrecCount],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    llm_response = chain.run(
        problem=problem,
        IncorrectCount=problem.IncorrectCount,
    )

    generate_result = parser.parse(llm_response)

    # Request to LLM to make title of generated problem
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5
    )

    parser = PydanticOutputParser(pydantic_object=TitleResult)

    title_prompt = """
        당신은 수학 교사입니다.
        다음은 문제와 이를 바탕으로 새롭게 만들어진 문제입니다.
        문제: {problem}
        새로운 문제: {problem_result}

        문제를 바탕으로  다음과 같은 지침에 따라 문제의 제목을 생성해 주세요.
        1. 문제의 제목과 새로운 문제를 바탕으로 문제의 제목에 같은 형식의 제목을 작성해 주세요.
        2. 새롭게 지어진 제목에 오탈자가 없는지 확인해 주세요
        3. 확인한 제목을 가독성 있게 다듬어 주세요.

        {format_instructions}    
    """
    prompt = PromptTemplate(
        template=title_prompt,
        input_variables=[problem, generate_result],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    llm_response = chain.run(
        problem=problem,
        generate_result=generate_result,
    )

    # Formatting title and generated problem into problem-ddb-format
    ddb.Table("problems").put_item(
        Item={
            "PK": generateRequest.acaID,
            "SK": f"PROBLEM#{generateRequest.problemId}",
            "Category": generateRequest.category,
            "Name": generateRequest.name,
            "Choices": generateRequest.choices,
            "Answer": generateRequest.answers,
            "Question": generateRequest.question,
            "Tags": generateRequest.tags,
            "Type": generateRequest.type,
            "ImageURL": generateRequest.imageURL,
            "TotalSolved": generateRequest.totalSolved,
            "incoreectChain": generateRequest.incoreectChain,
            "Solution": generateRequest.solution,
        }
    )

    # return new ddb-formatted problem
    return BaseResponse(
        status_code=200,
        messages="Success",
        data = {
            "PK": generateRequest.acaID,
            "SK": f"PROBLEM#{generateRequest.problemId}",
            "Category": generateRequest.category,
            "Name": generateRequest.name,
            "Choices": generateRequest.choices,
            "Answer": generateRequest.answers,
            "Question": generateRequest.question,
            "Tags": generateRequest.tags,
            "Type": generateRequest.type,
            "ImageURL": generateRequest.imageURL,
            "TotalSolved": generateRequest.totalSolved,
            "incoreectChain": generateRequest.incoreectChain,
            "Solution": generateRequest.solution,
        }
    )

