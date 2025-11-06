"""
API endpoints for the SmarTest application.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from services.question_service import QuestionService
from services.evaluation_service import EvaluationService
from services.test_service import TestService
from api.schemas import (
    GenerateQuestionsRequest,
    EvaluateAnswerRequest,
    CreateTestRequest,
    QuestionResponse,
    QuestionListResponse,
    AnswerResponse,
    EvaluationResponse,
    TestResponse,
    TestWithQuestionsResponse,
    TestListResponse,
    TestSummaryResponse,
    ErrorResponse,
    SuccessResponse
)
from typing import Optional

router = APIRouter(prefix="/api", tags=["SmarTest API"])


# Question Endpoints

@router.post(
    "/generate-questions",
    response_model=QuestionListResponse,
    summary="Generate Questions",
    description="Generate one or more questions of a specified type and difficulty"
)
def generate_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db)
):
    """
    Generate questions algorithmically.

    - **type**: Question type (nash, minimax, csp, search)
    - **count**: Number of questions to generate
    - **difficulty**: Difficulty level (easy, medium, hard)
    - **parameters**: Optional custom parameters for generation
    """
    try:
        # Extract parameters
        params = request.parameters or {}

        # Generate questions
        questions = QuestionService.generate_questions(
            db,
            question_type=request.type,
            count=request.count,
            difficulty=request.difficulty,
            **params
        )

        # Convert to response format (parse JSON strings to dicts)
        questions_response = []
        for q in questions:
            questions_response.append({
                "id": q.id,
                "type": q.type,
                "difficulty": q.difficulty,
                "question_text": q.question_text,
                "question_data": q.get_question_data(),  # Parse JSON string to dict
                "created_at": q.created_at
            })

        return {
            "questions": questions_response,
            "total": len(questions_response)
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.get(
    "/questions",
    response_model=QuestionListResponse,
    summary="List Questions",
    description="Get all questions with optional filters"
)
def get_questions(
    type: Optional[str] = Query(None, description="Filter by question type"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of questions"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all questions with optional filtering.
    """
    questions = QuestionService.get_all_questions(
        db,
        question_type=type,
        difficulty=difficulty,
        limit=limit
    )

    # Convert to response format
    questions_response = []
    for q in questions:
        questions_response.append({
            "id": q.id,
            "type": q.type,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "question_data": q.get_question_data(),
            "created_at": q.created_at
        })

    return {
        "questions": questions_response,
        "total": len(questions_response)
    }


