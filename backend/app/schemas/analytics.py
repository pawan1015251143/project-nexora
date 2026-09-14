from pydantic import BaseModel
from typing import List, Dict, Any

class MetricsResponse(BaseModel):
    total_students: int
    total_faculty: int
    total_documents: int
    approved_documents: int
    questions_today: int
    total_questions: int
    unanswered_questions: int
    positive_feedback: int
    negative_feedback: int

class ChartDataResponse(BaseModel):
    questions_over_time: List[Dict[str, Any]]
    popular_categories: List[Dict[str, Any]]
    popular_documents: List[Dict[str, Any]]
    department_usage: List[Dict[str, Any]]
    feedback_trends: List[Dict[str, Any]]
