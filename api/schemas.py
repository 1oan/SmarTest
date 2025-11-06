"""
Pydantic schemas for API request and response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Request Schemas

class GenerateQuestionsRequest(BaseModel):
    """Request schema for generating questions."""
    type: str = Field(..., description="Question type: 'nash', 'minimax', 'csp', or 'search'")
    count: int = Field(1, ge=1, le=50, description="Number of questions to generate (1-50)")
    difficulty: str = Field("medium", description="Difficulty level: 'easy', 'medium', or 'hard'")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional custom parameters (e.g., rows, cols, min_payoff, max_payoff)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "nash",
                "count": 5,
                "difficulty": "medium",
                "parameters": {
                    "rows": 3,
                    "cols": 3,
                    "min_payoff": 0,
                    "max_payoff": 10
                }
            }
        }


class EvaluateAnswerRequest(BaseModel):
    """Request schema for evaluating a student answer."""
    question_id: str = Field(..., description="ID of the question being answered")
    student_answer: str = Field(..., description="Student's answer as text")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "nash_a1b2c3d4",
                "student_answer": "Yes, there is a Nash equilibrium at (U, L)"
            }
        }


class CreateTestRequest(BaseModel):
    """Request schema for creating a test."""
    title: str = Field(..., description="Test title")
    question_ids: List[str] = Field(..., min_length=1, description="List of question IDs to include")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Midterm Exam - Game Theory",
                "question_ids": ["nash_a1b2c3d4", "nash_e5f6g7h8"]
            }
        }


# Response Schemas

class QuestionResponse(BaseModel):
    """Response schema for a question."""
    id: str
    type: str
    difficulty: str
    question_text: str
    question_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    """Response schema for listing questions."""
    questions: List[QuestionResponse]
    total: int


class AnswerResponse(BaseModel):
    """Response schema for getting correct answer."""
    question_id: str
    answer: Dict[str, Any]
    explanation: str
    question_type: str


class EvaluationResponse(BaseModel):
    """Response schema for answer evaluation."""
    id: str
    question_id: str
    student_answer: str
    score: float
    feedback: List[str]
    correct_answer: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    evaluated_at: datetime

    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    """Response schema for listing evaluations."""
    evaluations: List[EvaluationResponse]
    total: int


class TestResponse(BaseModel):
    """Response schema for a test."""
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class TestWithQuestionsResponse(BaseModel):
    """Response schema for a test with its questions."""
    id: str
    title: str
    created_at: datetime
    questions: List[QuestionResponse]
    total_questions: int


class TestListResponse(BaseModel):
    """Response schema for listing tests."""
    tests: List[TestResponse]
    total: int


class TestSummaryResponse(BaseModel):
    """Response schema for test summary."""
    test_id: str
    title: str
    created_at: Optional[str]
    total_questions: int
    questions_by_type: Dict[str, int]
    questions_by_difficulty: Dict[str, int]


class ErrorResponse(BaseModel):
    """Response schema for errors."""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str