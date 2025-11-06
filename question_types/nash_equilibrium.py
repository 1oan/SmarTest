"""
Nash Equilibrium question type implementation.
Generates game theory questions about pure Nash equilibria in normal form games.
"""
import random
import re
from typing import Dict, Any, List, Tuple, Optional
from question_types.base import QuestionTypeBase


class NashEquilibrium(QuestionTypeBase):
    """
    Nash Equilibrium question generator and evaluator.

    Highly parameterizable - supports any matrix size and payoff range.
    """

    def generate_question(self, difficulty: str = "medium", **kwargs) -> Dict[str, Any]:
        """
        Generate a Nash equilibrium question with random payoff matrix.

        Args:
            difficulty: "easy" (2x2), "medium" (2x3 or 3x2), "hard" (3x3 or larger)
            **kwargs:
                - rows: int (override default rows based on difficulty)
                - cols: int (override default cols based on difficulty)
                - min_payoff: int (default 0)
                - max_payoff: int (default 10)
        """
        # Get matrix dimensions
        rows = kwargs.get('rows') or self._get_default_rows(difficulty)
        cols = kwargs.get('cols') or self._get_default_cols(difficulty)
        min_payoff = kwargs.get('min_payoff', 0)
        max_payoff = kwargs.get('max_payoff', 10)

        # Generate random payoff matrix
        matrix = self._generate_random_matrix(rows, cols, min_payoff, max_payoff)

        # Generate labels for rows and columns
        row_labels = self._generate_labels(rows, 'row')
        col_labels = self._generate_labels(cols, 'col')

        # Create question data
        question_data = {
            'matrix': matrix,
            'rows': rows,
            'cols': cols,
            'row_labels': row_labels,
            'col_labels': col_labels
        }

        # Compute correct answer immediately
        correct_answer = self.generate_answer(question_data)

        # Format human-readable question text
        question_text = self._format_question_text(matrix, rows, cols, row_labels, col_labels)

        return {
            'type': 'nash',
            'difficulty': difficulty,
            'question_text': question_text,
            'question_data': question_data,
            'correct_answer': correct_answer
        }

    def generate_answer(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute the correct answer by finding all pure Nash equilibria.

        Args:
            question_data: Dictionary with matrix, rows, cols

        Returns:
            Dictionary with:
                - exists: bool (whether any Nash equilibrium exists)
                - equilibria: list of (row_index, col_index) tuples
                - row_labels: labels for rows
                - col_labels: labels for columns
        """
        matrix = question_data['matrix']
        rows = question_data['rows']
        cols = question_data['cols']

        # Find all Nash equilibria
        equilibria = self._find_nash_equilibria(matrix, rows, cols)

        return {
            'exists': len(equilibria) > 0,
            'equilibria': equilibria,
            'row_labels': question_data.get('row_labels', []),
            'col_labels': question_data.get('col_labels', [])
        }

    def evaluate_answer(
        self,
        student_answer: str,
        correct_answer: Dict[str, Any],
        question_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate student's answer with partial credit.

        Scoring:
        - 50 points: Correct existence (yes/no)
        - 50 points: Correct positions
          - Full credit if all equilibria found and no false positives
          - Partial credit proportional to correct finds
          - Penalty for false positives
        """
        feedback = []
        score = 0.0

        # Parse student answer
        student_exists, student_positions = self._parse_student_answer(
            student_answer, question_data
        )

        correct_exists = correct_answer['exists']
        correct_positions = set(map(tuple, correct_answer['equilibria']))

        # Score existence (50 points)
        if student_exists == correct_exists:
            score += 50
            if correct_exists:
                feedback.append("✓ Correct: You correctly identified that a Nash equilibrium exists")
            else:
                feedback.append("✓ Correct: You correctly identified that no Nash equilibrium exists")
        else:
            if student_exists:
                feedback.append("✗ Incorrect: You said Nash equilibrium exists, but it doesn't")
            else:
                feedback.append("✗ Incorrect: You said no Nash equilibrium exists, but at least one does exist")

        # Score positions (50 points) - only if equilibria exist
        if correct_exists:
            student_positions_set = set(student_positions)

            # True positives (correctly found equilibria)
            correct_found = student_positions_set & correct_positions
            # False positives (incorrectly identified as equilibria)
            incorrect_found = student_positions_set - correct_positions
            # False negatives (missed equilibria)
            missed = correct_positions - student_positions_set

            total_correct = len(correct_positions)

            if len(correct_found) == total_correct and len(incorrect_found) == 0:
                score += 50
                feedback.append("✓ Perfect: All Nash equilibria correctly identified with no errors")
            elif len(student_positions_set) == 0:
                feedback.append("✗ No positions provided: You didn't specify where the Nash equilibria are")
            else:
                # Partial credit calculation
                position_score = (len(correct_found) / total_correct) * 50

                # Penalty for false positives (up to 50% of position score)
                if len(incorrect_found) > 0:
                    penalty = min((len(incorrect_found) / total_correct) * 25, position_score * 0.5)
                    position_score = max(0, position_score - penalty)

                score += position_score

                # Detailed feedback
                if correct_found:
                    row_labels = question_data.get('row_labels', [])
                    col_labels = question_data.get('col_labels', [])
                    found_list = [f"({row_labels[r]}, {col_labels[c]})" for r, c in correct_found]
                    feedback.append(f"~ Partial: Correctly found {len(correct_found)}/{total_correct} equilibria: {', '.join(found_list)}")

                if incorrect_found:
                    row_labels = question_data.get('row_labels', [])
                    col_labels = question_data.get('col_labels', [])
                    incorrect_list = [f"({row_labels[r]}, {col_labels[c]})" for r, c in incorrect_found]
                    feedback.append(f"✗ Error: Incorrectly identified {len(incorrect_found)} non-equilibria: {', '.join(incorrect_list)}")

                if missed:
                    row_labels = question_data.get('row_labels', [])
                    col_labels = question_data.get('col_labels', [])
                    missed_list = [f"({row_labels[r]}, {col_labels[c]})" for r, c in missed]
                    feedback.append(f"✗ Missed: {len(missed)} equilibria not found: {', '.join(missed_list)}")

        return {
            'score': round(score, 2),
            'feedback': feedback,
            'correct_answer': correct_answer,
            'explanation': self.answer_question(question_data, 'detailed')
        }

    def answer_question(
        self,
        question_data: Dict[str, Any],
        detail_level: str = "detailed"
    ) -> str:
        """
        Generate explanation of the solution.

        Args:
            question_data: The question data
            detail_level: "concise" or "detailed"

        Returns:
            Explanation string
        """
        matrix = question_data['matrix']
        rows = question_data['rows']
        cols = question_data['cols']
        row_labels = question_data.get('row_labels', [str(i) for i in range(rows)])
        col_labels = question_data.get('col_labels', [str(j) for j in range(cols)])

        equilibria = self._find_nash_equilibria(matrix, rows, cols)

        if detail_level == "concise":
            if equilibria:
                eq_list = [f"({row_labels[r]}, {col_labels[c]})" for r, c in equilibria]
                return f"Yes, pure Nash equilibrium exists at: {', '.join(eq_list)}"
            else:
                return "No pure Nash equilibrium exists in this game."

        # Detailed explanation
        explanation = ["NASH EQUILIBRIUM ANALYSIS", "=" * 50, ""]
        explanation.append("A Nash equilibrium is a strategy profile where no player can improve")
        explanation.append("their payoff by unilaterally changing their strategy.\n")
        explanation.append("Checking each cell (strategy profile):\n")

        for i in range(rows):
            for j in range(cols):
                row_label = row_labels[i]
                col_label = col_labels[j]
                p1_payoff, p2_payoff = matrix[f"{i},{j}"]

                explanation.append(f"Cell ({row_label}, {col_label}): Payoffs = ({p1_payoff}, {p2_payoff})")

                # Check Player 1 best response
                p1_best = True
                for alt_i in range(rows):
                    if alt_i != i:
                        alt_payoff = matrix[f"{alt_i},{j}"][0]
                        if alt_payoff > p1_payoff:
                            p1_best = False
                            explanation.append(f"  Player 1: NOT best response (can get {alt_payoff} by switching to {row_labels[alt_i]})")
                            break

                if p1_best:
                    explanation.append(f"  Player 1: ✓ Best response (no better alternative)")

                # Check Player 2 best response
                p2_best = True
                for alt_j in range(cols):
                    if alt_j != j:
                        alt_payoff = matrix[f"{i},{alt_j}"][1]
                        if alt_payoff > p2_payoff:
                            p2_best = False
                            explanation.append(f"  Player 2: NOT best response (can get {alt_payoff} by switching to {col_labels[alt_j]})")
                            break

                if p2_best:
                    explanation.append(f"  Player 2: ✓ Best response (no better alternative)")

                # Conclusion for this cell
                if p1_best and p2_best:
                    explanation.append(f"  >>> NASH EQUILIBRIUM at ({row_label}, {col_label}) ✓")
                else:
                    explanation.append(f"  >>> Not a Nash equilibrium")

                explanation.append("")

        # Final summary
        explanation.append("=" * 50)
        explanation.append("CONCLUSION:")
        if equilibria:
            eq_list = [f"({row_labels[r]}, {col_labels[c]})" for r, c in equilibria]
            explanation.append(f"Pure Nash equilibrium exists at: {', '.join(eq_list)}")
        else:
            explanation.append("No pure Nash equilibrium exists in this game.")

        return "\n".join(explanation)

    # Helper methods

    def _get_default_rows(self, difficulty: str) -> int:
        """Get default number of rows based on difficulty."""
        if difficulty == "easy":
            return 2
        elif difficulty == "medium":
            return random.choice([2, 3])
        else:  # hard
            return random.choice([3, 4])

    def _get_default_cols(self, difficulty: str) -> int:
        """Get default number of columns based on difficulty."""
        if difficulty == "easy":
            return 2
        elif difficulty == "medium":
            return random.choice([2, 3])
        else:  # hard
            return random.choice([3, 4])

    def _generate_random_matrix(
        self,
        rows: int,
        cols: int,
        min_payoff: int,
        max_payoff: int
    ) -> Dict[str, Tuple[int, int]]:
        """
        Generate random payoff matrix.

        Returns:
            Dictionary mapping "row,col" to (player1_payoff, player2_payoff)
        """
        matrix = {}
        for i in range(rows):
            for j in range(cols):
                p1_payoff = random.randint(min_payoff, max_payoff)
                p2_payoff = random.randint(min_payoff, max_payoff)
                matrix[f"{i},{j}"] = (p1_payoff, p2_payoff)
        return matrix

    def _generate_labels(self, count: int, label_type: str) -> List[str]:
        """
        Generate labels for rows or columns.

        Args:
            count: Number of labels needed
            label_type: "row" or "col"

        Returns:
            List of label strings
        """
        if label_type == "row":
            if count <= 3:
                return ["U", "M", "D"][:count]
            else:
                return [f"R{i+1}" for i in range(count)]
        else:  # column
            if count <= 3:
                return ["L", "C", "R"][:count]
            else:
                return [f"C{i+1}" for i in range(count)]

    def _format_question_text(
        self,
        matrix: Dict[str, Tuple[int, int]],
        rows: int,
        cols: int,
        row_labels: List[str],
        col_labels: List[str]
    ) -> str:
        """Format the question as human-readable text with matrix display."""
        lines = [
            "Consider the following two-player game in normal form:",
            "",
            "Player 1 chooses rows, Player 2 chooses columns.",
            "Payoffs are shown as (Player 1, Player 2).",
            ""
        ]

        # Build matrix display
        # Header row
        header = "      " + "  ".join(f"{label:>8}" for label in col_labels)
        lines.append(header)
        lines.append("    " + "-" * (10 * cols))

        # Data rows
        for i in range(rows):
            row_label = row_labels[i]
            cells = []
            for j in range(cols):
                p1, p2 = matrix[f"{i},{j}"]
                cells.append(f"({p1:>2},{p2:>2})")
            row_line = f"{row_label:>2} |" + "  ".join(f"{cell:>8}" for cell in cells)
            lines.append(row_line)

        lines.append("")
        lines.append("Question: Does a pure Nash equilibrium exist in this game? If yes, identify all pure Nash equilibria.")

        return "\n".join(lines)

    def _find_nash_equilibria(
        self,
        matrix: Dict[str, Tuple[int, int]],
        rows: int,
        cols: int
    ) -> List[Tuple[int, int]]:
        """
        Core Nash equilibrium detection algorithm.

        For each cell (i, j):
          1. Check if Player 1 is best responding (fix column j, compare rows)
          2. Check if Player 2 is best responding (fix row i, compare columns)
          3. If both are best responding, it's a Nash equilibrium

        Returns:
            List of (row_index, col_index) tuples representing Nash equilibria
        """
        equilibria = []

        for i in range(rows):
            for j in range(cols):
                p1_payoff, p2_payoff = matrix[f"{i},{j}"]

                # Check if Player 1 is best responding
                p1_best_response = True
                for alt_i in range(rows):
                    if alt_i != i:
                        alt_p1_payoff = matrix[f"{alt_i},{j}"][0]
                        if alt_p1_payoff > p1_payoff:
                            p1_best_response = False
                            break

                # Check if Player 2 is best responding
                p2_best_response = True
                for alt_j in range(cols):
                    if alt_j != j:
                        alt_p2_payoff = matrix[f"{i},{alt_j}"][1]
                        if alt_p2_payoff > p2_payoff:
                            p2_best_response = False
                            break

                # Both best responding? -> Nash equilibrium
                if p1_best_response and p2_best_response:
                    equilibria.append((i, j))

        return equilibria

    def _parse_student_answer(
        self,
        student_answer: str,
        question_data: Dict[str, Any]
    ) -> Tuple[bool, List[Tuple[int, int]]]:
        """
        Parse student's text answer to extract existence and positions.
        Uses two-stage parsing: detect claim type, then detect negation.

        Returns:
            Tuple of (exists: bool, positions: List[Tuple[int, int]])
        """
        answer_lower = student_answer.lower().strip()
        row_labels = question_data.get('row_labels', [])
        col_labels = question_data.get('col_labels', [])

        # STAGE 1: Determine what type of claim is being made
        claim_type = self._extract_existence_claim(answer_lower)

        # STAGE 2: Determine if claim is negated or affirmed
        if claim_type == "equilibrium_mentioned":
            is_negated = self._detect_negation(answer_lower)
            exists = not is_negated
        elif claim_type == "direct_answer":
            # Simple yes/no answer
            exists = answer_lower.startswith('yes')
        else:
            # No clear claim, default to False
            exists = False

        # Extract positions using regex
        positions = self._extract_positions(student_answer, row_labels, col_labels)

        return exists, positions

    def _extract_existence_claim(self, answer_lower: str) -> Optional[str]:
        """
        Extract what type of claim the student is making.

        Returns:
            "equilibrium_mentioned" - student discusses equilibrium
            "direct_answer" - student just says yes/no (with optional qualifiers)
            None - no clear claim
        """
        # Check for equilibrium-related keywords
        equilibrium_keywords = [
            r'\bequilibrium\b',
            r'\bequilibria\b',
            r'\bnash\b',
            r'\bstrategy\s+profile\b'
        ]

        if any(re.search(kw, answer_lower) for kw in equilibrium_keywords):
            return "equilibrium_mentioned"

        # Check for existence/quantifier words that imply a claim about equilibrium
        existence_keywords = [
            r'\bexists?\b',
            r'\bthere\s+(?:is|are|isn\'t|aren\'t)\b',
            r'\byes\b',
            r'\bno\b',
            r'\bnone\b',
            r'\bfound\b',
            r'\bidentified\b'
        ]

        if any(re.search(kw, answer_lower) for kw in existence_keywords):
            return "equilibrium_mentioned"

        return None

    def _detect_negation(self, answer_lower: str) -> bool:
        """
        Detect if the student's claim is negated.
        Uses weighted pattern matching with context awareness.

        Returns:
            True if negated (no equilibrium exists)
            False if affirmed (equilibrium exists)
        """
        # Check for strong sentence-initial affirmations first (highest priority)
        if re.match(r'^\s*yes\b', answer_lower):
            return False  # Definitely affirmed

        # Negation patterns with weights (higher = stronger signal)
        negation_patterns = [
            # Strong sentence-level negations
            (r'^\s*no\b', 10),  # "No" at sentence start
            (r'\bthere\s+(?:is|are)\s+no\b', 10),  # "there is no", "there are no"
            (r'\bthere\s+(?:isn\'t|aren\'t)\b', 10),  # "there isn't", "there aren't"

            # Verb negations
            (r'\bdo(?:es)?n\'t\s+exist\b', 9),  # "doesn't exist", "don't exist"
            (r'\bdon\'t\s+exist\b', 9),  # "don't exist"
            (r'\bnot\s+exist\b', 9),  # "not exist"
            (r'\bcannot\s+(?:find|be)\b', 8),  # "cannot find", "cannot be"
            (r'\bcan\'t\s+(?:find|be)\b', 8),  # "can't find", "can't be"

            # Quantifier negations
            (r'\bno\s+(?:pure\s+)?(?:nash\s+)?equilibri(?:um|a)\b', 9),  # "no equilibrium", "no pure nash equilibrium"
            (r'\bnone\b', 8),  # "none"
            (r'\bneither\b', 7),  # "neither"
            (r'\bzero\s+equilibri', 8),  # "zero equilibria"
        ]

        # Affirmation patterns with weights
        affirmation_patterns = [
            # Strong affirmations
            (r'\bequilibri(?:um|a)\s+(?:does\s+)?exists?\b', 10),  # "equilibrium exists"
            (r'\bthere\s+(?:is|are)\s+(?:a|an|one|two|equilibri)', 10),  # "there is an equilibrium"
            (r'\bexists?\s+at\b', 9),  # "exists at"
            (r'\bexists?\b', 7),  # "exists" alone
            (r'\b(?:found|identified)\s+(?:a|an|equilibri)', 8),  # "found an equilibrium"
            (r'\bhas\s+(?:a|an|equilibri)', 7),  # "has an equilibrium"
        ]

        # Calculate weighted scores
        negation_score = sum(
            weight for pattern, weight in negation_patterns
            if re.search(pattern, answer_lower)
        )
        affirmation_score = sum(
            weight for pattern, weight in affirmation_patterns
            if re.search(pattern, answer_lower)
        )

        # Return True if negation score is higher (meaning "doesn't exist")
        return negation_score > affirmation_score

    def _extract_positions(
        self,
        student_answer: str,
        row_labels: List[str],
        col_labels: List[str]
    ) -> List[Tuple[int, int]]:
        """
        Extract equilibrium positions from student answer.

        Returns:
            List of (row_idx, col_idx) tuples
        """
        positions = []

        if not row_labels or not col_labels:
            return positions

        # Create pattern from labels
        row_pattern = "|".join(re.escape(label) for label in row_labels)
        col_pattern = "|".join(re.escape(label) for label in col_labels)
        pattern = rf'\(({row_pattern})\s*,\s*({col_pattern})\)'

        matches = re.findall(pattern, student_answer, re.IGNORECASE)

        for row_label, col_label in matches:
            # Find indices
            try:
                row_idx = row_labels.index(row_label.upper())
                col_idx = col_labels.index(col_label.upper())
                positions.append((row_idx, col_idx))
            except ValueError:
                continue

        return positions