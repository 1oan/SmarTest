"""
Abstract base class for all question types.
Defines the interface that all question types must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class QuestionTypeBase(ABC):
    """
    Abstract base class for question type implementations.

    All question types (Nash, MinMax, CSP, Search) must inherit from this
    class and implement all abstract methods.
    """

    @abstractmethod
    def generate_question(self, difficulty: str = "medium", **kwargs) -> Dict[str, Any]:
        """
        Generate a new question of this type.

        Args:
            difficulty: Difficulty level ("easy", "medium", "hard")
            **kwargs: Additional parameters specific to the question type

        Returns:
            Dictionary containing:
                - type: Question type identifier
                - difficulty: Difficulty level
                - question_text: Human-readable question
                - question_data: Type-specific data structure
                - correct_answer: Computed correct answer
        """
        pass

    @abstractmethod
    def generate_answer(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute the correct answer for a given question.

        Args:
            question_data: The question data structure

        Returns:
            Dictionary containing the correct answer
        """
        pass

    @abstractmethod
    def evaluate_answer(
        self,
        student_answer: str,
        correct_answer: Dict[str, Any],
        question_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a student's answer against the correct answer.

        Args:
            student_answer: Student's answer as text
            correct_answer: The correct answer
            question_data: The question data structure

        Returns:
            Dictionary containing:
                - score: Float from 0 to 100
                - feedback: List of feedback strings
                - correct_answer: The correct answer
                - explanation: Detailed explanation
        """
        pass

    @abstractmethod
    def answer_question(
        self,
        question_data: Dict[str, Any],
        detail_level: str = "detailed"
    ) -> str:
        """
        Generate a detailed explanation of how to solve the question.

        Args:
            question_data: The question data structure
            detail_level: "concise" or "detailed"

        Returns:
            String containing the explanation
        """
        pass