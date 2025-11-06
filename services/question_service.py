"""
Service layer for question generation and retrieval.
"""
from sqlalchemy.orm import Session
from database.models import Question
from question_types.nash_equilibrium import NashEquilibrium
from typing import List, Optional, Dict, Any
import uuid


class QuestionService:
    """Service for managing question generation and retrieval."""

    # Map question types to their implementation classes
    QUESTION_TYPES = {
        'nash': NashEquilibrium(),
        # Future: 'minimax': MinMaxAlphaBeta(),
        # Future: 'csp': ConstraintSatisfaction(),
        # Future: 'search': SearchStrategy(),
    }

    @staticmethod
    def generate_questions(
        db: Session,
        question_type: str,
        count: int = 1,
        difficulty: str = "medium",
        **kwargs
    ) -> List[Question]:
        """
        Generate multiple questions and save to database.

        Args:
            db: Database session
            question_type: Type of question ("nash", "minimax", "csp", "search")
            count: Number of questions to generate
            difficulty: Difficulty level ("easy", "medium", "hard")
            **kwargs: Additional parameters for question generation

        Returns:
            List of generated Question objects

        Raises:
            ValueError: If question type is not supported
        """
        if question_type not in QuestionService.QUESTION_TYPES:
            raise ValueError(f"Unsupported question type: {question_type}")

        generator = QuestionService.QUESTION_TYPES[question_type]
        generated_questions = []

        for _ in range(count):
            # Generate question data
            question_dict = generator.generate_question(difficulty, **kwargs)

            # Create unique ID
            question_id = f"{question_type}_{uuid.uuid4().hex[:8]}"

            # Get explanation
            explanation = generator.answer_question(
                question_dict['question_data'],
                detail_level='detailed'
            )

            # Create database model
            question = Question(
                id=question_id,
                type=question_dict['type'],
                difficulty=question_dict['difficulty'],
                question_text=question_dict['question_text'],
                explanation=explanation
            )

            # Set JSON fields
            question.set_question_data(question_dict['question_data'])
            question.set_correct_answer(question_dict['correct_answer'])

            # Save to database
            db.add(question)
            generated_questions.append(question)

        db.commit()

        # Refresh to get created_at timestamps
        for q in generated_questions:
            db.refresh(q)

        return generated_questions

    @staticmethod
    def get_question(db: Session, question_id: str) -> Optional[Question]:
        """
        Retrieve a question by ID.

        Args:
            db: Database session
            question_id: Question ID

        Returns:
            Question object or None if not found
        """
        return db.query(Question).filter(Question.id == question_id).first()

    @staticmethod
    def get_all_questions(
        db: Session,
        question_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 100
    ) -> List[Question]:
        """
        Retrieve all questions with optional filters.

        Args:
            db: Database session
            question_type: Filter by type (optional)
            difficulty: Filter by difficulty (optional)
            limit: Maximum number of questions to return

        Returns:
            List of Question objects
        """
        query = db.query(Question)

        if question_type:
            query = query.filter(Question.type == question_type)

        if difficulty:
            query = query.filter(Question.difficulty == difficulty)

        return query.order_by(Question.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_correct_answer(
        db: Session,
        question_id: str,
        detail_level: str = "detailed"
    ) -> Optional[Dict[str, Any]]:
        """
        Get the correct answer with explanation for a question.

        Args:
            db: Database session
            question_id: Question ID
            detail_level: "concise" or "detailed"

        Returns:
            Dictionary with answer and explanation, or None if question not found
        """
        question = QuestionService.get_question(db, question_id)

        if not question:
            return None

        correct_answer = question.get_correct_answer()

        # Get detailed explanation if requested
        if detail_level == "detailed":
            explanation = question.explanation
        else:
            # Generate concise explanation
            if question.type in QuestionService.QUESTION_TYPES:
                generator = QuestionService.QUESTION_TYPES[question.type]
                explanation = generator.answer_question(
                    question.get_question_data(),
                    detail_level='concise'
                )
            else:
                explanation = "Answer generation not available for this question type."

        return {
            'question_id': question_id,
            'answer': correct_answer,
            'explanation': explanation,
            'question_type': question.type
        }

    @staticmethod
    def delete_question(db: Session, question_id: str) -> bool:
        """
        Delete a question from the database.

        Args:
            db: Database session
            question_id: Question ID

        Returns:
            True if deleted, False if not found
        """
        question = QuestionService.get_question(db, question_id)

        if not question:
            return False

        db.delete(question)
        db.commit()
        return True