import os
import pytest
from src.utils.image2text import extract_text_from_image
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


@pytest.fixture(scope="session")
def setup_test_image():
    """
    테스트에 사용할 이미지 파일을 설정하고, 테스트 종료 후 파일을 정리합니다.
    실제 테스트를 위해서는 'test_image_with_text.jpg'라는 파일을 준비해야 합니다.
    """
    image_path = "src/test/test_math_submit.jpg"
    # 실제 테스트를 위해선 이 경로에 텍스트가 포함된 이미지 파일이 있어야 합니다.
    if not os.path.exists(image_path):
        pytest.skip(f"테스트 이미지 파일이 존재하지 않습니다: {image_path}")

    yield image_path

    # teardown: 이 예제에서는 파일을 삭제하지 않습니다.
    # 필요시 파일을 삭제하는 코드를 추가할 수 있습니다.
    # if os.path.exists(image_path):
    #     os.remove(image_path)


def test_extract_text_successfully(setup_test_image):
    """
    [Given] 텍스트가 포함된 유효한 이미지 경로가 주어졌을 때
    [When] extract_text_from_image 함수를 호출하면
    [Then] 올바른 텍스트를 반환하고 터미널에 출력해야 한다.
    """
    # Given: pytest fixture를 통해 유효한 이미지 경로를 받습니다.
    valid_image_path = setup_test_image

    # When: 테스트 대상 함수를 호출합니다.
    extracted_text = extract_text_from_image(valid_image_path)

    # Then: 추출된 텍스트가 비어있지 않음을 검증하고 터미널에 출력합니다.
    assert extracted_text is not None
    assert isinstance(extracted_text, str)
    assert len(extracted_text) > 0

    print("\n--- 실제 API 호출을 통해 추출된 텍스트 ---")
    print(extracted_text)
    print("---------------------------------------")


def test_extract_text_with_invalid_path():
    """
    [Given] 존재하지 않는 이미지 경로가 주어졌을 때
    [When] extract_text_from_image 함수를 호출하면
    [Then] "invalid file path" 메시지를 반환해야 한다.
    """
    # Given: 존재하지 않는 파일 경로를 정의합니다.
    invalid_path = "non_existent_file.jpg"

    # When: 함수를 호출합니다.
    extracted_text = extract_text_from_image(invalid_path)

    # Then: 예상한 에러 메시지를 반환하는지 확인합니다.
    assert extracted_text == "invalid file path"