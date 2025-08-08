import re
from src.model.categories import forbidden_keywords, suspicious_patterns

def guard_injection(input_text: str) -> bool :
    """
    LLM 프롬프트 인젝션 공격을 방어하기 위해 입력 텍스트를 검사합니다.

    Args:
        input_text (str): 사용자의 입력 문자열.

    Returns:
        bool:
            - 첫 번째 값 (bool): 텍스트가 안전하다고 판단되면 True, 잠재적 위협이 있으면 False.
    """

    normalized_text = input_text.lower()

    # 1. 금지된 키워드 검사
    for keyword in forbidden_keywords:
        if keyword in normalized_text:
            return False

    # 2. 의심스러운 패턴 검사
    for pattern in suspicious_patterns:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            return False

    # 모든 검사를 통과하면 안전하다고 판단
    return True