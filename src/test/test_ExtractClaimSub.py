import base64
import json
import binascii

from src.utils.ExtractClaimSub import ExtractClaimSub  # Your module's name should be correct
import logging


# Helper function to create a dummy JWT token for testing.
def create_jwt_token(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = "dummy_signature"
    return f"{header_b64}.{payload_b64}.{signature}"


def setup_test_logging(caplog, test_name):
    caplog.set_level(logging.INFO)
    logging.info("\n" + "=" * 50)
    logging.info(f"Test Case: {test_name}")
    logging.info("-" * 50)


def teardown_test_logging():
    logging.info("=" * 50)


def assert_and_log(caplog, actual_sub, expected_sub, success, expected_success, error, expected_error_type):
    logging.info(f"Test Result: {'성공' if success else '실패'}")
    logging.info(f"expectedSub: '{expected_sub}'")
    logging.info(f"actualSub:   '{actual_sub}'")

    if error:
        logging.info(f"Error Type: {type(error).__name__}")
    else:
        logging.info("Error Type: None")

    assert success == expected_success
    assert actual_sub == expected_sub

    if expected_error_type:
        assert isinstance(error, expected_error_type)
    else:
        assert error is None


# --- Individual Test Functions ---
def test_valid_token_success(caplog):
    """테스트 케이스: 'sub' 클레임이 포함된 유효한 토큰"""
    setup_test_logging(caplog, "유효한 토큰")

    # Given
    header = f"Bearer {create_jwt_token({'sub': '12345', 'email': 'test@example.com'})}"
    expected_sub = "12345"
    expected_success = True
    expected_error_type = None

    # When
    actual_sub, success, error = ExtractClaimSub(header)

    # Then
    assert_and_log(caplog, actual_sub, expected_sub, success, expected_success, error, expected_error_type)
    teardown_test_logging()


def test_missing_sub_claim_failure(caplog):
    """테스트 케이스: 'sub' 클레임이 누락된 토큰"""
    setup_test_logging(caplog, "sub 클레임 누락")

    # Given
    header = f"Bearer {create_jwt_token({'email': 'test@example.com'})}"
    expected_sub = ""
    expected_success = False
    expected_error_type = ValueError

    # When
    actual_sub, success, error = ExtractClaimSub(header)

    # Then
    assert_and_log(caplog, actual_sub, expected_sub, success, expected_success, error, expected_error_type)
    teardown_test_logging()


def test_empty_header_failure(caplog):
    """테스트 케이스: 헤더가 비어있는 경우"""
    setup_test_logging(caplog, "빈 헤더")

    # Given
    header = ""
    expected_sub = ""
    expected_success = False
    expected_error_type = ValueError

    # When
    actual_sub, success, error = ExtractClaimSub(header)

    # Then
    assert_and_log(caplog, actual_sub, expected_sub, success, expected_success, error, expected_error_type)
    teardown_test_logging()


def test_invalid_header_format_failure(caplog):
    """테스트 케이스: Bearer 접두사가 없는 헤더"""
    setup_test_logging(caplog, "유효하지 않은 헤더 형식")

    # Given
    header = "InvalidFormatToken"
    expected_sub = ""
    expected_success = False
    expected_error_type = ValueError

    # When
    actual_sub, success, error = ExtractClaimSub(header)

    # Then
    assert_and_log(caplog, actual_sub, expected_sub, success, expected_success, error, expected_error_type)
    teardown_test_logging()


def test_invalid_jwt_format_failure(caplog):
    """테스트 케이스: 토큰 파트가 3개 미만인 경우"""
    setup_test_logging(caplog, "유효하지 않은 JWT 형식")

    # Given
    header = "Bearer invalid.token"
    expected_sub = ""
    expected_success = False
    expected_error_type = ValueError

    # When
    actual_sub, success, error = ExtractClaimSub(header)

    # Then
    assert_and_log(caplog, actual_sub, expected_sub, success, expected_success, error, expected_error_type)
    teardown_test_logging()


def test_invalid_base64_payload_failure(caplog):
    """테스트 케이스: Base64로 인코딩되지 않은 페이로드"""
    setup_test_logging(caplog, "Base64 디코딩 오류")

    # Given
    header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid!.signature"
    expected_sub = ""
    expected_success = False
    expected_error_type = binascii.Error

    # When
    actual_sub, success, error = ExtractClaimSub(header)

    # Then
    assert_and_log(caplog, actual_sub, expected_sub, success, expected_success, error, expected_error_type)
    teardown_test_logging()


def test_non_json_payload_failure(caplog):
    """테스트 케이스: JSON 형식이 아닌 페이로드"""
    setup_test_logging(caplog, "JSON 디코딩 오류")

    # Given
    # 'dGVzdA'는 'test'의 Base64 인코딩 값입니다.
    header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.signature"
    expected_sub = ""
    expected_success = False
    expected_error_type = json.JSONDecodeError

    # When
    actual_sub, success, error = ExtractClaimSub(header)

    # Then
    assert_and_log(caplog, actual_sub, expected_sub, success, expected_success, error, expected_error_type)
    teardown_test_logging()