from fastapi import FastAPI, Header

from src.model.analysis_model import AnalysisRequest
from src.service import chat_service, analysis_service, generate_service
from src.model.chat_model import *
from src.model.generate_model import *

app = FastAPI()


@app.post("/chat")
def talk_chatbot(chatRequest: ChatRequest, authorization: str = Header(None)):
    return chat_service.response_chat(chatRequest, authorization)


@app.post("/problem/generate")
def generate_problem(generateRequest: GenerateRequest, authorization: str = Header(None)):
    return generate_service.generate_problem(generateRequest, authorization)

@app.post("/analysis")
def submission_analysis(analysisRequest: AnalysisRequest, authorization: str = Header(None)):
    return analysis_service.submission_analysis(analysisRequest, authorization)