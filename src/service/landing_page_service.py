from typing import List
from fastapi import HTTPException
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from src.model.landing_page_model import LandingPageModel

ddb = boto3.resource(
    'dynamodb',
    region_name='ap-northeast-2',
)


def create_landing_page(subdomain: str, landing_page_request: LandingPageModel):
    """
    랜딩 페이지를 생성합니다.

    Args:
        subdomain (str): 서브도메인 이름.
        landing_page_request (List[LandingPageRequest]): 랜딩 페이지 요청 데이터 리스트.

    Returns:
        dict: 생성된 랜딩 페이지 정보.
    """
    if not subdomain or not landing_page_request:
        raise HTTPException(status_code=400, detail="Invalid input data")

    try:
        ddb.Table("landing_page").put_item(
            Item={
                "subdomain": subdomain,
                "hero": landing_page_request.hero,
                "section_1": landing_page_request.section_1,
                "section_2": landing_page_request.section_2,
                "section_3": landing_page_request.section_3,
            }
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to create landing page: {e}")

    return {"message": "success"}


def get_landing_page(subdomain: str) -> LandingPageModel:
    """
    랜딩 페이지 정보를 조회합니다.

    Args:
        subdomain (str): 서브도메인 이름.

    Returns:
        dict: 랜딩 페이지 정보.
    """
    if not subdomain:
        raise HTTPException(status_code=400, detail="Subdomain is required")

    try:
        response = ddb.Table("landing_page").get_item(
            Key={"subdomain": subdomain}
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve landing page: {e}")

    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="Landing page not found")

    item = response['Item']

    return LandingPageModel(
        hero=item.get("hero", ""),
        section_1=item.get("section_1", ""),
        section_2=item.get("section_2", ""),
        section_3=item.get("section_3", ""),
    )


def update_landing_page(subdomain: str, landing_page_request: LandingPageModel):
    """
    랜딩 페이지 정보를 업데이트합니다.

    Args:
        subdomain (str): 서브도메인 이름.
        landing_page_request (List[LandingPageRequest]): 랜딩 페이지 요청 데이터 리스트.

    Returns:
        dict: 업데이트된 랜딩 페이지 정보.
    """
    if not subdomain or not landing_page_request:
        raise HTTPException(status_code=400, detail="Invalid input data")

    try:
        ddb.Table("landing_page").update_item(
            Key={"subdomain": subdomain},
            UpdateExpression="SET hero = :hero, section_1 = :section_1, section_2 = :section_2, section_3 = :section_3",
            ExpressionAttributeValues={
                ":hero": landing_page_request.hero,
                ":section_1": landing_page_request.section_1,
                ":section_2": landing_page_request.section_2,
                ":section_3": landing_page_request.section_3,
            }
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to update landing page: {e}")

    return {"message": "success"}
