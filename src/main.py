from fastapi import FastAPI
from src.service import chat_service
from src.model.chat_model import *

app = FastAPI()


@app.post("/chat")
def talk_chatbot(chatRequest: ChatRequest):
    return chat_service.response_chat(chatRequest)
