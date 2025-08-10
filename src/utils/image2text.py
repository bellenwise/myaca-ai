from openai import OpenAI
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionContentPartTextParam, ChatCompletionContentPartImageParam, ChatCompletionUserMessageParam
import src.utils.encode_image as encoder
import os

# load_env
load_dotenv()

# Prompt
extract_text_from_image_prompt = """
아래 이미지에서 모든 텍스트를 추출해 주세요.

추출 시 유의사항:

텍스트의 행(줄): 텍스트가 여러 줄로 되어 있다면, 각 줄의 순서를 정확하게 지켜서 추출해 주세요.

필기 방향: 필기체의 기울기나 사선 방향에 관계없이 텍스트를 올바른 순서로 읽어주세요. 글자가 겹치거나 왜곡되어 있더라도 내용을 정확히 파악해야 합니다.

오류 최소화: 오타나 잘못 읽은 부분이 없도록 최대한 정확하게 텍스트를 변환해 주세요.

수학 수식 정형: 수학 풀이의 경우, 수식을 Latex문법으로 처리한 후, 숫자와 텍스트로 변환해 주세요.
"""

# Initialize Client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def extract_text_from_image(image_path: str) -> str:
    """
    이미지 파일 경로를 입력받아 OpenAI GPT-4o 모델을 사용하여 텍스트를 추출합니다.

    Args:
        image_path (str): 추출할 텍스트가 포함된 이미지 파일의 경로.

    Returns:
        str: 이미지에서 추출된 텍스트.
    """
    if not os.path.exists(image_path):
        return "invalid file path"

    try:
        base64_image = encoder.Encode_image(image_path)

        messages = [
            ChatCompletionUserMessageParam(
                role="user",
                content=[
                    ChatCompletionContentPartTextParam(type="text", text=extract_text_from_image_prompt),
                    ChatCompletionContentPartImageParam(
                        type="image_url",
                        image_url={
                            # Base64 데이터 앞에 올바른 프리픽스 추가
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    )
                ]
            )
        ]

        # API response
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=300,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"error occurred while extracting text: {e}"