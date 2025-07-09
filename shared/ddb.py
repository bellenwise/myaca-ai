import boto3
import logging
from typing import Dict, List, Optional, Any, Union
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DDBClient:
    """
    DynamoDB 클라이언트 - AWS 공식 문서 기반 구현
    Query, TransactionWriteItems

    """

    def __init__(self, region_name='eu-west-01'):
        # DynamoDB 리소스 및 클라이언트 초기화
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.dynamodb_client = boto3.client('dynamodb', region_name=region_name)

        logger.info("DynamoDB Client initialized")

    def get_table(self, table_name: str):
        """
        테이블 객체 반환

        Args:
            table_name (str): 테이블 이름

        Returns:
            DynamoDB Table 객체
        """
        return self.dynamodb.Table(table_name)

    def query(self,
              table_name: str,
              key_condition_expression: Any,
              filter_expression: Optional[Any] = None,
              index_name: Optional[str] = None,
              projection_expression: Optional[str] = None,
              expression_attribute_names: Optional[Dict[str, str]] = None,
              expression_attribute_values: Optional[Dict[str, Any]] = None,
              limit: Optional[int] = None,
              scan_index_forward: bool = True,
              exclusive_start_key: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        DynamoDB Query 작업

        Args:
            table_name (str): 테이블 이름
            key_condition_expression (Any): 키 조건 표현식
            filter_expression (Optional[Any]): 필터 표현식
            index_name (Optional[str]): 인덱스 이름 (GSI용)
            projection_expression (Optional[str]): 프로젝션 표현식
            expression_attribute_names (Optional[Dict[str, str]]): 표현식 속성 이름
            expression_attribute_values (Optional[Dict[str, Any]]): 표현식 속성 값
            limit (Optional[int]): 결과 제한
            scan_index_forward (bool): 스캔 방향
            exclusive_start_key (Optional[Dict[str, Any]]): 시작 키 (페이지네이션용)

        Returns:
            Dict[str, Any]: 쿼리 결과
        """
        try:
            table = self.get_table(table_name)

            params = {
                'KeyConditionExpression': key_condition_expression,
                'ScanIndexForward': scan_index_forward
            }

            if index_name:
                params['IndexName'] = index_name

            if filter_expression:
                params['FilterExpression'] = filter_expression

            if projection_expression:
                params['ProjectionExpression'] = projection_expression

            if expression_attribute_names:
                params['ExpressionAttributeNames'] = expression_attribute_names

            if expression_attribute_values:
                params['ExpressionAttributeValues'] = expression_attribute_values

            if limit:
                params['Limit'] = limit

            if exclusive_start_key:
                params['ExclusiveStartKey'] = exclusive_start_key

            response = table.query(**params)

            logger.info(f"Query successful. Items count: {response['Count']}")
            return {
                'Items': response['Items'],
                'Count': response['Count'],
                'ScannedCount': response['ScannedCount'],
                'LastEvaluatedKey': response.get('LastEvaluatedKey')
            }

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise e

    def transact_write_items(self, transact_items: List[Dict[str, Any]]) -> (bool, Exception):
        """
        DynamoDB TransactWriteItems 작업

        Args:
            transact_items (List[Dict[str, Any]]): 트랜잭션 아이템 리스트

        Returns:
            bool: 트랜잭션 성공 여부
        """
        try:
            self.dynamodb_client.transact_write_items(
                TransactItems=transact_items
            )
            logger.info(f"Transaction write successful. Items count: {len(transact_items)}")
            return True, None

        except Exception as e:
            logger.error(f"Transaction write failed: {e}")
            return False, e

    def batch_delete(self, table_name: str, session_id: str) -> (bool, Exception):
        """
        세션의 모든 채팅 기록을 배치로 삭제
        25개 이상일 경우 transactional batches로 처리f

        Args:
            table_name (str): 테이블 이름
            session_id (str): 세션 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 세션의 모든 아이템 조회
            items = self.query(
                table_name=table_name,
                key_condition_expression=Key("PK").eq(session_id)
            )
            
            chat_items = items.get("Items", [])
            
            if not chat_items:
                logger.info(f"No items found for session: {session_id}")
                return True, None
            
            # 25개씩 배치로 나누어 처리
            batch_size = 25
            batches = [chat_items[i:i + batch_size] for i in range(0, len(chat_items), batch_size)]
            
            for batch in batches:
                transact_items = []
                for item in batch:
                    transact_items.append({
                        "Delete": {
                            "TableName": table_name,
                            "Key": {
                                "PK": {"S": item["PK"]},
                                "SK": {"S": item["SK"]}
                            }
                        }
                    })
                
                # 트랜잭션으로 배치 삭제
                success, error = self.transact_write_items(transact_items)
                if not success:
                    logger.error(f"Batch delete failed for session {session_id}: {error}")
                    return False, error
                
                logger.info(f"Batch deleted {len(batch)} items for session {session_id}")
            
            logger.info(f"Successfully deleted all {len(chat_items)} items for session {session_id}")
            return True, None

        except Exception as e:
            logger.error(f"Batch delete by session failed: {e}")
            return False, e

    def delete_message(self, table_name: str, session_id: str, message_id: str) -> (bool, Exception):
        """
        특정 메시지를 삭제

        Args:
            table_name (str): 테이블 이름
            session_id (str): 세션 ID
            message_id (str): 메시지 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            transact_items = [{
                "Delete": {
                    "TableName": table_name,
                    "Key": {
                        "PK": {"S": session_id},
                        "SK": {"S": message_id}
                    }
                }
            }]
            
            success, error = self.transact_write_items(transact_items)
            if not success:
                logger.error(f"Delete message failed for session {session_id}, message {message_id}: {error}")
                return False, error
            
            logger.info(f"Successfully deleted message {message_id} from session {session_id}")
            return True, None

        except Exception as e:
            logger.error(f"Delete message failed: {e}")
            return False, e