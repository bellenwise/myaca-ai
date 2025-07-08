#!/usr/bin/env python3
"""
POST /message API Test - GWT Pattern
Success scenarios for message posting with local DDB using Docker
"""
import unittest
from unittest.mock import patch, Mock
import os
import sys
import uuid

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mock import MockDDBClient, MockContext, create_test_event, assert_response_success, assert_response_error
from app import lambda_handler


class TestPostMessageSuccess(unittest.TestCase):
    """POST /message API Success Test Cases - GWT Pattern"""

    def setUp(self):
        """Test setup"""
        self.mock_context = MockContext()
        self.mock_ddb_client = MockDDBClient()
        
    @patch.dict(os.environ, {'CHAT': 'test-chat-table'})
    @patch('app.ddbClient')
    @patch('app.ChainHandler')
    def test_post_message(self, mock_chain_handler, mock_ddb_client):
        """
        Given: Valid message content and session_id in POST request
        When: Request is sent to /message endpoint
        Then: Returns 200 response with AI response and saves user message + AI response to DDB
        """
        # Given
        session_id = "test-session-123"
        user_id = "test-user-456"
        content = "Hello, this is a test message."
        
        event = create_test_event(
            http_method="POST",
            path="/message",
            body={
                "session_id": session_id,
                "user_id": user_id,
                "content": content
            }
        )
        
        # Mock ChainHandler response
        mock_chain_response = {
            "message_id": "ai-msg-789",
            "retrieve_result": "Retrieved relevant information",
            "generate_result": "Generated AI response"
        }
        mock_chain_handler_instance = Mock()
        mock_chain_handler_instance.handle_request.return_value = mock_chain_response
        mock_chain_handler.return_value = mock_chain_handler_instance
        
        # Mock DDB transaction success
        mock_ddb_client.transact_write_items.return_value = (True, None)
        
        # When
        response = lambda_handler(event, self.mock_context)
        
        # Then
        response_body = assert_response_success(self, response)
        
        # Verify response data
        self.assertEqual(response_body['data']['retrieve_result'], 'Retrieved relevant information')
        self.assertEqual(response_body['data']['generate_result'], 'Generated AI response')
        self.assertEqual(response_body['data']['message_id'], 'ai-msg-789')
        
        # Verify ChainHandler was called
        mock_chain_handler_instance.handle_request.assert_called_once_with(event, self.mock_context)
        
        # Verify DDB transaction was called with correct parameters
        mock_ddb_client.transact_write_items.assert_called_once()
        call_args = mock_ddb_client.transact_write_items.call_args
        transact_items = call_args[1]['transact_items']
        
        # Verify two transaction items (user message + AI response)
        self.assertEqual(len(transact_items), 2)
        
        # Verify first item (user message)
        first_item = transact_items[0]['Put']
        self.assertEqual(first_item['TableName'], 'test-chat-table')
        self.assertIn('Item', first_item)
        
        # Verify second item (AI response)
        second_item = transact_items[1]['Put']
        self.assertEqual(second_item['TableName'], 'test-chat-table')
        self.assertIn('Item', second_item)

if __name__ == '__main__':
    unittest.main(verbosity=2)