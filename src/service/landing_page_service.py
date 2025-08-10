from typing import List
from fastapi import HTTPException
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.model.landing_page_model import LandingPageRequest

ddb = boto3.resource(
    'dynamodb',
    region_name='ap-northeast-2',
)


def create_landing_page(subdomain: str, landing_page_request: List[LandingPageRequest]):
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
        imageUrls = [req.image_url for req in landing_page_request]
        titles = [req.title for req in landing_page_request]
        descriptions = [req.description for req in landing_page_request]

        ddb.Table("landing_page").put_item(
            Item={
                "subdomain": subdomain,
                "imageUrls": imageUrls,
                "titles": titles,
                "descriptions": descriptions
            }
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to create landing page: {e}")

    return {"message": "success"}


def get_landing_page(subdomain: str) -> List[LandingPageRequest]:
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
    image_urls = item.get("imageUrls", [])
    titles = item.get("titles", [])
    descriptions = item.get("descriptions", [])

    return [
        LandingPageRequest(
            title=title,
            description=desc,
            image_url=url
        )
        for title, desc, url in zip(titles, descriptions, image_urls)
    ]


def update_landing_page(subdomain: str, landing_page_request: List[LandingPageRequest]):
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
        imageUrls = [req.image_url for req in landing_page_request]
        titles = [req.title for req in landing_page_request]
        descriptions = [req.description for req in landing_page_request]

        ddb.Table("landing_page").update_item(
            Key={"subdomain": subdomain},
            UpdateExpression="SET imageUrls = :imageUrls, titles = :titles, descriptions = :descriptions",
            ExpressionAttributeValues={
                ":imageUrls": imageUrls,
                ":titles": titles,
                ":descriptions": descriptions
            }
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to update landing page: {e}")

    return {"message": "success"}