@router.get(
    "/questions/{question_id}",
    response_model=QuestionResponse,
    summary="Get Question",
    description="Get a specific question by ID"
)
def get_question(
    question_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific question by its ID.
    """
    question = QuestionService.get_question(db, question_id)

    if not question:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    return {
        "id": question.id,
        "type": question.type,
        "difficulty": question.difficulty,
        "question_text": question.question_text,
        "question_data": question.get_question_data(),
        "created_at": question.created_at
    }


@router.get(
    "/questions/{question_id}/answer",
    response_model=AnswerResponse,
    summary="Get Correct Answer",
    description="Get the correct answer and explanation for a question"
)
def get_answer(
    question_id: str,
    detail_level: str = Query("detailed", regex="^(concise|detailed)$"),
    db: Session = Depends(get_db)
):
    """
    Get the correct answer with explanation.

    - **detail_level**: "concise" or "detailed"
    """
    answer_data = QuestionService.get_correct_answer(db, question_id, detail_level)

    if not answer_data:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    return answer_data


@router.delete(
    "/questions/{question_id}",
    response_model=SuccessResponse,
    summary="Delete Question",
    description="Delete a question from the database"
)
def delete_question(
    question_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a question by ID.
    """
    success = QuestionService.delete_question(db, question_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    return {
        "success": True,
        "message": f"Question {question_id} deleted successfully"
    }


# Evaluation Endpoints

@router.post(
    "/evaluate-answer",
    response_model=EvaluationResponse,
    summary="Evaluate Answer",
    description="Evaluate a student's answer and provide score with feedback"
)
def evaluate_answer(
    request: EvaluateAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate a student's answer against the correct answer.

    Returns score (0-100), detailed feedback, correct answer, and explanation.
    """
    try:
        evaluation = EvaluationService.evaluate_answer(
            db,
            question_id=request.question_id,
            student_answer=request.student_answer
        )

        if not evaluation:
            raise HTTPException(
                status_code=404,
                detail=f"Question {request.question_id} not found"
            )

        # Build response with additional data
        response = {
            "id": evaluation.id,
            "question_id": evaluation.question_id,
            "student_answer": evaluation.student_answer,
            "score": evaluation.score,
            "feedback": evaluation.get_feedback(),
            "evaluated_at": evaluation.evaluated_at
        }

        # Add correct answer and explanation if available
        if hasattr(evaluation, '_correct_answer'):
            response["correct_answer"] = evaluation._correct_answer
        if hasattr(evaluation, '_explanation'):
            response["explanation"] = evaluation._explanation

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating answer: {str(e)}")


@router.get(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationResponse,
    summary="Get Evaluation",
    description="Get a specific evaluation by ID"
)
def get_evaluation(
    evaluation_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific evaluation by ID.
    """
    evaluation = EvaluationService.get_evaluation(db, evaluation_id)

    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")

    return {
        "id": evaluation.id,
        "question_id": evaluation.question_id,
        "student_answer": evaluation.student_answer,
        "score": evaluation.score,
        "feedback": evaluation.get_feedback(),
        "evaluated_at": evaluation.evaluated_at
    }


# Test Endpoints

@router.post(
    "/create-test",
    response_model=TestResponse,
    summary="Create Test",
    description="Create a test by combining multiple questions"
)
def create_test(
    request: CreateTestRequest,
    db: Session = Depends(get_db)
):
    """
    Create a test from a list of question IDs.
    """
    try:
        test = TestService.create_test(
            db,
            title=request.title,
            question_ids=request.question_ids
        )

        if not test:
            raise HTTPException(
                status_code=404,
                detail="One or more questions not found"
            )

        return test

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test: {str(e)}")


@router.get(
    "/tests",
    response_model=TestListResponse,
    summary="List Tests",
    description="Get all tests"
)
def get_tests(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Retrieve all tests.
    """
    tests = TestService.get_all_tests(db, limit=limit)

    return {
        "tests": tests,
        "total": len(tests)
    }


@router.get(
    "/tests/{test_id}",
    response_model=TestWithQuestionsResponse,
    summary="Get Test",
    description="Get a specific test with all its questions"
)
def get_test(
    test_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific test with all its questions.
    """
    test = TestService.get_test(db, test_id)

    if not test:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")

    questions = TestService.get_test_questions(db, test_id)

    # Convert questions to response format
    questions_response = []
    for q in questions:
        questions_response.append({
            "id": q.id,
            "type": q.type,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "question_data": q.get_question_data(),
            "created_at": q.created_at
        })

    return {
        "id": test.id,
        "title": test.title,
        "created_at": test.created_at,
        "questions": questions_response,
        "total_questions": len(questions_response)
    }


@router.get(
    "/tests/{test_id}/summary",
    response_model=TestSummaryResponse,
    summary="Get Test Summary",
    description="Get summary statistics for a test"
)
def get_test_summary(
    test_id: str,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for a test.
    """
    summary = TestService.get_test_summary(db, test_id)

    if not summary:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")

    return summary


@router.delete(
    "/tests/{test_id}",
    response_model=SuccessResponse,
    summary="Delete Test",
    description="Delete a test from the database"
)
def delete_test(
    test_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a test by ID.
    """
    success = TestService.delete_test(db, test_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")

    return {
        "success": True,
        "message": f"Test {test_id} deleted successfully"
    }