import base64

# Encode Image into Base64
def encode_image(image_path: str) -> str:
    """
           파일 경로에서 이미지를 다운로드하여 Base64로 인코딩합니다.

           Args:
               image_url (str): 이미지 URL

           Returns:
               str: Base64로 인코딩된 이미지 데이터

           Raises:
               Exception: 이미지 다운로드 또는 인코딩 실패시
           """

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def encode_image_from_url(image_url: str) -> str :
    """
       URL로부터 이미지를 다운로드하여 Base64로 인코딩합니다.

       Args:
           image_url (str): 이미지 URL

       Returns:
           str: Base64로 인코딩된 이미지 데이터

       Raises:
           Exception: 이미지 다운로드 또는 인코딩 실패시
       """

    try:
        import requests
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # 이미지 데이터를 Base64로 인코딩
        image_data = response.content
        base64_image = base64.b64encode(image_data).decode('utf-8')
        return base64_image

    except Exception as e:
        raise Exception(f"Failed to download or encode image from URL: {e}")
