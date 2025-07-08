import logging
import uuid
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ChainHandler :
    def handle_request(self, event, context):
        try :
            # parsing
            http_method = event.get("httpMethod")
            path_params = event.get("pathParameters")
            http_path = event.get("path")

            # routing
            if http_method == "POST" and http_path.startswith("/message"):
                # orchestration - langchain
                    # retrieve - pinecone searching
                retrieve_result = "retrieve_result"
                    # generate - openai generating
                generate_result = "generate_result"

                get_final_result = retrieve_result or generate_result

                # pass to langsmith
                pass_to_langsmith  = "result"

                # return
                logger.info("post message ok")
                response_body : Dict[str, Any] = {
                    "message_id": uuid.uuid4().hex,
                    "retrieve_result": retrieve_result,
                    "generate_result": generate_result,
                }
                return response_body


        except Exception as e:
            logger.info(f"exception occurred in chain handler: {str(e)}")
            raise e