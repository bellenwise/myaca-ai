#!/usr/bin/env python3
"""
GET /session API Test - GWT Pattern
Success scenarios for session retrieval with local DDB using Docker
"""
import unittest
from unittest.mock import patch
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mock import MockDDBClient, MockContext, create_test_event, assert_response_success
from app import lambda_handler


class TestGetSessionSuccess(unittest.TestCase):
    """GET /session API Success Test Cases - GWT Pattern"""

    def setUp(self):
        """Test setup"""
        self.mock_context = MockContext()
        self.mock_ddb_client = MockDDBClient()

    @patch.dict(os.environ, {'CHAT': 'test-chat-table'})
    @patch('app.ddbClient')
    def test_get_session(self, mock_ddb_client):
        """
        Given: Existing session_id with multiple chat messages
        When: GET request is sent to /session endpoint
        Then: Returns 200 response with complete chat history
        """
        # Given
        session_id = "test-session-123"
        event = create_test_event(
            http_method="GET",
            path="/session",
            query_params={"session_id": session_id}
        )

        # Mock DDB query result - existing chat data with conversation
        mock_query_result = {
            "Items": [
                {
                    "PK": session_id,
                    "SK": "test-user-456",
                    "message_id": "msg-123",
                    "message_type": "user",
                    "content": "Hello, how are you?",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z"
                },
                {
                    "PK": session_id,
                    "SK": "AGENT",
                    "message_id": "msg-124",
                    "message_type": "assistant",
                    "content": "Hello! I'm doing well, thank you for asking. How can I help you today?",
                    "created_at": "2023-01-01T00:00:01Z",
                    "updated_at": "2023-01-01T00:00:01Z"
                },
                {
                    "PK": session_id,
                    "SK": "test-user-456",
                    "message_id": "msg-125",
                    "message_type": "user",
                    "content": "Can you help me with Python programming?",
                    "created_at": "2023-01-01T00:00:02Z",
                    "updated_at": "2023-01-01T00:00:02Z"
                },
                {
                    "PK": session_id,
                    "SK": "AGENT",
                    "message_id": "msg-126",
                    "message_type": "assistant",
                    "content": "Absolutely! I'd be happy to help you with Python programming. What specific topic would you like to learn about?",
                    "created_at": "2023-01-01T00:00:03Z",
                    "updated_at": "2023-01-01T00:00:03Z"
                }
            ],
            "Count": 4,
            "ScannedCount": 4
        }
        mock_ddb_client.query.return_value = mock_query_result

        # When
        response = lambda_handler(event, self.mock_context)

        # Then
        response_body = assert_response_success(self, response)

        # Verify response data
        self.assertEqual(response_body['data']['Items'], mock_query_result['Items'])
        self.assertEqual(response_body['data']['Count'], 4)
        self.assertEqual(response_body['data']['ScannedCount'], 4)

        # Verify conversation flow
        items = response_body['data']['Items']
        self.assertEqual(items[0]['content'], "Hello, how are you?")
        self.assertEqual(items[1]['content'], "Hello! I'm doing well, thank you for asking. How can I help you today?")
        self.assertEqual(items[2]['content'], "Can you help me with Python programming?")
        self.assertEqual(items[3]['content'], "Absolutely! I'd be happy to help you with Python programming. What specific topic would you like to learn about?")

        # Verify DDB query was called with correct parameters
        mock_ddb_client.query.assert_called_once()
        call_args = mock_ddb_client.query.call_args
        self.assertEqual(call_args[1]['table_name'], 'test-chat-table')

    @patch.dict(os.environ, {'CHAT': 'test-chat-table'})
    @patch('app.ddbClient')
    def test_get_session_with_zero_value(self, mock_ddb_client):
        """
        Given: New session_id with no existing chat data
        When: GET request is sent to /session endpoint
        Then: Returns 200 response with empty chat history
        """
        # Given
        session_id = "new-session-456"
        event = create_test_event(
            http_method="GET",
            path="/session",
            query_params={"session_id": session_id}
        )

        # Mock DDB query result - empty result for new session
        mock_query_result = {
            "Items": [],
            "Count": 0,
            "ScannedCount": 0
        }
        mock_ddb_client.query.return_value = mock_query_result

        # When
        response = lambda_handler(event, self.mock_context)

        # Then
        response_body = assert_response_success(self, response)

        # Verify empty response data
        self.assertEqual(response_body['data']['Items'], [])
        self.assertEqual(response_body['data']['Count'], 0)
        self.assertEqual(response_body['data']['ScannedCount'], 0)

        # Verify DDB query was called with correct parameters
        mock_ddb_client.query.assert_called_once()
        call_args = mock_ddb_client.query.call_args
        self.assertEqual(call_args[1]['table_name'], 'test-chat-table')


if __name__ == '__main__':
    unittest.main(verbosity=2)