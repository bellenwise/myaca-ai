from typing import List
import boto3
import dotenv
import langchain_openai
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException
from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from src.model.outputParser import ProblemAnalysisResult
from src.model.problem_model import ProblemStatsModel, AssignmentReview

ddb = boto3.resource("dynamodb", region_name="ap-northeast-2")

dotenv.load_dotenv()


def get_problem_stats(subdomain: str, problem_id: str) -> ProblemStatsModel:
    """
    Get statistics for a specific problem in a subdomain.

    Args:
        subdomain (str): The subdomain of the problem.
        problem_id (str): The ID of the problem.

    Returns:
        dict: A dictionary containing the problem statistics.
    """
    table = ddb.Table("problems")
    response = table.get_item(
        Key={"PK": subdomain, "SK": f"PROBLEM#{problem_id}"}
    )

    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="Problem not found")
    item = response['Item']

    total_solved = item.get('TotalSolved', 0)
    incorrect_count = item.get('IncorrectCount', 0)
    if total_solved == 0:
        correct_rate = None
    else:
        correct_rate = int(round((total_solved - incorrect_count) / total_solved * 100, 0))

    reason = item.get('Reason', {})

    return ProblemStatsModel(
        correctRate=correct_rate,
        reason=reason
    )


def get_analysis_summary(problem_id: str) -> str:
    table = ddb.Table("assignment_submits")
    response = table.query(
        IndexName="ProblemID-index",
        KeyConditionExpression=Key('ProblemID').eq(problem_id),
    )
    response_items = response.get('Items', [])
    analysis = [item.get('Analysis', "") for item in response_items]

    llm = langchain_openai.ChatOpenAI(
        model="gpt-4o",
        temperature=0.5,
    )

    parser = PydanticOutputParser(pydantic_object=ProblemAnalysisResult)
    problem_analysis_template = """
    당신은 수학 문제 풀이 분석가입니다.
    역할은 학생들의 과제 분석을 토대로 문제의 어떤 부분에 대해 학생들이 어려움을 겪는지 파악하고, 그에 대한 분석을 제공합니다.
    
    학생들의 과제: {analysis}
    
    {format_instructions}
    """
    problem_analysis_prompt = PromptTemplate(
        template=problem_analysis_template,
        input_variables=["analysis"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        }
    )
    chain = LLMChain(
        llm=llm,
        prompt=problem_analysis_prompt,
    )

    llm_response = chain.run(
        analysis=analysis,
    )
    problem_analysis_result = parser.parse(llm_response)

    return problem_analysis_result.analysis


def get_student_assignment_review(student_id: str, assignment_id: str) -> List[AssignmentReview]:
    table = ddb.Table("assignment_submits")
    response = table.query(
        KeyConditionExpression=Key('PK').eq(f"ASSIGNMENT#{assignment_id}") & Key('SK').begins_with(student_id)
    )

    if 'Items' not in response or not response['Items']:
        raise HTTPException(status_code=404, detail="No submissions found for the student")

    # Map the DynamoDB items to AssignmentReview objects
    return_items = [
        AssignmentReview(
            problemID=item.get('SK').split('#')[-1],
            reason=item.get('Reason', None),
            analysis=item.get('Analysis', None),
            explanation=item.get('Explanation', None),
        )
        for item in response['Items']
    ]

    return return_items
