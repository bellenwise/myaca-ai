import boto3
import logging
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DDBClient:
    """
    DynamoDB 클라이언트 - AWS 공식 문서 기반 구현
    Query, TransactionWriteItems

    """

    def __init__(self, region_name='eu-west-01'):
        # DynamoDB 리소스 및 클라이언트 초기화
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