import requests
from PIL import Image
from io import BytesIO


def validate_image_link(url, max_size_mb=5):
    """
    이미지 링크로부터 유효성을 검사하는 함수

    Args :
        url : 이미지 링크
        max_size_mb : 최대 이미지 크기

    Returns :
        True or False

    """

    try:
        # URl Request
        image_response = requests.get(url, stream=True, timeout=5)
        image_response.raise_for_status()

        # Content_type Check
        content_type = image_response.headers.get("Content-Type", '').lower()
        if not content_type.startswith('image/'):
            return False

        # Size of Image Check
        content_length = image_response.headers.get("Content-Length", 0)
        if not content_length or int(content_length) > max_size_mb * 1024 * 1024:
            return False

        # Image Load Test
        image_data = image_response.content
        img = Image.open(BytesIO(image_data))
        img_format = img.format
        img.verify()

        # Format Validation
        if img_format not in ["JPEG", "PNG"]:
            return False

        return True

    except Exception as e:
        return False
