from fastapi import FastAPI, Header
from src.model.analysis_model import AnalysisRequest
from src.model.landing_page_model import LandingPageRequest
from src.service import chat_service, analysis_service, generate_service, landing_page_service
from src.model.chat_model import *
from src.model.generate_model import *
from typing import List

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


# 랜딩 페이지 CRUD
@app.post("/landing/{subdomain}")
def create_landing_page(subdomain: str, landing_page_request: List[LandingPageRequest]):
    return landing_page_service.create_landing_page(subdomain, landing_page_request)


@app.get("/landing/{subdomain}")
def get_landing_page(subdomain: str) -> List[LandingPageRequest]:
    return landing_page_service.get_landing_page(subdomain)


@app.put("/landing/{subdomain}")
def update_landing_page(subdomain: str, landing_page_request: List[LandingPageRequest]):
    return landing_page_service.update_landing_page(subdomain, landing_page_request)
