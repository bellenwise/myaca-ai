from typing import List
import boto3
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException
from src.model.problem_model import ProblemStatsModel, AssignmentReview

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
    if total_solved == 0:
        correct_rate = None
    else:
        correct_rate = int(round((total_solved - incorrect_count) / total_solved * 100, 0))

    reason = item.get('reason', {})

    return ProblemStatsModel(
        correctRate=correct_rate,
        Reason=reason
    )


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
            questionId=item.get('SK').split('#')[-1],
            Reason=item.get('Reason', None),
            analysis=item.get('Analysis', None)
        )
        for item in response['Items']
    ]

    return return_items
