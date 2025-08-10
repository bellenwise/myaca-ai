from fastapi import FastAPI, Header
from src.model.analysis_model import AnalysisRequest
from src.service import chat_service, analysis_service, generate_service
from src.model.chat_model import *
from src.model.generate_model import *

app = FastAPI()


@app.post("/chat")
def talk_chatbot(chat_request: ChatRequest, Authorization: Union[str, None] = Header(default=None)) -> ChatResponse:
    return chat_service.response_chat(chat_request, Authorization)


@app.post("/problem/generate")
def generate_problem(generate_request: GenerateRequest, authorization: str = Header(None)):
    return generate_service.generate_problem(generate_request, authorization)


@app.post("/analysis")
def submission_analysis(analysis_request: AnalysisRequest, authorization: str = Header(None)):
    return analysis_service.submission_analysis(analysis_request, authorization)
