from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.model.utils_model import TextResponse
from src.model.outputParser import ModifyResult, ValidResult

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.5
)


def text_validation(text: str) -> TextResponse :
    """
    LLM을 사용해 텍스트로 변환된 결과물에 대해, 사용 가능한지 검사합니다.

    Args:
        text: 이미지로부터 추출된 텍스트

    Outputs:
        if success: True, text
        Otherwise : False, ""
    """

    # Modify text
    parser = PydanticOutputParser(pydantic_object=ModifyResult)

    modify_template = """
        당신은 수학 보조강사합니다.
        다음은 학생이 제출한 답안의 풀이과정 입니다.
        풀이과정: {text}
        
        제출한 풀이과정을 바탕으로 다음의 분석 과정에 따라 분석해 주세요.
        1. 텍스트를 분석하면서 오탈자가 있는지 확인하고, 올바르게 수정해 주세요.
        2. 수정된 텍스트 중, 잘못 수정된 부분이 있는지 확인하고, 문제가 있다면 해당 부분을 원복해 주세요.
        
        {format_instructions}
    """

    modify_prompt = PromptTemplate(
        template=modify_template,
        input_variables=["text"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=modify_prompt)
    llm_response = chain.run(
        text=text,
    )

    modify_result = parser.parse(llm_response)

    # Validate text
    parser = PydanticOutputParser(pydantic_object=ValidResult)

    validate_template = """
            당신은 수학 보조강사합니다.
            다음은 학생이 제출한 답안의 풀이과정 입니다.
            풀이과정: {text}

            제출한 풀이과정을 바탕으로,
            해당 내용을 채점에 사용할 수 있을 정도로 읽을 수 있는지를
            다음의 기준을 따라 1 혹은 0으로 판단해 주세요.
            
            1. 제출된 풀이가 백지인지 판단해 주세요.
            2. 제출된 풀이가 문맥을 파악하기 힘든지 판단해 주세요.
            3. 읽음에 있어, 엉뚱한 문자나 숫자가 너무 많아 읽기가 힘든지 판단해 주세요.
            
            {format_instructions}
        """

    validate_prompt = PromptTemplate(
        template=validate_template,
        input_variables=["text"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )

    chain = LLMChain(llm=llm, prompt=validate_prompt)
    llm_response = chain.run(
        text=modify_result.text,
    )

    validate_result = parser.parse(llm_response)

    if validate_result.validity: return TextResponse(True, modify_result.text)
    else : return TextResponse(False, "")
