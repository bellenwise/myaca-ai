import base64
import json
import logging
import binascii
from typing import Optional, Tuple
import src.ctypes.Cognito as Cognito


def ExtractClaimSub(header: str) -> Tuple[str, bool, Optional[Exception]]:
    """
    Extracts the 'sub' claim from a JWT token in an Authorization header.

    Args:
        header: The Authorization header string.

    Returns:
        A tuple containing:
        - The 'sub' claim string if successful.
        - A boolean indicating success (True) or failure (False).
        - An exception object if an error occurred, otherwise None.
    """
    if not header:
        logging.info("empty header")
        return "", False, ValueError("Missing Authorization header")

    if not header.startswith("Bearer "):
        logging.info("invalid authorization header format")
        return "", False, ValueError("Invalid Authorization header format")

    try:
        token = header.split(" ")[1]
        parts = token.split(".")
        if len(parts) != 3:
            logging.info("invalid token format")
            return "", False, ValueError("Invalid token format")

        # JWT의 payload는 base64url로 인코딩됩니다.
        payload_base64 = parts[1]
        # Base64 디코딩을 위해 패딩 추가 (필요한 경우)
        payload_base64 += '=' * (-len(payload_base64) % 4)
        payload = base64.urlsafe_b64decode(payload_base64).decode('utf-8')

        claims_data = json.loads(payload)
        claims = Cognito.CognitoClaims(**claims_data)

        if claims.sub:
            return claims.sub, True, None
        else:
            logging.info("sub claim not found")
            return "", False, ValueError("'sub' claim not found in token")

    except IndexError:
        return "", False, ValueError("Token format is invalid")
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:
        logging.error(f"Failed to process token: {e}")
        return "", False, e
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return "", False, e