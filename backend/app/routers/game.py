from uuid import UUID
"""
Game router.
Handles board retrieval, answer submission, leaderboard, and game state.
"""

from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.database import get_db, async_session_maker
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.board import Board, BoardTile, TileStatus
from app.models.round import Round, RoundStatus, RoundParticipant
from app.models.question import Question
from app.models.attempt import Attempt
from app.models.score import Score
from app.models.leaderboard import LeaderboardEntry
from app.models.qualification import Qualification
from app.models.tournament import Tournament
from app.schemas.game import (
    BoardResponse, BoardTileResponse, SubmitAnswerRequest, SubmitAnswerResponse,
    LeaderboardResponse, LeaderboardEntryResponse, QualificationResponse,
    AdminDashboardStats, TeamDashboardStats,
)
from app.utils.auth import get_current_user, get_current_admin
from app.services.game_engine import game_engine
from app.websocket.manager import manager

router = APIRouter(prefix="/api/game", tags=["Game"])


@router.get("/board/{round_id}", response_model=BoardResponse)
async def get_board(
    round_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the team's board for a round."""
    # Get team
    team_result = await db.execute(select(Team).where(Team.user_id == current_user.id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get board
    board_result = await db.execute(
        select(Board).options(selectinload(Board.tiles))
        .where(and_(Board.round_id == round_id, Board.team_id == team.id))
    )
    board = board_result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found. Round may not have started yet.")

    # Get bingo lines
    bingo_lines = game_engine.detect_bingos(board.tiles, board.size)

    tiles = []
    for i, tile in enumerate(sorted(board.tiles, key=lambda t: t.position)):
        # Get question difficulty
        q_result = await db.execute(select(Question.difficulty).where(Question.id == tile.question_id))
        diff = q_result.scalar()
        tiles.append(BoardTileResponse(
            id=str(tile.id), position=tile.position,
            row=tile.row, col=tile.col,
            status=tile.status.value,
            question_number=i + 1,
            difficulty=diff.value if hasattr(diff, 'value') else str(diff) if diff else "easy",
            answered_at=tile.answered_at,
            is_bingo_part=tile.is_bingo_part,
        ))

    return BoardResponse(
        id=str(board.id), round_id=str(board.round_id),
        team_id=str(board.team_id), size=board.size,
        tiles=tiles, bingo_lines=bingo_lines,
    )


@router.get("/tile/{tile_id}/question")
async def get_tile_question(
    tile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the question for a specific tile (without revealing the answer)."""
    tile_result = await db.execute(select(BoardTile).where(BoardTile.id == tile_id))
    tile = tile_result.scalar_one_or_none()
    if not tile:
        raise HTTPException(status_code=404, detail="Tile not found")

    if tile.status != TileStatus.UNANSWERED:
        raise HTTPException(status_code=400, detail="This question has already been answered")

    # Get question
    q_result = await db.execute(
        select(Question).options(selectinload(Question.options))
        .where(Question.id == tile.question_id)
    )
    q = q_result.scalar_one()

    return {
        "id": str(q.id),
        "question_text": q.question_text,
        "code_snippet": q.code_snippet,
        "question_type": q.question_type.value,
        "language": q.language.value,
        "difficulty": q.difficulty.value,
        "time_limit": q.time_limit,
        "options": [
            {"option_label": o.option_label, "option_text": o.option_text}
            for o in sorted(q.options, key=lambda x: x.order)
        ],
    }


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    data: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an answer for a tile."""
    # Get team
    team_result = await db.execute(select(Team).where(Team.user_id == current_user.id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get tile
    tile_result = await db.execute(
        select(BoardTile).options(selectinload(BoardTile.board))
        .where(BoardTile.id == data.tile_id)
    )
    tile = tile_result.scalar_one_or_none()
    if not tile:
        raise HTTPException(status_code=404, detail="Tile not found")

    if tile.status != TileStatus.UNANSWERED:
        raise HTTPException(status_code=400, detail="This question has already been answered")

    # Check round is active
    round_result = await db.execute(select(Round).where(Round.id == tile.board.round_id))
    round_obj = round_result.scalar_one()
    if round_obj.status != RoundStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Round is not active")

    # Submit answer
    is_correct, points, correct_answer, explanation = await game_engine.submit_answer(
        db, tile, team.id, round_obj.id, data.answer, data.time_taken_seconds,
    )

    # Get board for score update
    board_result = await db.execute(
        select(Board).options(selectinload(Board.tiles))
        .where(Board.id == tile.board_id)
    )
    board = board_result.scalar_one()

    # Update score
    score = await game_engine.update_score(db, team.id, round_obj.id, board)

    # Update leaderboard
    entries = await game_engine.update_leaderboard(db, round_obj.id)

    # Get bingo lines
    tiles_result = await db.execute(
        select(BoardTile).where(BoardTile.board_id == board.id)
    )
    all_tiles = list(tiles_result.scalars().all())
    bingo_lines = game_engine.detect_bingos(all_tiles, board.size)

    await db.flush()

    # Broadcast leaderboard update
    lb_data = [
        {
            "rank": e.rank, "team_id": str(e.team_id), "team_name": e.team_name,
            "score": e.score, "bingo_count": e.bingo_count,
            "correct_answers": e.correct_answers, "accuracy": e.accuracy,
            "completion_percentage": e.completion_percentage, "avg_time": e.avg_time,
        }
        for e in entries
    ]
    await manager.broadcast_leaderboard(str(round_obj.id), lb_data)

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        explanation=explanation,
        points_earned=points,
        new_score=score.total_score,
        new_bingo_count=score.bingo_count,
        bingo_lines=bingo_lines,
        tile_status="correct" if is_correct else "wrong",
    )


@router.get("/leaderboard/{round_id}", response_model=LeaderboardResponse)
async def get_leaderboard(
    round_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the leaderboard for a round."""
    round_result = await db.execute(select(Round).where(Round.id == round_id))
    round_obj = round_result.scalar_one_or_none()
    if not round_obj:
        raise HTTPException(status_code=404, detail="Round not found")

    entries_result = await db.execute(
        select(LeaderboardEntry).where(LeaderboardEntry.round_id == round_id)
        .order_by(LeaderboardEntry.rank)
    )
    entries = entries_result.scalars().all()

    return LeaderboardResponse(
        round_id=str(round_obj.id),
        round_name=round_obj.name,
        entries=[
            LeaderboardEntryResponse(
                rank=e.rank, team_id=str(e.team_id), team_name=e.team_name,
                score=e.score, bingo_count=e.bingo_count,
                correct_answers=e.correct_answers, total_questions=e.total_questions,
                accuracy=e.accuracy, completion_percentage=e.completion_percentage,
                avg_time=e.avg_time,
            )
            for e in entries
        ],
    )


@router.get("/qualifications/{round_id}", response_model=list[QualificationResponse])
async def get_qualifications(
    round_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get qualification results for a round."""
    result = await db.execute(
        select(Qualification, Team)
        .join(Team, Qualification.team_id == Team.id)
        .where(Qualification.round_id == round_id)
        .order_by(Qualification.final_rank)
    )
    qualifications = result.all()

    return [
        QualificationResponse(
            team_id=str(q.team_id), team_name=t.team_name,
            tournament_id=str(q.tournament_id), round_id=str(q.round_id),
            status=q.status.value, final_rank=q.final_rank,
            final_score=q.final_score,
        )
        for q, t in qualifications
    ]


@router.get("/admin/dashboard", response_model=AdminDashboardStats)
async def admin_dashboard(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get admin dashboard statistics."""
    from sqlalchemy import func as sqlfunc

    total_tournaments = (await db.execute(select(sqlfunc.count(Tournament.id)))).scalar() or 0
    active_tournaments = (await db.execute(
        select(sqlfunc.count(Tournament.id)).where(Tournament.status == "active")
    )).scalar() or 0
    total_teams = (await db.execute(select(sqlfunc.count(Team.id)))).scalar() or 0
    total_questions = (await db.execute(select(sqlfunc.count(Question.id)))).scalar() or 0
    total_rounds = (await db.execute(select(sqlfunc.count(Round.id)))).scalar() or 0
    active_rounds = (await db.execute(
        select(sqlfunc.count(Round.id)).where(Round.status == "active")
    )).scalar() or 0
    online_teams = (await db.execute(
        select(sqlfunc.count(User.id)).where(and_(User.role == "team", User.is_online == True))
    )).scalar() or 0

    return AdminDashboardStats(
        total_tournaments=total_tournaments,
        active_tournaments=active_tournaments,
        total_teams=total_teams,
        total_questions=total_questions,
        total_rounds=total_rounds,
        active_rounds=active_rounds,
        online_teams=online_teams,
    )


@router.get("/team/dashboard", response_model=TeamDashboardStats)
async def team_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get team dashboard data."""
    team_result = await db.execute(select(Team).where(Team.user_id == current_user.id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Room-joined teams always follow the tournament they joined. Legacy teams
    # keep the previous behavior of following the newest active tournament.
    if team.tournament_id:
        t_result = await db.execute(
            select(Tournament).where(Tournament.id == team.tournament_id)
        )
    else:
        t_result = await db.execute(
            select(Tournament)
            .where(Tournament.status == "active")
            .order_by(Tournament.created_at.desc())
            .limit(1)
        )
    tournament = t_result.scalar_one_or_none()

    # Find active round
    current_round = None
    current_score = 0
    current_rank = 0
    bingo_count = 0
    qual_status = "pending"
    remaining = 0

    if tournament and tournament.status.value == "active":
        r_result = await db.execute(
            select(Round).where(
                and_(Round.tournament_id == tournament.id, Round.status == "active")
            ).order_by(Round.order.desc()).limit(1)
        )
        round_obj = r_result.scalar_one_or_none()
        if round_obj:
            # Room teams that joined before a round started are enrolled here
            # as a compatibility fallback, so they never need admin-created
            # credentials or a manual "add teams" step.
            if team.tournament_id:
                participant_result = await db.execute(
                    select(RoundParticipant.id).where(
                        RoundParticipant.round_id == round_obj.id,
                        RoundParticipant.team_id == team.id,
                    )
                )
                if participant_result.scalar_one_or_none() is None:
                    db.add(RoundParticipant(
                        id=uuid4(), round_id=round_obj.id, team_id=team.id,
                    ))
                    await db.flush()
                    await game_engine.generate_board(
                        db, round_obj.id, team.id, round_obj.board_size,
                        round_obj.difficulty.value if hasattr(round_obj.difficulty, "value") else str(round_obj.difficulty),
                        round_obj.num_questions,
                    )
                    await db.flush()

            current_round = round_obj.name

            # Get score
            score_result = await db.execute(
                select(Score).where(
                    and_(Score.team_id == team.id, Score.round_id == round_obj.id)
                )
            )
            score = score_result.scalar_one_or_none()
            if score:
                current_score = score.total_score
                bingo_count = score.bingo_count

            # Get rank
            lb_result = await db.execute(
                select(LeaderboardEntry).where(
                    and_(LeaderboardEntry.round_id == round_obj.id, LeaderboardEntry.team_id == team.id)
                )
            )
            lb = lb_result.scalar_one_or_none()
            if lb:
                current_rank = lb.rank

            # Calculate remaining time
            if round_obj.actual_start:
                elapsed = (datetime.utcnow() - round_obj.actual_start).total_seconds()
                remaining = max(0, round_obj.timer_seconds - int(elapsed))

    return TeamDashboardStats(
        team_name=team.team_name,
        current_tournament_id=str(tournament.id) if tournament else None,
        current_tournament=tournament.name if tournament else None,
        current_tournament_status=tournament.status.value if tournament else None,
        current_round=current_round,
        current_score=current_score,
        current_rank=current_rank,
        bingo_count=bingo_count,
        qualification_status=qual_status,
        remaining_time=remaining,
    )


# ========== WebSocket endpoint ==========

@router.websocket("/ws/{round_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    round_id: UUID,
):
    """WebSocket endpoint for real-time game updates."""
    # Accept connection
    user_id = websocket.query_params.get("user_id", "")
    await manager.connect(websocket, f"round_{round_id}", user_id)

    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            elif msg_type == "request_leaderboard":
                # Send current leaderboard
                async with async_session_maker() as db:
                    entries_result = await db.execute(
                        select(LeaderboardEntry)
                        .where(LeaderboardEntry.round_id == round_id)
                        .order_by(LeaderboardEntry.rank)
                    )
                    entries = entries_result.scalars().all()
                    lb_data = [
                        {
                            "rank": e.rank, "team_id": str(e.team_id),
                            "team_name": e.team_name, "score": e.score,
                            "bingo_count": e.bingo_count,
                            "correct_answers": e.correct_answers,
                            "accuracy": e.accuracy,
                            "completion_percentage": e.completion_percentage,
                            "avg_time": e.avg_time,
                        }
                        for e in entries
                    ]
                    await manager.send_personal_message(
                        {"type": "leaderboard_update", "data": lb_data},
                        websocket,
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket, f"round_{round_id}", user_id)
    except Exception:
        manager.disconnect(websocket, f"round_{round_id}", user_id)
