"""
SQLAlchemy ORM models for the SmarTest application.
"""
from sqlalchemy import Column, String, Integer, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base
import json


class Question(Base):
    """
    Model for storing generated questions.
    """
    __tablename__ = "questions"

    id = Column(String, primary_key=True, index=True)  # e.g., "nash_001"
    type = Column(String, nullable=False, index=True)  # "nash", "minimax", "csp", "search"
    difficulty = Column(String, nullable=False)  # "easy", "medium", "hard"
    question_text = Column(Text, nullable=False)  # Human-readable question
    question_data = Column(Text, nullable=False)  # JSON string with type-specific data
    correct_answer = Column(Text, nullable=False)  # JSON string with computed answer
    explanation = Column(Text, nullable=True)  # Detailed explanation
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    evaluations = relationship("Evaluation", back_populates="question", cascade="all, delete-orphan")
    test_associations = relationship("TestQuestion", back_populates="question", cascade="all, delete-orphan")

    def get_question_data(self):
        """Parse question_data from JSON string to dict."""
        return json.loads(self.question_data)

    def get_correct_answer(self):
        """Parse correct_answer from JSON string to dict."""
        return json.loads(self.correct_answer)

    def set_question_data(self, data: dict):
        """Convert question_data dict to JSON string."""
        self.question_data = json.dumps(data)

    def set_correct_answer(self, answer: dict):
        """Convert correct_answer dict to JSON string."""
        self.correct_answer = json.dumps(answer)


class Test(Base):
    """
    Model for storing test collections (combination of multiple questions).
    """
    __tablename__ = "tests"

    id = Column(String, primary_key=True, index=True)  # e.g., "test_001"
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    question_associations = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")


class TestQuestion(Base):
    """
    Many-to-many relationship table between tests and questions.
    Includes ordering information.
    """
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String, ForeignKey("tests.id"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    order_index = Column(Integer, nullable=False)  # Order of question in test

    # Relationships
    test = relationship("Test", back_populates="question_associations")
    question = relationship("Question", back_populates="test_associations")


class Evaluation(Base):
    """
    Model for storing student answer evaluations.
    """
    __tablename__ = "evaluations"

    id = Column(String, primary_key=True, index=True)  # e.g., "eval_001"
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    student_answer = Column(Text, nullable=False)  # Raw student answer text
    score = Column(Float, nullable=False)  # Score from 0 to 100
    feedback = Column(Text, nullable=False)  # JSON array of feedback strings
    evaluated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    question = relationship("Question", back_populates="evaluations")

    def get_feedback(self):
        """Parse feedback from JSON string to list."""
        return json.loads(self.feedback)

    def set_feedback(self, feedback_list: list):
        """Convert feedback list to JSON string."""
        self.feedback = json.dumps(feedback_list)