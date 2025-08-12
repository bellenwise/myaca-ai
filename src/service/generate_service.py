import boto3
import logging
import dotenv
import uuid
from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.model.outputParser import *
from src.model.generate_model import GenerateRequest
from src.model.response_model import *
from src.utils.extract_claim_sub import extract_claim_sub

logger = logging.getLogger(__name__)
dotenv.load_dotenv()

def  generate_problem(generate_request: GenerateRequest) -> BaseResponse:
    """
        비슷한 문제 생성

        Args:
            generate_request :
                - aca_id
                - problemID

        Returns:
            조회된 과제 제출 결과 데이터
        """

    ddb = boto3.resource(
        'dynamodb',
        region_name='ap-northeast-2'
    )

    # Get Problem with acaID & problemID from ddb-problems
    problem = ddb.Table("problems").get_item(
        Key={"PK": generate_request.acaId, "SK": f"PROBLEM#{generate_request.problemId}"}
    ).get('Item')

    # Request to LLM that a kind of problem of selected problem
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5
    )

    parser = PydanticOutputParser(pydantic_object=GenerateResult)

    new_problem_id = uuid.uuid4().hex
    generate_prompt = """
        당신은 수학 교사입니다.
        다음은 문제, 문제를 틀린 학생들의 틀린 이유와 그 수입니다.
        문제: {problem}
        틀린 이유와 그 수: {IncorrectReasons}

        문제, 정답률, 틀린 이유를 바탕으로 다음과 같은 지침에 따라 문제와 비슷한 문제를 생성해 주세요.
        1. 총 제출자와 틀린 이유의 수를 기반으로 정답률을 고려해 문제의 복잡도를 전체 학생 수준의 중간으로 조정해 주세요.
        2. 틀린 이유와 그 수를 고려하여 가장 많이 틀린 이유를 훈련할 수 있도록 동일한 분야의 새 문제를 생성해 주세요.
        3. 새롭게 생성한 문제가 오류 혹은 잘못된 구조로 이루어졌는지 점검해 주세요.
        4. 정상적으로 점검된 문제를 정리하여 기존 문제와 같은 형식으로 만들어 주세요.
        5. 생성된 모든 내용을 한글로 번역해 주세요.

        {format_instructions}    
    """
    prompt = PromptTemplate(
        template=generate_prompt,
        input_variables=["problem", "IncorrectReasons"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    llm_response = chain.run(
        problem=problem,
        IncorrectReasons=problem.get('IncorrectReasons'),
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
        새로운 문제: {generate_result}

        문제를 바탕으로  다음과 같은 지침에 따라 문제의 제목을 생성해 주세요.
        1. 문제의 제목과 새로운 문제를 바탕으로 문제의 제목에 같은 형식의 제목을 작성해 주세요.
        2. 새롭게 지어진 제목에 오탈자가 없는지 확인해 주세요
        3. 확인한 제목을 가독성 있게 다듬어 주세요.
        
        {format_instructions}    
    """
    prompt = PromptTemplate(
        template=title_prompt,
        input_variables=["problem", "generate_result"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    llm_response = chain.run(
        problem=problem,
        generate_result=generate_result,
    )

    title_result = parser.parse(llm_response)

    # Formatting title and generated problem into problem-ddb-format
    response_item = {
            "pk": generate_request.acaId,
            "sk": f"PROBLEM#{new_problem_id}",
            "category": generate_result.category,
            "name": title_result.title,
            "choices": generate_result.choices,
            "answer": generate_result.answers,
            "question": generate_result.question,
            "tags": generate_result.tags,
            "type": generate_result.type,
            "imageURL": generate_result.imageURL,
            "totalSolved": 0,
            "incorrectCount": 0,
            "incorrectReasons": {
                "개념 부족" : 0,
                "적용 오류" : 0,
                "문제 해석 오류" : 0,
                "정보 누락/오독" : 0,
                "계산 실수" : 0,
                "논리적 오류" : 0,
                "선택지 오해" : 0,
                "추론 실패" : 0,
                "오타" : 0,
            },
            "solution": generate_result.solution,
        }

    # ddb.Table("problems").put_item(
    #     Item= response_item,
    #     ConditionExpression="attribute_not_exists(SK)"
    # )

    # return new ddb-formatted problem
    return SuccessResponse(
        data = response_item
    )

