# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SmarTest** - AI-powered exam question generator and evaluator for an Artificial Intelligence course

**Tech Stack:**
- **Backend:** Python + FastAPI + SQLAlchemy + SQLite
- **Frontend:** Vue.js 3 + Vite (separate repository)
- **Current Status:** Basic FastAPI setup complete, implementing database layer

**Project Location:** `~/Facultate/SmarTest/fastapi/`

## Core Features

1. **Question Generation** - Generate 4 types of AI exam questions with configurable difficulty
2. **Test Builder** - Combine multiple questions into tests
3. **Answer Generator** - Application answers its own questions with detailed explanations
4. **Answer Evaluator** - Evaluate student answers (0-100%) with feedback

## Required Question Types

| Type | Description |
|------|-------------|
| **Nash Equilibrium** | Given game matrix → Find pure Nash equilibria |
| **MinMax Alpha-Beta** | Given game tree → Root value + nodes visited with pruning |
| **CSP** | Given variables/domains/constraints → Solution using Backtracking+FC/MRV/AC-3 |
| **Search Strategy** | Given problem type → Best search algorithm |

**Development Strategy:** Implement Nash Equilibrium fully first as template for others.

## Development Commands

```bash
# Activate virtual environment (ALWAYS do this first)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server with auto-reload
uvicorn app:app --reload --port 8000

# Run server (simple)
python app.py

# Install new package and update requirements
pip install package-name
pip freeze > requirements.txt

# Access API documentation
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

## Architecture

### Directory Structure

```
fastapi/
├── app.py                      # FastAPI entry point
├── requirements.txt            # Dependencies
├── database.db                 # SQLite database (created at runtime)
│
├── api/                        # API layer
│   ├── routes.py              # API endpoints
│   └── schemas.py             # Pydantic models
│
├── database/                   # Database layer
│   ├── connection.py          # SQLAlchemy setup
│   └── models.py              # ORM models
│
├── question_types/             # Question type implementations
│   ├── base.py                # Abstract base class
│   ├── nash_equilibrium.py   # Nash implementation (FIRST)
│   ├── minimax.py             # MinMax implementation
│   ├── csp.py                 # CSP implementation
│   └── search_strategy.py     # Search selection implementation
│
├── services/                   # Business logic
│   ├── question_service.py    # Question generation
│   ├── evaluation_service.py  # Answer evaluation
│   └── test_service.py        # Test management
│
├── utils/
│   └── pdf_service.py         # PDF generation/parsing
│
└── config/
    └── settings.py            # Configuration
```

### Database Schema (SQLite + SQLAlchemy)

**4 tables:**

1. **questions** - Generated questions
   - `id` (TEXT PK): "nash_001", "minimax_002"
   - `type` (TEXT): "nash", "minimax", "csp", "search"
   - `difficulty` (TEXT): "easy", "medium", "hard"
   - `question_text` (TEXT): Human-readable question
   - `question_data` (JSON): Type-specific data (matrix, tree, etc.)
   - `correct_answer` (JSON): Computed answer
   - `explanation` (TEXT): Detailed explanation
   - `created_at` (TIMESTAMP)

2. **tests** - Test collections
   - `id` (TEXT PK), `title` (TEXT), `created_at` (TIMESTAMP)

3. **test_questions** - Many-to-many relationship
   - `id` (INT PK AUTO), `test_id` (TEXT FK), `question_id` (TEXT FK), `order_index` (INT)

4. **evaluations** - Student answer evaluations
   - `id` (TEXT PK), `question_id` (TEXT FK), `student_answer` (TEXT)
   - `score` (REAL 0-100), `feedback` (JSON), `evaluated_at` (TIMESTAMP)

### Question Type Base Class

All question types inherit from `QuestionTypeBase` and implement:

- `generate_question(difficulty)` - Generate random question instance
- `generate_answer(question_data)` - Compute correct answer
- `evaluate_answer(student_answer, correct_answer, question_data)` - Score (0-100) with feedback
- `answer_question(question_data, detail_level)` - Generate step-by-step explanation

## Nash Equilibrium Implementation (Reference)

**Question Generation:**
- Matrix size by difficulty: easy (2x2), medium (2x3 or 3x2), hard (3x3)
- Random payoffs: 0-10 for each player in each cell
- Mix questions with/without Nash equilibria

**Core Nash Detection Algorithm:**
```
For each cell (i, j):
    1. Check Player 1 best response:
       - Fix column j (P2's strategy)
       - Compare row i payoff with all other rows
       - P1 best-responding if no other row gives higher payoff

    2. Check Player 2 best response:
       - Fix row i (P1's strategy)
       - Compare column j payoff with all other columns
       - P2 best-responding if no other column gives higher payoff

    3. If BOTH best-responding → Nash equilibrium at (i, j)
```

**Evaluation Scoring:**
- 50 points: Correct existence (yes/no)
- 50 points: Correct position(s)
- Partial credit for finding some but not all equilibria

## API Endpoints

Core endpoints to implement:

- `POST /api/generate-questions` - Generate questions (type, count, difficulty)
- `POST /api/evaluate-answer` - Evaluate student answer, return score + feedback
- `GET /api/questions/{id}/answer` - Get correct answer with explanation
- `POST /api/create-test` - Create test from question IDs
- `GET /api/questions` - List all questions
- `GET /api/export-pdf/{id}` - Export question as PDF (future)

## Implementation Workflow

**Phase 1: Database Layer**
1. Create `database/connection.py` - SQLAlchemy setup, session factory, `init_db()`, `get_db()` dependency
2. Create `database/models.py` - Define all 4 models (Question, Test, TestQuestion, Evaluation)
3. Update `app.py` to call `init_db()` on startup

**Phase 2: Nash Equilibrium (Template)**
1. Create `question_types/base.py` - Abstract base class with interface
2. Create `question_types/nash_equilibrium.py` - Full implementation (generation, detection, evaluation)
3. Test independently before integration

**Phase 3: Services Layer**
1. `services/question_service.py` - Question generation and retrieval
2. `services/evaluation_service.py` - Answer evaluation logic
3. `services/test_service.py` - Test management

**Phase 4: API Layer**
1. `api/schemas.py` - Pydantic models for requests/responses
2. `api/routes.py` - Implement all endpoints
3. Update `app.py` - Add routes, CORS middleware
4. Test via Swagger UI at http://localhost:8000/docs

**Phase 5: Additional Question Types**
- Replicate Nash pattern for MinMax, CSP, Search Strategy

**Phase 6: PDF Support** (lower priority)
- `utils/pdf_service.py` - Generation and parsing

## Code Style

- Follow PEP 8
- Use type hints for function signatures
- Add docstrings to classes and non-trivial functions
- Use Pydantic models for validation
- Store complex data (matrices, trees) as JSON in database
- Use FastAPI dependency injection for database sessions

## Important Notes

- Database file `database.db` created automatically on first run
- Test endpoints using Swagger UI at `/docs`
- Always activate virtual environment before development
- Question generation should create variety (with/without solutions)
- Use regex for parsing student answers: `r'\(([UMD]),\s*([LCR])\)'`