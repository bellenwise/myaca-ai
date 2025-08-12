import boto3
from typing import Dict
from src.model.response_model import BaseResponse, SuccessResponse


def get_assignment_analysis(assignment_id: str) -> BaseResponse:

    ddb = boto3.resource('dynamodb', region_name="ap-northeast-2")

    from boto3.dynamodb.conditions import Key
    assignments = ddb.Table("assignment_submits").query(
        KeyConditionExpression=Key("PK").eq(f"ASSGINMENT#{assignment_id}")
    ).get('Items', [])

    count = 0
    incorrectReasons :Dict[str, int] = {}

    for assignment in assignments:
        incorrectReason = assignment.get("IncorrectReason", "")
        if incorrectReason != "" :
            incorrectReasons[incorrectReason] += 1
            count += 1

    if count == 0:
        return SuccessResponse(
            message="No analysis"
        )
    else :
        return SuccessResponse(
            data={"IncorrectReasons": incorrectReasons}
        )



