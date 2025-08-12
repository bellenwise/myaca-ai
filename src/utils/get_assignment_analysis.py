from collections import defaultdict

import boto3
from typing import Dict
from src.model.response_model import BaseResponse, SuccessResponse, InternalServerErrorResponse


def get_assignment_analysis(course_id: str, assignment_id: str) -> BaseResponse:

    ddb = boto3.resource('dynamodb', region_name="ap-northeast-2")

    from boto3.dynamodb.conditions import Key
    assignments = ddb.Table("assignment_submits").query(
        KeyConditionExpression=Key("PK").eq(f"ASSIGNMENT#{assignment_id}")
    ).get('Items', [])

    assignment_submits = ddb.Table("academies").query(
        KeyConditionExpression=Key("PK").eq(f"ASSIGNMENT#{assignment_id}")
    ).get("Items", [])

    print(assignments)

    counts = defaultdict(int)
    total_score = 0
    score_sum = 0
    ass_num = 0
    res_count = 0
    reasons = defaultdict(int)

    for submit in assignment_submits:
        ass_num += 1
        total_score = len(submit.get("Problems"))
        score_sum += submit.get("Score")
        count = submit.get("Count", 0)
        for key, value in count.items() :
            if key : counts[key] += 1

    for assignment in assignments:
        reason = assignment.get("Reason")
        print(reason)
        if reason :
            print(reason)
            reasons[reason] += 1
            res_count += 1

    if res_count == 0 :
        return InternalServerErrorResponse(
            message="no Analysis",
            data={
                "problemCounts": dict(counts),
                "score": total_score,
                "avg": int(score_sum)/ass_num
            }
        )
    else :
        return SuccessResponse(
            data={
                "reasons": dict(reasons),
                "problemCounts": counts,
                "score": total_score,
                "avgSum": int(score_sum)/ass_num
            }
        )



