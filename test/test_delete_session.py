#!/usr/bin/env python3
"""
DELETE /session/{session_id} API Test - GWT Pattern
Success and error scenarios for session deletion with local DDB using Docker
"""
import unittest
from unittest.mock import patch, Mock
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mock import MockDDBClient, MockContext, create_test_event, assert_response_success, assert_response_error
from app import lambda_handler


class TestDeleteSession(unittest.TestCase):
    """DELETE /session/{session_id} API Test Cases - GWT Pattern"""

    def setUp(self):
        """Test setup"""
        self.mock_context = MockContext()
        self.mock_ddb_client = MockDDBClient()

    @patch.dict(os.environ, {'CHAT': 'test-chat-table'})
    @patch('app.ddbClient')
    def test_delete_session(self, mock_ddb_client):
        """
        Given: Existing session_id with chat messages
        When: DELETE request is sent to /session/{session_id} endpoint
        Then: Returns 200 response and deletes all session messages
        """
        # Given
        session_id = "test-session-123"
        event = create_test_event(
            http_method="DELETE",
            path="/session/{session_id}",
            path_params={"session_id": session_id}
        )

        # Mock DDB batch_delete success
        mock_ddb_client.batch_delete.return_value = (True, None)

        # When
        response = lambda_handler(event, self.mock_context)

        # Then
        assert_response_success(self, response)
        self.assertEqual(response.message, f"DELETED session: {session_id}")

        # Verify DDB batch_delete was called with correct parameters
        mock_ddb_client.batch_delete.assert_called_once_with(
            table_name='test-chat-table',
            session_id=session_id
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)