import boto3
from fastapi import HTTPException

from src.model.problem_model import ProblemStatsModel

ddb = boto3.resource("dynamodb", region_name="ap-northeast-2")


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
    correct_rate = f'{total_solved - incorrect_count}/{total_solved}'
    incorrect_reason = item.get('IncorrectReason', {})

    return ProblemStatsModel(
        correctRate=correct_rate,
        incorrectReason=incorrect_reason
    )
