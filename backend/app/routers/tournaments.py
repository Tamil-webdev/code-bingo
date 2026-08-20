"""
Tournament management router.
Handles tournament and round CRUD, status management.
"""

from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.tournament import Tournament, TournamentStatus
from app.models.round import Round, RoundStatus, RoundParticipant
from app.models.team import Team
from app.models.score import Score
from app.models.qualification import Qualification, QualificationStatus
from app.schemas.tournament import (
    TournamentCreate, TournamentUpdate, TournamentResponse,
    TournamentListResponse, RoundCreate, RoundUpdate, RoundResponse,
)
from app.utils.auth import get_current_admin, get_current_user
from app.websocket.manager import manager

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])


@router.get("/", response_model=list[TournamentListResponse])
async def list_tournaments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tournaments."""
    result = await db.execute(
        select(Tournament).order_by(Tournament.created_at.desc())
    )
    tournaments = result.scalars().all()
    return [
        TournamentListResponse(
            id=str(t.id), name=t.name, description=t.description,
            status=t.status.value, max_teams=t.max_teams,
            num_rounds=t.num_rounds, created_at=t.created_at,
        )
        for t in tournaments
    ]


@router.get("/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(
    tournament_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tournament details with rounds."""

    result = await db.execute(
        select(Tournament).options(selectinload(Tournament.rounds))
        .where(Tournament.id == tournament_id)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")

    rounds = []
    for r in t.rounds:
        p_count = await db.execute(
            select(func.count(RoundParticipant.id)).where(RoundParticipant.round_id == r.id)
        )
        rounds.append(RoundResponse(
            id=str(r.id), tournament_id=str(r.tournament_id),
            name=r.name, order=r.order, board_size=r.board_size,
            timer_seconds=r.timer_seconds, difficulty=r.difficulty.value,
            num_questions=r.num_questions, qualification_count=r.qualification_count,
            status=r.status.value, start_time=r.start_time, end_time=r.end_time,
            actual_start=r.actual_start, actual_end=r.actual_end,
            participant_count=p_count.scalar() or 0,
        ))

    return TournamentResponse(
        id=str(t.id), name=t.name, description=t.description,
        status=t.status.value, registration_start=t.registration_start,
        registration_end=t.registration_end, max_teams=t.max_teams,
        num_rounds=t.num_rounds, rounds=rounds, created_at=t.created_at,
    )


@router.get("/{tournament_id}/rounds", response_model=list[RoundResponse])
async def list_rounds(
    tournament_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all rounds for a tournament."""

    tournament = await db.execute(select(Tournament.id).where(Tournament.id == tournament_id))
    if tournament.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Tournament not found")

    result = await db.execute(
        select(Round).where(Round.tournament_id == tournament_id).order_by(Round.order)
    )
    rounds = result.scalars().all()
    response = []
    for r in rounds:
        participant_count = await db.execute(
            select(func.count(RoundParticipant.id)).where(RoundParticipant.round_id == r.id)
        )
        response.append(RoundResponse(
            id=str(r.id), tournament_id=str(r.tournament_id),
            name=r.name, order=r.order, board_size=r.board_size,
            timer_seconds=r.timer_seconds, difficulty=r.difficulty.value,
            num_questions=r.num_questions, qualification_count=r.qualification_count,
            status=r.status.value, start_time=r.start_time, end_time=r.end_time,
            actual_start=r.actual_start, actual_end=r.actual_end,
            participant_count=participant_count.scalar() or 0,
        ))
    return response


@router.get("/rounds/{round_id}", response_model=RoundResponse)
async def get_round(
    round_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get one round's configuration and current status."""
    result = await db.execute(select(Round).where(Round.id == round_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Round not found")

    participant_count = await db.execute(
        select(func.count(RoundParticipant.id)).where(RoundParticipant.round_id == r.id)
    )
    return RoundResponse(
        id=str(r.id), tournament_id=str(r.tournament_id),
        name=r.name, order=r.order, board_size=r.board_size,
        timer_seconds=r.timer_seconds,
        difficulty=r.difficulty.value if hasattr(r.difficulty, "value") else str(r.difficulty),
        num_questions=r.num_questions, qualification_count=r.qualification_count,
        status=r.status.value, start_time=r.start_time, end_time=r.end_time,
        actual_start=r.actual_start, actual_end=r.actual_end,
        participant_count=participant_count.scalar() or 0,
    )


@router.post("/", response_model=TournamentResponse)
async def create_tournament(
    data: TournamentCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tournament with rounds."""
    tournament = Tournament(
        id=uuid4(), name=data.name, description=data.description,
        registration_start=data.registration_start,
        registration_end=data.registration_end,
        max_teams=data.max_teams, num_rounds=data.num_rounds,
        created_by=admin.id, status=TournamentStatus.DRAFT,
    )
    db.add(tournament)
    await db.flush()

    rounds = []
    for i, rd in enumerate(data.rounds or []):
        r = Round(
            id=uuid4(), tournament_id=tournament.id,
            name=rd.name, order=rd.order if rd.order else i,
            board_size=rd.board_size, timer_seconds=rd.timer_seconds,
            difficulty=rd.difficulty, num_questions=rd.num_questions,
            qualification_count=rd.qualification_count,
            start_time=rd.start_time, end_time=rd.end_time,
        )
        db.add(r)
        rounds.append(RoundResponse(
            id=str(r.id), tournament_id=str(tournament.id),
            name=r.name, order=r.order, board_size=r.board_size,
            timer_seconds=r.timer_seconds, difficulty=r.difficulty.value if hasattr(r.difficulty, 'value') else str(r.difficulty),
            num_questions=r.num_questions, qualification_count=r.qualification_count,
            status=r.status.value, participant_count=0,
        ))

    await db.flush()

    return TournamentResponse(
        id=str(tournament.id), name=tournament.name,
        description=tournament.description, status=tournament.status.value,
        registration_start=tournament.registration_start,
        registration_end=tournament.registration_end,
        max_teams=tournament.max_teams, num_rounds=tournament.num_rounds,
        rounds=rounds, created_at=tournament.created_at,
    )


@router.put("/{tournament_id}", response_model=TournamentListResponse)
async def update_tournament(
    tournament_id: UUID, data: TournamentUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update tournament details."""
    result = await db.execute(select(Tournament).where(Tournament.id == tournament_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "status" and value:
            setattr(t, field, TournamentStatus(value))
        elif value is not None:
            setattr(t, field, value)

    await db.flush()
    return TournamentListResponse(
        id=str(t.id), name=t.name, description=t.description,
        status=t.status.value, max_teams=t.max_teams,
        num_rounds=t.num_rounds, created_at=t.created_at,
    )


@router.delete("/{tournament_id}")
async def delete_tournament(
    tournament_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a tournament."""
    result = await db.execute(select(Tournament).where(Tournament.id == tournament_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    await db.delete(t)
    await db.flush()
    return {"message": "Tournament deleted"}


@router.post("/{tournament_id}/start")
async def start_tournament(
    tournament_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Start a tournament."""
    result = await db.execute(select(Tournament).where(Tournament.id == tournament_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    t.status = TournamentStatus.ACTIVE
    await db.flush()
    return {"message": "Tournament started", "status": "active"}


@router.post("/{tournament_id}/pause")
async def pause_tournament(
    tournament_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pause a tournament."""
    result = await db.execute(select(Tournament).where(Tournament.id == tournament_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    t.status = TournamentStatus.PAUSED
    await db.flush()
    return {"message": "Tournament paused"}


@router.post("/{tournament_id}/end")
async def end_tournament(
    tournament_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """End a tournament."""
    result = await db.execute(select(Tournament).where(Tournament.id == tournament_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    t.status = TournamentStatus.COMPLETED
    await db.flush()
    return {"message": "Tournament ended"}


# ========== Round management ==========

@router.post("/{tournament_id}/rounds", response_model=RoundResponse)
async def create_round(
    tournament_id: UUID, data: RoundCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a new round to a tournament."""

    result = await db.execute(select(Tournament).where(Tournament.id == tournament_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Get max order
    max_order = await db.execute(
        select(func.max(Round.order)).where(Round.tournament_id == tournament_id)
    )
    current_max = max_order.scalar() or -1

    r = Round(
        id=uuid4(), tournament_id=t.id,
        name=data.name, order=current_max + 1,
        board_size=data.board_size, timer_seconds=data.timer_seconds,
        difficulty=data.difficulty, num_questions=data.num_questions,
        qualification_count=data.qualification_count,
        start_time=data.start_time, end_time=data.end_time,
    )
    db.add(r)
    t.num_rounds = current_max + 2
    await db.flush()

    return RoundResponse(
        id=str(r.id), tournament_id=str(r.tournament_id),
        name=r.name, order=r.order, board_size=r.board_size,
        timer_seconds=r.timer_seconds,
        difficulty=r.difficulty.value if hasattr(r.difficulty, 'value') else str(r.difficulty),
        num_questions=r.num_questions, qualification_count=r.qualification_count,
        status=r.status.value, participant_count=0,
    )


@router.put("/rounds/{round_id}", response_model=RoundResponse)
async def update_round(
    round_id: UUID, data: RoundUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update round settings."""
    result = await db.execute(select(Round).where(Round.id == round_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Round not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(r, field, value)
    await db.flush()

    p_count = await db.execute(
        select(func.count(RoundParticipant.id)).where(RoundParticipant.round_id == r.id)
    )
    return RoundResponse(
        id=str(r.id), tournament_id=str(r.tournament_id),
        name=r.name, order=r.order, board_size=r.board_size,
        timer_seconds=r.timer_seconds,
        difficulty=r.difficulty.value if hasattr(r.difficulty, 'value') else str(r.difficulty),
        num_questions=r.num_questions, qualification_count=r.qualification_count,
        status=r.status.value, start_time=r.start_time, end_time=r.end_time,
        actual_start=r.actual_start, actual_end=r.actual_end,
        participant_count=p_count.scalar() or 0,
    )


@router.post("/rounds/{round_id}/start")
async def start_round(
    round_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Start a round - generates boards for all participants."""
    from app.services.game_engine import game_engine

    result = await db.execute(select(Round).where(Round.id == round_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Round not found")

    r.status = RoundStatus.ACTIVE
    r.actual_start = datetime.utcnow()

    # Get participants
    participants = await db.execute(
        select(RoundParticipant).where(RoundParticipant.round_id == r.id)
    )
    parts = participants.scalars().all()

    # Generate boards for each team
    for p in parts:
        await game_engine.generate_board(
            db, r.id, p.team_id, r.board_size,
            r.difficulty.value if hasattr(r.difficulty, 'value') else str(r.difficulty),
            r.num_questions,
        )

    await db.flush()

    # Broadcast round start
    await manager.broadcast_round_event(str(r.id), "start", {
        "round_name": r.name,
        "timer_seconds": r.timer_seconds,
        "board_size": r.board_size,
    })

    return {"message": "Round started", "status": "active"}


@router.post("/rounds/{round_id}/pause")
async def pause_round(
    round_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pause a round."""
    result = await db.execute(select(Round).where(Round.id == round_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Round not found")
    r.status = RoundStatus.PAUSED
    await db.flush()
    await manager.broadcast_round_event(str(r.id), "pause", {})
    return {"message": "Round paused"}


@router.post("/rounds/{round_id}/resume")
async def resume_round(
    round_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused round."""
    result = await db.execute(select(Round).where(Round.id == round_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Round not found")
    r.status = RoundStatus.ACTIVE
    await db.flush()
    await manager.broadcast_round_event(str(r.id), "resume", {})
    return {"message": "Round resumed"}


@router.post("/rounds/{round_id}/end")
async def end_round(
    round_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """End a round."""
    result = await db.execute(select(Round).where(Round.id == round_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Round not found")
    r.status = RoundStatus.COMPLETED
    r.actual_end = datetime.utcnow()
    await db.flush()
    await manager.broadcast_round_event(str(r.id), "end", {})
    return {"message": "Round ended"}


@router.post("/rounds/{round_id}/add-teams")
async def add_teams_to_round(
    round_id: UUID,
    team_ids: list[UUID],
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add teams as participants to a round."""

    result = await db.execute(select(Round).where(Round.id == round_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Round not found")

    added = 0
    for tid in team_ids:
        # UUID parsing is already done by FastAPI since we typed team_ids: list[UUID]

        team_result = await db.execute(select(Team.id).where(Team.id == tid))
        if team_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail=f"Team not found: {tid}")

        # Check if already added
        existing = await db.execute(
            select(RoundParticipant).where(
                RoundParticipant.round_id == r.id,
                RoundParticipant.team_id == tid,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(RoundParticipant(
                id=uuid4(), round_id=r.id, team_id=tid,
            ))
            added += 1

    await db.flush()
    return {"message": f"Added {added} teams to round"}


@router.post("/rounds/{round_id}/advance-qualified")
async def advance_qualified_teams(
    round_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Advance top N teams to the next round based on qualification count."""
    from app.services.game_engine import game_engine

    result = await db.execute(select(Round).where(Round.id == round_id))
    current_round = result.scalar_one_or_none()
    if not current_round:
        raise HTTPException(status_code=404, detail="Round not found")

    # Update leaderboard first
    entries = await game_engine.update_leaderboard(db, current_round.id)

    # Get next round
    next_round_result = await db.execute(
        select(Round).where(
            Round.tournament_id == current_round.tournament_id,
            Round.order == current_round.order + 1,
        )
    )
    next_round = next_round_result.scalar_one_or_none()

    qualified_teams = []
    eliminated_teams = []

    for i, entry in enumerate(entries):
        status = QualificationStatus.QUALIFIED if i < current_round.qualification_count else QualificationStatus.ELIMINATED

        q = Qualification(
            id=uuid4(), tournament_id=current_round.tournament_id,
            round_id=current_round.id, team_id=entry.team_id,
            status=status, final_rank=entry.rank, final_score=entry.score,
            decided_at=datetime.utcnow(),
        )
        db.add(q)

        if status == QualificationStatus.QUALIFIED:
            qualified_teams.append(str(entry.team_id))
            # Add to next round if it exists
            if next_round:
                db.add(RoundParticipant(
                    id=uuid4(), round_id=next_round.id, team_id=entry.team_id,
                ))
        else:
            eliminated_teams.append(str(entry.team_id))

    await db.flush()

    # Notify teams
    for tid in qualified_teams:
        await manager.send_to_user(
            {"type": "notification", "data": {"message": "Congratulations! You've qualified for the next round!", "level": "success"}},
            tid,
        )
    for tid in eliminated_teams:
        await manager.send_to_user(
            {"type": "notification", "data": {"message": "Unfortunately, you've been eliminated. Better luck next time!", "level": "warning"}},
            tid,
        )

    return {
        "message": f"Advanced {len(qualified_teams)} teams",
        "qualified": len(qualified_teams),
        "eliminated": len(eliminated_teams),
    }
