"""
Authentication router.
Handles login for both admin and team users, with duplicate login prevention.
Supports Firebase email/password accounts synced to local users.
"""

import secrets
from datetime import datetime
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, or_
from app.database import get_db
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.tournament import Tournament, TournamentStatus
from app.models.round import Round, RoundParticipant, RoundStatus
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, FirebaseAuthRequest, RegisterRequest, RoomJoinRequest
from app.utils.auth import verify_password, create_access_token, get_current_user, get_password_hash
from app.utils.firebase import verify_firebase_id_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _username_from_email(email: str) -> str:
    local = email.split("@")[0].lower()
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in local)
    return safe[:80] or "player"


async def _issue_token_response(user: User, db: AsyncSession) -> TokenResponse:
    token = create_access_token(data={"sub": user.username, "role": user.role.value})

    user.is_online = True
    user.last_login = datetime.utcnow()
    user.current_session_token = token

    team_id = None
    team_name = None
    if user.role == UserRole.TEAM:
        team_result = await db.execute(select(Team).where(Team.user_id == user.id))
        team = team_result.scalar_one_or_none()
        if team:
            team_id = str(team.id)
            team_name = team.team_name

    await db.flush()

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        username=user.username,
        role=user.role.value,
        team_id=team_id,
        team_name=team_name,
    )


async def _find_user_by_firebase(db: AsyncSession, uid: str, email: Optional[str]) -> Optional[User]:
    conditions = [User.firebase_uid == uid]
    if email:
        conditions.append(User.email == email)
    result = await db.execute(select(User).where(or_(*conditions)))
    return result.scalar_one_or_none()


async def _create_firebase_team_user(
    db: AsyncSession,
    *,
    uid: str,
    email: str,
    team_name: str,
) -> User:
    base_username = _username_from_email(email)
    username = base_username
    suffix = 1
    while True:
        existing = await db.execute(select(User).where(User.username == username))
        if not existing.scalar_one_or_none():
            break
        username = f"{base_username}_{suffix}"
        suffix += 1

    user = User(
        id=uuid4(),
        username=username,
        hashed_password=get_password_hash(secrets.token_urlsafe(32)),
        email=email,
        firebase_uid=uid,
        role=UserRole.TEAM,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    team = Team(
        id=uuid4(),
        user_id=user.id,
        team_name=team_name.strip(),
        college_name=None,
    )
    db.add(team)
    await db.flush()
    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    Prevents duplicate logins for team accounts.
    """
    # Find user
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # For team users, prevent duplicate logins
    if user.role == UserRole.TEAM and user.is_online and user.current_session_token:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This team is already logged in from another device. Please logout first.",
        )

    return await _issue_token_response(user, db)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a team account using the application's local authentication."""
    email = request.email.strip().lower()
    team_name = request.team_name.strip()
    if not email or not team_name or len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Email, team name, and a 6-character password are required")

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    base_username = _username_from_email(email)
    username = base_username
    suffix = 1
    while True:
        existing_username = await db.execute(select(User).where(User.username == username))
        if not existing_username.scalar_one_or_none():
            break
        username = f"{base_username}_{suffix}"
        suffix += 1

    user = User(
        id=uuid4(),
        username=username,
        hashed_password=get_password_hash(request.password),
        email=email,
        role=UserRole.TEAM,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(Team(id=uuid4(), user_id=user.id, team_name=team_name, college_name=None))
    await db.flush()
    return await _issue_token_response(user, db)


@router.post("/join-room", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def join_room(request: RoomJoinRequest, db: AsyncSession = Depends(get_db)):
    """Join a tournament room and receive an immediate team session without credentials."""
    room_code = request.room_code.strip().upper()
    team_name = request.team_name.strip()
    if not room_code or not team_name:
        raise HTTPException(status_code=400, detail="Room ID and team name are required")

    tournament_result = await db.execute(
        select(Tournament).where(Tournament.room_code == room_code)
    )
    tournament = tournament_result.scalar_one_or_none()
    if not tournament or tournament.status in {TournamentStatus.COMPLETED, TournamentStatus.CANCELLED}:
        raise HTTPException(status_code=404, detail="Room not found or no longer accepting teams")

    team_count = await db.execute(
        select(func.count(Team.id)).where(Team.tournament_id == tournament.id)
    )
    if team_count.scalar() >= tournament.max_teams:
        raise HTTPException(status_code=409, detail="This room is full")

    existing_team = await db.execute(
        select(Team.id).where(
            Team.tournament_id == tournament.id,
            func.lower(Team.team_name) == team_name.lower(),
        )
    )
    if existing_team.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="That team name has already joined this room")

    username = f"room_{tournament.id.hex[:8]}_{uuid4().hex[:8]}"
    user = User(
        id=uuid4(), username=username,
        hashed_password=get_password_hash(secrets.token_urlsafe(32)),
        role=UserRole.TEAM, is_active=True,
    )
    db.add(user)
    await db.flush()
    team = Team(
        id=uuid4(), user_id=user.id, tournament_id=tournament.id,
        team_name=team_name, college_name=None,
    )
    db.add(team)
    await db.flush()

    # Automatically register a room-joined team for the live round, or for
    # the first upcoming round when the contest has not started yet.
    round_result = await db.execute(
        select(Round)
        .where(
            Round.tournament_id == tournament.id,
            Round.status == RoundStatus.ACTIVE,
        )
        .order_by(Round.order.desc())
        .limit(1)
    )
    round_obj = round_result.scalar_one_or_none()
    if not round_obj:
        round_result = await db.execute(
            select(Round)
            .where(
                Round.tournament_id == tournament.id,
                Round.status == RoundStatus.PENDING,
            )
            .order_by(Round.order)
            .limit(1)
        )
        round_obj = round_result.scalar_one_or_none()
    if round_obj:
        db.add(RoundParticipant(id=uuid4(), round_id=round_obj.id, team_id=team.id))
        await db.flush()
        if round_obj.status == RoundStatus.ACTIVE:
            from app.services.game_engine import game_engine
            await game_engine.generate_board(
                db, round_obj.id, team.id, round_obj.board_size,
                round_obj.difficulty.value if hasattr(round_obj.difficulty, "value") else str(round_obj.difficulty),
                round_obj.num_questions,
            )
            await db.flush()

    return await _issue_token_response(user, db)


@router.post("/firebase", response_model=TokenResponse)
async def firebase_auth(request: FirebaseAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify Firebase ID token and sync with a local user account.
    Creates a new team account when team_name is provided for first-time sign-up.
    """
    account = await verify_firebase_id_token(request.id_token)
    uid = account["uid"]
    email = account.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firebase account must have an email address",
        )

    user = await _find_user_by_firebase(db, uid, email)

    if not user:
        team_name = (request.team_name or account.get("display_name") or "").strip()
        if not team_name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tournament account found. Please create an account first.",
            )
        user = await _create_firebase_team_user(
            db, uid=uid, email=email, team_name=team_name
        )
    elif not user.firebase_uid:
        user.firebase_uid = uid
        if not user.email:
            user.email = email

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    if user.role == UserRole.TEAM and user.is_online and user.current_session_token:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This team is already logged in from another device. Please logout first.",
        )

    return await _issue_token_response(user, db)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout current user and clear session."""
    current_user.is_online = False
    current_user.current_session_token = None
    await db.flush()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )


@router.post("/force-logout/{username}")
async def force_logout(
    username: str,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin force logout a team (in case of stuck sessions)."""
    if admin.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_online = False
    user.current_session_token = None
    await db.flush()
    return {"message": f"Force logged out {username}"}
