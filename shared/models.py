from datetime import datetime

from typing import Dict

from dataclasses import dataclass


@dataclass
class Chat:
    """
    DynamoDB chat_logs

    Attributes:
        PK (str): session_id
        SK (str): user_id
            user_id (str): student_id or "AGENT"
        message_id (str): 고유한 메시지 ID
        message_type (str): 메시지 타입 (user, assistant, system)
        createdAt (str): 생성 시간 (ISO 8601 형식)
        updatedAt (str): 수정 시간 (ISO 8601 형식)
        content (str): 메시지 내용
        payload (Dict[str, Any]): 추가 정보를 담는 딕셔너리
    """
    PK: str
    SK: str
    message_id: str
    message_type: str
    content: str
    created_at: str
    updated_at: str
    # payload: Optional[Dict[str, Any]] = None

    @classmethod
    def create(
        cls,
        session_id: str,
        user_id: str,
        message_id: str,
        message_type: str,
        content: str,
        # payload: Optional[Dict[str, Any]] = None
    ) -> 'Chat':
        """
        새로운 ChatLog 인스턴스를 생성하는 클래스 메서드

        Args:
            session_id (str): 세션 ID
            user_id (str): 사용자 ID
            message_type (MessageType): 메시지 타입
            content (str): 메시지 내용
            payload (Dict[str, Any], optional): 추가 정보

        Returns:
            ChatLog: 새로운 ChatLog 인스턴스
        """
        now = datetime.now()
        return cls(
            PK=session_id,
            SK=user_id,
            message_id=message_id,
            message_type=message_type,
            content=content,
            created_at=now.isoformat() + 'Z',
            updated_at=now.isoformat() + 'Z',
            # payload=payload or {}
        )

    def update(self, new_content: str):
        self.content = new_content
        self.updated_at = datetime.now().isoformat() + 'Z'

    # def to_ddb_item(self) -> Dict[str, Any]:
    #     return asdict(self)
    #
    # def from_ddb_item(cls, item: Dict[str, Any]) -> 'Chat':
    #     return cls(**item)