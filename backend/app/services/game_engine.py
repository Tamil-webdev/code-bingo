"""
Game engine service.
Core game logic: board generation, answer validation, scoring, bingo detection.
"""

import random
from typing import List, Tuple, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.board import Board, BoardTile, TileStatus
from app.models.question import Question, QuestionDifficulty
from app.models.attempt import Attempt
from app.models.score import Score
from app.models.leaderboard import LeaderboardEntry
from app.models.round import Round


class GameEngine:
    """Core game logic for Code Bingo."""

    # Scoring constants
    CORRECT_ANSWER_POINTS = 10
    FASTEST_CORRECT_BONUS = 5
    HARD_QUESTION_BONUS = 5
    PERFECT_ROUND_BONUS = 20

    @staticmethod
    async def generate_board(
        db: AsyncSession,
        round_id: UUID,
        team_id: UUID,
        board_size: int,
        difficulty: str,
        num_questions: int,
    ) -> Board:
        """
        Generate a randomized bingo board for a team.
        Selects questions from the pool and assigns to random positions.
        """
        total_tiles = board_size * board_size

        # Build question query based on difficulty
        query = select(Question).where(Question.is_active == True)
        if difficulty != "mixed":
            query = query.where(Question.difficulty == difficulty)

        result = await db.execute(query)
        available_questions = list(result.scalars().all())

        if len(available_questions) < total_tiles:
            # If not enough questions, allow reuse with different tile positions
            selected_questions = random.choices(available_questions, k=total_tiles)
        else:
            selected_questions = random.sample(available_questions, total_tiles)

        # Shuffle for randomization
        random.shuffle(selected_questions)

        # Create the board
        board = Board(
            id=uuid4(),
            round_id=round_id,
            team_id=team_id,
            size=board_size,
        )
        db.add(board)

        # Create tiles
        for idx, question in enumerate(selected_questions):
            row = idx // board_size
            col = idx % board_size
            tile = BoardTile(
                id=uuid4(),
                board_id=board.id,
                question_id=question.id,
                position=idx,
                row=row,
                col=col,
                status=TileStatus.UNANSWERED,
            )
            db.add(tile)

        await db.flush()
        return board

    @staticmethod
    async def submit_answer(
        db: AsyncSession,
        tile: BoardTile,
        team_id: UUID,
        round_id: UUID,
        submitted_answer: str,
        time_taken: float,
    ) -> Tuple[bool, int, str, str]:
        """
        Process an answer submission.
        Returns (is_correct, points_earned, correct_answer, explanation).
        """
        # Get the question
        result = await db.execute(select(Question).where(Question.id == tile.question_id))
        question = result.scalar_one()

        # Check if answer is correct (case-insensitive comparison)
        is_correct = submitted_answer.strip().lower() == question.correct_answer.strip().lower()

        # Calculate points
        points = 0
        if is_correct:
            points = GameEngine.CORRECT_ANSWER_POINTS
            # Hard question bonus
            if question.difficulty == QuestionDifficulty.HARD:
                points += GameEngine.HARD_QUESTION_BONUS

            # Update tile status
            tile.status = TileStatus.CORRECT
        else:
            tile.status = TileStatus.WRONG

        tile.answered_at = datetime.utcnow()

        # Record attempt
        attempt = Attempt(
            id=uuid4(),
            board_tile_id=tile.id,
            team_id=team_id,
            round_id=round_id,
            question_id=question.id,
            submitted_answer=submitted_answer,
            is_correct=is_correct,
            time_taken_seconds=time_taken,
            points_earned=points,
        )
        db.add(attempt)

        await db.flush()
        return is_correct, points, question.correct_answer, question.explanation or ""

    @staticmethod
    def detect_bingos(tiles: List[BoardTile], board_size: int) -> List[List[int]]:
        """
        Detect all bingo lines (horizontal, vertical, diagonal).
        Returns list of position arrays that form bingos.
        """
        bingo_lines = []

        # Create a grid of statuses
        grid = {}
        for tile in tiles:
            grid[(tile.row, tile.col)] = tile.status == TileStatus.CORRECT or tile.status == TileStatus.BINGO

        # Check horizontal lines
        for row in range(board_size):
            if all(grid.get((row, col), False) for col in range(board_size)):
                bingo_lines.append([row * board_size + col for col in range(board_size)])

        # Check vertical lines
        for col in range(board_size):
            if all(grid.get((row, col), False) for row in range(board_size)):
                bingo_lines.append([row * board_size + col for row in range(board_size)])

        # Check main diagonal (top-left to bottom-right)
        if all(grid.get((i, i), False) for i in range(board_size)):
            bingo_lines.append([i * board_size + i for i in range(board_size)])

        # Check anti-diagonal (top-right to bottom-left)
        if all(grid.get((i, board_size - 1 - i), False) for i in range(board_size)):
            bingo_lines.append([i * board_size + (board_size - 1 - i) for i in range(board_size)])

        return bingo_lines

    @staticmethod
    async def update_score(
        db: AsyncSession,
        team_id: UUID,
        round_id: UUID,
        board: Board,
    ) -> Score:
        """Update the team's score for the round."""
        # Get or create score record
        result = await db.execute(
            select(Score).where(
                and_(Score.team_id == team_id, Score.round_id == round_id)
            )
        )
        score = result.scalar_one_or_none()
        if not score:
            score = Score(id=uuid4(), team_id=team_id, round_id=round_id)
            db.add(score)

        # Get all attempts for this team in this round
        attempts_result = await db.execute(
            select(Attempt).where(
                and_(Attempt.team_id == team_id, Attempt.round_id == round_id)
            )
        )
        attempts = list(attempts_result.scalars().all())

        # Calculate stats
        correct = sum(1 for a in attempts if a.is_correct)
        wrong = sum(1 for a in attempts if not a.is_correct)
        total = len(attempts)
        total_tiles = board.size * board.size

        # Detect bingos
        # Refresh tiles
        tiles_result = await db.execute(
            select(BoardTile).where(BoardTile.board_id == board.id)
        )
        tiles = list(tiles_result.scalars().all())
        bingo_lines = GameEngine.detect_bingos(tiles, board.size)

        # Mark bingo tiles
        bingo_positions = set()
        for line in bingo_lines:
            for pos in line:
                bingo_positions.add(pos)
        for tile in tiles:
            if tile.position in bingo_positions and tile.status == TileStatus.CORRECT:
                tile.status = TileStatus.BINGO

        # Calculate total score
        base_score = sum(a.points_earned for a in attempts)

        # Check for perfect round
        perfect_bonus = 0
        if correct == total_tiles and wrong == 0:
            perfect_bonus = GameEngine.PERFECT_ROUND_BONUS

        score.total_score = base_score + perfect_bonus
        score.correct_answers = correct
        score.wrong_answers = wrong
        score.bingo_count = len(bingo_lines)
        score.accuracy = (correct / total * 100) if total > 0 else 0.0
        score.avg_response_time = (
            sum(a.time_taken_seconds for a in attempts) / total if total > 0 else 0.0
        )
        score.completion_percentage = (total / total_tiles * 100) if total_tiles > 0 else 0.0
        score.perfect_round_bonus = perfect_bonus

        if correct == total_tiles:
            score.completion_time = datetime.utcnow()

        await db.flush()
        return score

    @staticmethod
    async def update_leaderboard(
        db: AsyncSession,
        round_id: UUID,
    ) -> List[LeaderboardEntry]:
        """Recalculate and update the leaderboard for a round."""
        from app.models.team import Team

        # Get all scores for this round
        scores_result = await db.execute(
            select(Score, Team).join(Team, Score.team_id == Team.id).where(
                Score.round_id == round_id
            ).order_by(
                Score.bingo_count.desc(),
                Score.total_score.desc(),
                Score.completion_time.asc(),
                Score.wrong_answers.asc(),
                Score.avg_response_time.asc(),
            )
        )
        scores_with_teams = scores_result.all()

        # Get round info
        round_result = await db.execute(select(Round).where(Round.id == round_id))
        round_obj = round_result.scalar_one()

        # Delete existing leaderboard entries
        existing = await db.execute(
            select(LeaderboardEntry).where(LeaderboardEntry.round_id == round_id)
        )
        for entry in existing.scalars().all():
            await db.delete(entry)

        # Create new entries
        entries = []
        for rank, (score, team) in enumerate(scores_with_teams, 1):
            entry = LeaderboardEntry(
                id=uuid4(),
                round_id=round_id,
                team_id=team.id,
                rank=rank,
                team_name=team.team_name,
                score=score.total_score,
                bingo_count=score.bingo_count,
                correct_answers=score.correct_answers,
                total_questions=round_obj.num_questions,
                accuracy=score.accuracy,
                completion_percentage=score.completion_percentage,
                avg_time=score.avg_response_time,
            )
            db.add(entry)
            entries.append(entry)

        await db.flush()
        return entries


# Singleton game engine
game_engine = GameEngine()
