#!/usr/bin/env python3
"""
DELETE /message/{message_id} API Test - GWT Pattern
Success and error scenarios for message deletion with local DDB using Docker
"""
import unittest
from unittest.mock import patch, Mock
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mock import MockDDBClient, MockContext, create_test_event, assert_response_success, assert_response_error
from app import lambda_handler


class TestDeleteMessage(unittest.TestCase):
    """DELETE /message/{message_id} API Test Cases - GWT Pattern"""

    def setUp(self):
        """Test setup"""
        self.mock_context = MockContext()
        self.mock_ddb_client = MockDDBClient()

    @patch.dict(os.environ, {'CHAT': 'test-chat-table'})
    @patch('app.ddbClient')
    def test_delete_message(self, mock_ddb_client):
        """
        Given: Valid session_id and message_id in request body
        When: DELETE request is sent to /message/{message_id} endpoint
        Then: Returns 200 response and deletes specific message
        """
        # Given
        session_id = "test-session-123"
        message_id = "test-message-456"
        table_name = "test-chat-table"
        
        event = create_test_event(
            http_method="DELETE",
            path="/message/{message_id}",
            path_params={"message_id": message_id},
            body={
                "session_id": session_id,
                "message_id": message_id,
                "table_name": table_name
            }
        )

        # Mock DDB delete_message success
        mock_ddb_client.delete_message.return_value = (True, None)

        # When
        response = lambda_handler(event, self.mock_context)

        # Then
        assert_response_success(self, response)
        self.assertEqual(response.message, f"DELETED message: {message_id}")

        # Verify DDB delete_message was called with correct parameters
        mock_ddb_client.delete_message.assert_called_once_with(
            table_name=table_name,
            session_id=session_id,
            message_id=message_id
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)