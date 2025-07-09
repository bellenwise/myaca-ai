# import
import os
import logging
import uuid
import json
from shared.response import *
from shared.ddb import DDBClient
from boto3.dynamodb.conditions import Key
from shared.models import *
from chain import ChainHandler
from typing import Dict, Any, List

# lambda settings
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ddbClient = DDBClient()


# entry
def lambda_handler(event, context):
    """
    Lambda handler function
    동적 라우팅
    :param event: json
    :param context: context
    :return: http response
    """
    logger.info("Request: %s", event)

    try:
        http_method = event.get("httpMethod")
        http_path = event.get("path")
        header = event.get("headers")
        path_params = event.get("pathParameters")
        query_params = event.get("queryStringParameters")
        body = event.get("body")

        if http_method == "GET":
            # Get
            if http_path.startswith("/session"):
                # DDB
                query_out: Dict[str, any] = ddbClient.query(
                    table_name=os.environ.get("CHAT"),
                    key_condition_expression=Key("PK").eq(query_params.get("session_id")),
                )
                response_body = {
                    "Items": query_out["Items"],
                    "Count": query_out["Count"],
                    "ScannedCount": query_out["ScannedCount"],
                }

                return success_response("OK", response_body)

        elif http_method == "DELETE":
            # Delete
            if http_path.startswith("/session"):
                # Get session_id from path parameters
                session_id = path_params.get("session_id") if path_params else None
                if not session_id:
                    return not_found_response("session_id is required")
                
                # DDB batch delete with transactional processing
                success, error = ddbClient.batch_delete(
                    table_name=os.environ.get("CHAT"),
                    session_id=session_id
                )
                
                if not success:
                    return server_error_response(f"Failed to delete session: {error}")
                
                return success_response(f"DELETED session: {session_id}")

            elif http_path.startswith("/message"):
                # Parse body for message deletion
                body_json = json.loads(body) if body else {}
                session_id = body_json.get("session_id")
                message_id = body_json.get("message_id")
                table_name = body_json.get("table_name")
                
                if not session_id or not message_id:
                    return not_found_response("session_id and message_id are required")
                
                # Delete specific message
                success, error = ddbClient.delete_message(
                    table_name=table_name,
                    session_id=session_id,
                    message_id=message_id
                )
                
                if not success:
                    return server_error_response(f"Failed to delete message: {error}")
                
                return success_response(f"DELETED message: {message_id}")

        else:
            # POST or PUT
            handler = ChainHandler()
            response = handler.handle_request(event, context)

            # ddb process
            body_json = json.loads(body) if body else {}
            session_id = body_json.get("session_id", "")
            user_id = body_json.get("user_id", "AGENT")
            content = body_json.get("content", "")
            message_id = uuid.uuid4().hex

            ddb_response, error = ddbClient.transact_write_items(
                transact_items=[
                    {
                        "Put": {
                            "TableName": os.environ.get("CHAT"),
                            "Item": Chat.create(
                                session_id,
                                user_id,
                                message_id,
                                "chat",
                                content,
                            ),
                        },
                    },
                    {
                        "Put": {
                            "TableName": os.environ.get("CHAT"),
                            "Item": Chat.create(
                                session_id,
                                "AGENT",
                                response.get("message_id"),
                                "chat",
                                content,
                            ),
                        }
                    }
                ]
            )
            if ddb_response is False:
                return server_error_response(f"ddb transaction failed: {error}")

            # return http response
            # return output of question
            return success_response("OK", response)

    except Exception as e:
        logger.info("exception in routing: %s", e)
        return server_error_response(f"internal server error: {str(e)}")