"""
Service layer for test management (combining multiple questions).
"""
from sqlalchemy.orm import Session
from database.models import Test, TestQuestion, Question
from typing import List, Optional, Dict, Any
import uuid


class TestService:
    """Service for managing tests (collections of questions)."""

    @staticmethod
    def create_test(
        db: Session,
        title: str,
        question_ids: List[str]
    ) -> Optional[Test]:
        """
        Create a test by combining multiple questions.

        Args:
            db: Database session
            title: Test title
            question_ids: List of question IDs to include

        Returns:
            Test object or None if any question not found

        Raises:
            ValueError: If question_ids is empty or contains duplicates
        """
        if not question_ids:
            raise ValueError("Must provide at least one question ID")

        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Duplicate question IDs are not allowed")

        # Verify all questions exist
        for qid in question_ids:
            question = db.query(Question).filter(Question.id == qid).first()
            if not question:
                return None

        # Create test ID
        test_id = f"test_{uuid.uuid4().hex[:8]}"

        # Create test
        test = Test(
            id=test_id,
            title=title
        )

        db.add(test)
        db.flush()  # Get the test ID before adding associations

        # Create associations with ordering
        for order_index, question_id in enumerate(question_ids):
            test_question = TestQuestion(
                test_id=test_id,
                question_id=question_id,
                order_index=order_index
            )
            db.add(test_question)

        db.commit()
        db.refresh(test)

        return test

    @staticmethod
    def get_test(db: Session, test_id: str) -> Optional[Test]:
        """
        Retrieve a test by ID.

        Args:
            db: Database session
            test_id: Test ID

        Returns:
            Test object or None if not found
        """
        return db.query(Test).filter(Test.id == test_id).first()

    @staticmethod
    def get_test_questions(db: Session, test_id: str) -> Optional[List[Question]]:
        """
        Get all questions in a test, ordered by their position.

        Args:
            db: Database session
            test_id: Test ID

        Returns:
            List of Question objects in order, or None if test not found
        """
        test = TestService.get_test(db, test_id)

        if not test:
            return None

        # Get questions through the association table, ordered
        test_questions = (
            db.query(TestQuestion)
            .filter(TestQuestion.test_id == test_id)
            .order_by(TestQuestion.order_index)
            .all()
        )

        # Get the actual Question objects
        questions = []
        for tq in test_questions:
            question = db.query(Question).filter(Question.id == tq.question_id).first()
            if question:
                questions.append(question)

        return questions

    @staticmethod
    def get_all_tests(db: Session, limit: int = 100) -> List[Test]:
        """
        Retrieve all tests.

        Args:
            db: Database session
            limit: Maximum number of tests to return

        Returns:
            List of Test objects
        """
        return db.query(Test).order_by(Test.created_at.desc()).limit(limit).all()

    @staticmethod
    def delete_test(db: Session, test_id: str) -> bool:
        """
        Delete a test from the database.

        Args:
            db: Database session
            test_id: Test ID

        Returns:
            True if deleted, False if not found
        """
        test = TestService.get_test(db, test_id)

        if not test:
            return False

        db.delete(test)
        db.commit()
        return True

    @staticmethod
    def get_test_summary(db: Session, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of the test including question count and types.

        Args:
            db: Database session
            test_id: Test ID

        Returns:
            Dictionary with test summary, or None if test not found
        """
        test = TestService.get_test(db, test_id)

        if not test:
            return None

        questions = TestService.get_test_questions(db, test_id)

        # Count questions by type
        type_counts = {}
        difficulty_counts = {}

        for q in questions:
            type_counts[q.type] = type_counts.get(q.type, 0) + 1
            difficulty_counts[q.difficulty] = difficulty_counts.get(q.difficulty, 0) + 1

        return {
            'test_id': test_id,
            'title': test.title,
            'created_at': test.created_at.isoformat() if test.created_at else None,
            'total_questions': len(questions),
            'questions_by_type': type_counts,
            'questions_by_difficulty': difficulty_counts
        }