from typing import TypeVar
from src.model.image_model import ImageProcessRequest, ImageGenerationRequest
from src.service import image_process_service
from fastapi import FastAPI, Header, Response
from typing import List
from src.model.assignment_model import AssignmentAnalysisRequest
from src.model.problem_model import ProblemStatsModel, AssignmentReview
from src.model.submission_model import SubmissionAnalysisRequest
from src.model.landing_page_model import LandingPageRequest
from src.model.response_model import BaseResponse
from src.service import chat_service, generate_service, landing_page_service, assignment_analysis_service, image_service
from src.model.chat_model import *
from src.model.generate_model import *
from src.service import problem_service

T = TypeVar('T')

app = FastAPI()


@app.post("/chat", summary="학생 LLM 채팅")
def talk_chatbot(chat_request: ChatRequest, Authorization: Union[str, None] = Header(default=None)) -> ChatResponse:
    return chat_service.response_chat(chat_request, Authorization)


@app.post("/problem/generate", summary="관리자 비슷한 문제 생성")
def generate_problem(generate_request: GenerateRequest, authorization: str = Header(None)) -> BaseResponse:
    return generate_service.generate_problem(generate_request, authorization)


@app.post("/submission/analyze",summary="학생 제출 이미지 텍스트 분석 및 저장")
def image_analysis(analysis_request: ImageProcessRequest) -> BaseResponse:
    return image_process_service.image_process(analysis_request)


# @app.post("/assignment/analyze", summary="과제 마감 후 제출물 분석")
# def analyze_assignment(a_a_request: AssignmentAnalysisRequest, authorization: str = Header(None)) -> BaseResponse:
#     return assignment_analysis_service.analyze_assignment(a_a_request, authorization)


@app.get("/assignment/analysis", summary="과제 분석 내용 조회")
def get_assignment_analysis(acaId: str, assignmentId: str, authorization: str = Header(None)) -> BaseResponse:
    return assignment_analysis_service.get_assignment_analysis(acaId, assignmentId, authorization)
  

@app.post("/landing/{subdomain}", summary="랜딩 페이지 Create")
def create_landing_page(subdomain: str, landing_page_request: List[LandingPageRequest]):
    return landing_page_service.create_landing_page(subdomain, landing_page_request)


@app.get("/landing/{subdomain}", summary="랜딩 페이지 Read")
def get_landing_page(subdomain: str) -> List[LandingPageRequest]:
    return landing_page_service.get_landing_page(subdomain)


@app.put("/landing/{subdomain}",  summary="랜딩 페이지 Update")
def update_landing_page(subdomain: str, landing_page_request: List[LandingPageRequest]):
    return landing_page_service.update_landing_page(subdomain, landing_page_request)


@app.get("/problem/stats", summary="문제에 대한 통계를 조회하는 API")
def get_problem_stats(subdomain: str, problem_id: str) -> ProblemStatsModel:
    return problem_service.get_problem_stats(subdomain, problem_id)


@app.get("/review", summary="학생의 과제 분석 결과를 조회하는 API")
def get_student_assignment_review(student_id: str, assignment_id: str) -> List[AssignmentReview]:
    return problem_service.get_student_assignment_review(student_id, assignment_id)


@app.post("/image_generation", summary="이미지 생성 요청 API")
def image_generation(image_request: ImageGenerationRequest) -> Response:
    return image_service.generate_image(image_request)
