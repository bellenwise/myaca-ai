import logging
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MockDDBClient:
    """
    DynamoDB client mocking class
    For testing without actual AWS DynamoDB calls
    """

    def __init__(self, region_name='eu-west-01'):
        self.region_name = region_name
        self.mock_data = {}
        self.transaction_log = []
        logger.info("Mock DynamoDB Client initialized")

    def set_mock_data(self, table_name: str, data: List[Dict[str, Any]]):
        """
        Set mock data for testing
        
        Args:
            table_name (str): Table name
            data (List[Dict[str, Any]]): Mock data list
        """
        self.mock_data[table_name] = data

    def get_table(self, table_name: str):
        """
        Return table object (mocked)
        
        Args:
            table_name (str): Table name
            
        Returns:
            Mock Table object
        """
        return MockTable(table_name, self.mock_data.get(table_name, []))

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
        DynamoDB Query operation mocking
        
        Args:
            table_name (str): Table name
            key_condition_expression (Any): Key condition expression
            filter_expression (Optional[Any]): Filter expression
            index_name (Optional[str]): Index name
            projection_expression (Optional[str]): Projection expression
            expression_attribute_names (Optional[Dict[str, str]]): Expression attribute names
            expression_attribute_values (Optional[Dict[str, Any]]): Expression attribute values
            limit (Optional[int]): Result limit
            scan_index_forward (bool): Scan direction
            exclusive_start_key (Optional[Dict[str, Any]]): Start key
            
        Returns:
            Dict[str, Any]: Query result
        """
        try:
            data = self.mock_data.get(table_name, [])
            
            # Return all data by default (actual implementation needs filtering by key_condition_expression)
            items = data.copy()
            
            # Apply limit
            if limit:
                items = items[:limit]
                
            # Apply scan direction
            if not scan_index_forward:
                items = items[::-1]
            
            result = {
                'Items': items,
                'Count': len(items),
                'ScannedCount': len(items),
                'LastEvaluatedKey': None
            }
            
            logger.info(f"Mock Query successful. Items count: {len(items)}")
            return result
            
        except Exception as e:
            logger.error(f"Mock Query failed: {e}")
            raise e

    def transact_write_items(self, transact_items: List[Dict[str, Any]]) -> (bool, Exception):
        """
        DynamoDB TransactWriteItems operation mocking
        
        Args:
            transact_items (List[Dict[str, Any]]): Transaction items list
            
        Returns:
            tuple: (success, exception)
        """
        try:
            # Log transaction
            self.transaction_log.append({
                'items': transact_items,
                'timestamp': logger.handlers[0].formatter.formatTime(logger.makeRecord('mock', 20, '', 0, '', (), None)) if logger.handlers else 'unknown'
            })
            
            # Actual implementation should process each transaction item
            # Currently considered successful
            logger.info(f"Mock Transaction write successful. Items count: {len(transact_items)}")
            return True, None
            
        except Exception as e:
            logger.error(f"Mock Transaction write failed: {e}")
            return False, e

    def get_transaction_log(self) -> List[Dict[str, Any]]:
        """
        Return transaction log (for testing)
        
        Returns:
            List[Dict[str, Any]]: Transaction log
        """
        return self.transaction_log

    def clear_transaction_log(self):
        """
        Clear transaction log (for testing)
        """
        self.transaction_log = []

    def batch_delete(self, table_name: str, session_id: str) -> (bool, Exception):
        """
        Mock batch delete operation
        
        Args:
            table_name (str): Table name
            session_id (str): Session ID
            
        Returns:
            tuple: (success, exception)
        """
        try:
            logger.info(f"Mock batch delete for session: {session_id}")
            return True, None
        except Exception as e:
            logger.error(f"Mock batch delete failed: {e}")
            return False, e

    def delete_message(self, table_name: str, session_id: str, message_id: str) -> (bool, Exception):
        """
        Mock delete message operation
        
        Args:
            table_name (str): Table name
            session_id (str): Session ID
            message_id (str): Message ID
            
        Returns:
            tuple: (success, exception)
        """
        try:
            logger.info(f"Mock delete message: {message_id} from session: {session_id}")
            return True, None
        except Exception as e:
            logger.error(f"Mock delete message failed: {e}")
            return False, e


class MockTable:
    """
    DynamoDB Table mocking class
    """
    
    def __init__(self, table_name: str, data: List[Dict[str, Any]]):
        self.table_name = table_name
        self.data = data
        
    def query(self, **kwargs) -> Dict[str, Any]:
        """
        Table query mocking
        
        Returns:
            Dict[str, Any]: Query result
        """
        items = self.data.copy()
        
        # Apply limit
        if 'Limit' in kwargs:
            items = items[:kwargs['Limit']]
            
        # Apply scan direction
        if not kwargs.get('ScanIndexForward', True):
            items = items[::-1]
            
        return {
            'Items': items,
            'Count': len(items),
            'ScannedCount': len(items),
            'LastEvaluatedKey': None
        }


# Test helper functions
class MockContext:
    """Mock AWS Lambda context for testing"""
    
    def __init__(self):
        self.function_name = "test-function"
        self.function_version = "1"
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
        self.memory_limit_in_mb = 128
        self.remaining_time_in_millis = 30000
        self.log_group_name = "/aws/lambda/test-function"
        self.log_stream_name = "2023/01/01/[$LATEST]test-stream"
        self.aws_request_id = "test-request-id"


def create_test_event(http_method: str, path: str, body: Optional[Dict[str, Any]] = None, 
                     query_params: Optional[Dict[str, str]] = None, 
                     path_params: Optional[Dict[str, str]] = None,
                     headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Create a test event for AWS Lambda testing
    
    Args:
        http_method (str): HTTP method (GET, POST, etc.)
        path (str): Request path
        body (Optional[Dict[str, Any]]): Request body
        query_params (Optional[Dict[str, str]]): Query parameters
        path_params (Optional[Dict[str, str]]): Path parameters
        headers (Optional[Dict[str, str]]): Request headers
        
    Returns:
        Dict[str, Any]: Test event
    """
    event = {
        "httpMethod": http_method,
        "path": path,
        "headers": headers or {},
        "pathParameters": path_params,
        "queryStringParameters": query_params,
        "body": json.dumps(body) if body else None,
        "isBase64Encoded": False
    }
    return event


def assert_response_success(test_case, response) -> Dict[str, Any]:
    """
    Assert that response is successful and return parsed body
    
    Args:
        test_case: Test case instance
        response: HttpResponse object
        
    Returns:
        Dict[str, Any]: Response data
    """
    test_case.assertEqual(response.status_code, 200)
    test_case.assertIsNotNone(response.body)
    
    return {'data': response.body}


def assert_response_error(test_case, response, expected_status_code=500) -> Dict[str, Any]:
    """
    Assert that response is error and return parsed body
    
    Args:
        test_case: Test case instance
        response: HttpResponse object
        expected_status_code: Expected status code (default 500)
        
    Returns:
        Dict[str, Any]: Response data
    """
    test_case.assertEqual(response.status_code, expected_status_code)
    test_case.assertIsNotNone(response.message)
    
    return {'message': response.message}