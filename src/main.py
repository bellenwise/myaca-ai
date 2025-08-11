from typing import List
from fastapi import FastAPI, Header
from src.model.assignment_model import AssignmentAnalysisRequest
from src.model.problem_model import ProblemStatsModel, AssignmentReview
from src.model.submission_model import SubmissionAnalysisRequest
from src.model.landing_page_model import LandingPageRequest
from src.model.response_model import BaseResponse
from src.service import chat_service, submission_analysis_service, generate_service, landing_page_service, assignment_analysis_service
from src.model.chat_model import *
from src.model.generate_model import *
from src.service import problem_service

app = FastAPI()


@app.post("/chat")
def talk_chatbot(chat_request: ChatRequest, Authorization: Union[str, None] = Header(default=None)) -> ChatResponse:
    return chat_service.response_chat(chat_request, Authorization)


@app.post("/problem/generate")
def generate_problem(generate_request: GenerateRequest, authorization: str = Header(None)):
    return generate_service.generate_problem(generate_request, authorization)


@app.post("/submit/analyze")
def analyze_submission(a_s_request: SubmissionAnalysisRequest, authorization: str = Header(None)):
    return submission_analysis_service.analyze_submission(a_s_request, authorization)


@app.post("/assignment/analyze")
def analyze_assignment(a_a_request: AssignmentAnalysisRequest, authorization: str = Header(None)) -> BaseResponse :
    return assignment_analysis_service.analyze_assignment(a_a_request, authorization)


@app.get("/assignment/analysis")
def get_assignment_analysis(g_a_request: AssignmentAnalysisRequest, authorization: str = Header(None)) -> BaseResponse:
    return assignment_analysis_service.get_assignment_analysis(g_a_request, authorization)

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


@app.get("/problem/stats", summary="문제에 대한 통계를 조회하는 API")
def get_problem_stats(subdomain: str, problem_id: str) -> ProblemStatsModel:
    return problem_service.get_problem_stats(subdomain, problem_id)


@app.get("/review", summary="학생의 과제 분석 결과를 조회하는 API")
def get_student_assignment_review(student_id: str, assignment_id: str) -> List[AssignmentReview]:
    return problem_service.get_student_assignment_review(student_id, assignment_id)
