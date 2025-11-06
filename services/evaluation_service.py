"""
Service layer for answer evaluation.
"""
from sqlalchemy.orm import Session
from database.models import Evaluation, Question
from services.question_service import QuestionService
from typing import Optional, Dict, Any
import uuid


class EvaluationService:
    """Service for evaluating student answers."""

    @staticmethod
    def evaluate_answer(
        db: Session,
        question_id: str,
        student_answer: str
    ) -> Optional[Evaluation]:
        """
        Evaluate a student's answer and save the evaluation.

        Args:
            db: Database session
            question_id: ID of the question being answered
            student_answer: Student's answer as text

        Returns:
            Evaluation object with score and feedback, or None if question not found

        Raises:
            ValueError: If question type is not supported
        """
        # Get the question
        question = QuestionService.get_question(db, question_id)

        if not question:
            return None

        # Get the question type generator
        if question.type not in QuestionService.QUESTION_TYPES:
            raise ValueError(f"Unsupported question type: {question.type}")

        generator = QuestionService.QUESTION_TYPES[question.type]

        # Get question data and correct answer
        question_data = question.get_question_data()
        correct_answer = question.get_correct_answer()

        # Evaluate the answer
        evaluation_result = generator.evaluate_answer(
            student_answer,
            correct_answer,
            question_data
        )

        # Create evaluation ID
        evaluation_id = f"eval_{uuid.uuid4().hex[:8]}"

        # Create database model
        evaluation = Evaluation(
            id=evaluation_id,
            question_id=question_id,
            student_answer=student_answer,
            score=evaluation_result['score']
        )

        # Set feedback JSON
        evaluation.set_feedback(evaluation_result['feedback'])

        # Save to database
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        # Add additional data for response (not stored in DB)
        evaluation._correct_answer = correct_answer
        evaluation._explanation = evaluation_result['explanation']

        return evaluation

    @staticmethod
    def get_evaluation(db: Session, evaluation_id: str) -> Optional[Evaluation]:
        """
        Retrieve an evaluation by ID.

        Args:
            db: Database session
            evaluation_id: Evaluation ID

        Returns:
            Evaluation object or None if not found
        """
        return db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    @staticmethod
    def get_evaluations_for_question(
        db: Session,
        question_id: str,
        limit: int = 100
    ) -> list[Evaluation]:
        """
        Get all evaluations for a specific question.

        Args:
            db: Database session
            question_id: Question ID
            limit: Maximum number of evaluations to return

        Returns:
            List of Evaluation objects
        """
        return (
            db.query(Evaluation)
            .filter(Evaluation.question_id == question_id)
            .order_by(Evaluation.evaluated_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_evaluation_statistics(db: Session, question_id: str) -> Dict[str, Any]:
        """
        Get statistics for all evaluations of a question.

        Args:
            db: Database session
            question_id: Question ID

        Returns:
            Dictionary with statistics (count, average score, etc.)
        """
        evaluations = EvaluationService.get_evaluations_for_question(db, question_id)

        if not evaluations:
            return {
                'question_id': question_id,
                'total_evaluations': 0,
                'average_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0
            }

        scores = [e.score for e in evaluations]

        return {
            'question_id': question_id,
            'total_evaluations': len(evaluations),
            'average_score': round(sum(scores) / len(scores), 2),
            'min_score': min(scores),
            'max_score': max(scores)
        }