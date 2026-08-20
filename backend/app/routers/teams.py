"""
Teams management router.
Handles team CRUD, bulk credential generation, and CSV import.
"""

import csv
import secrets
import string
import io
from uuid import UUID, uuid4
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User, UserRole
from app.models.team import Team, TeamMember
from app.utils.auth import get_current_admin, get_current_user, get_password_hash

router = APIRouter(prefix="/api/teams", tags=["Teams"])


def generate_password(length: int = 8) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.get("/")
async def list_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all registered teams."""
    result = await db.execute(
        select(Team).options(
            selectinload(Team.members),
            selectinload(Team.user)
        ).order_by(Team.team_name)
    )
    teams = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "team_name": t.team_name,
            "college_name": t.college_name,
            "username": t.user.username if t.user else "",
            "members": [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "email": m.email,
                    "role_in_team": m.role_in_team,
                }
                for m in t.members
            ],
        }
        for t in teams
    ]


@router.post("/")
async def create_team(
    data: dict,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new team with login credentials."""
    # Check username uniqueness
    existing = await db.execute(select(User).where(User.username == data["username"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")

    # Create user account
    user = User(
        id=uuid4(),
        username=data["username"],
        hashed_password=get_password_hash(data["password"]),
        role=UserRole.TEAM,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create team
    team = Team(
        id=uuid4(),
        user_id=user.id,
        team_name=data["team_name"],
        college_name=data.get("college_name"),
    )
    db.add(team)
    await db.flush()

    return {
        "id": str(team.id),
        "team_name": team.team_name,
        "username": user.username,
        "message": "Team created successfully",
    }


@router.delete("/{team_id}")
async def delete_team(
    team_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a team and its associated user account."""

    team_result = await db.execute(select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Delete user too
    user_result = await db.execute(select(User).where(User.id == team.user_id))
    user = user_result.scalar_one_or_none()

    await db.delete(team)
    if user:
        await db.delete(user)
    await db.flush()

    return {"message": "Team deleted successfully"}


@router.post("/generate-credentials")
async def generate_credentials(
    count: int = Query(default=10, ge=1, le=200),
    prefix: str = Query(default="team"),
    college: Optional[str] = Query(default=None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Bulk generate team credentials with auto-numbered usernames."""
    # Find current highest team number for this prefix
    result = await db.execute(
        select(User).where(User.username.like(f"{prefix}%"))
    )
    existing_users = result.scalars().all()
    
    # Determine next starting number
    start_num = 1
    for u in existing_users:
        suffix = u.username.replace(prefix + "_", "").replace(prefix, "")
        if suffix.isdigit():
            start_num = max(start_num, int(suffix) + 1)

    credentials = []
    for i in range(count):
        num = start_num + i
        username = f"{prefix}_{num:02d}"
        password = generate_password(8)
        team_name = f"{prefix.replace('_', ' ').title()} {num:02d}"

        # Create user
        user = User(
            id=uuid4(),
            username=username,
            hashed_password=get_password_hash(password),
            role=UserRole.TEAM,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        # Create team
        team = Team(
            id=uuid4(),
            user_id=user.id,
            team_name=team_name,
            college_name=college,
        )
        db.add(team)
        await db.flush()

        credentials.append({
            "team_name": team_name,
            "username": username,
            "password": password,
        })

    return credentials


@router.post("/import-csv")
async def import_teams_csv(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Import teams from CSV file.
    Expected CSV columns: team_name, college_name (optional), username, password
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))

    # Validate headers
    required = {"team_name", "username", "password"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {', '.join(required)}. Got: {reader.fieldnames}"
        )

    created = []
    errors = []

    for row_num, row in enumerate(reader, start=2):
        username = row.get("username", "").strip()
        password = row.get("password", "").strip()
        team_name = row.get("team_name", "").strip()
        college = row.get("college_name", "").strip() or None

        if not username or not password or not team_name:
            errors.append(f"Row {row_num}: Missing required fields")
            continue

        # Check for duplicate username
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            errors.append(f"Row {row_num}: Username '{username}' already exists, skipped")
            continue

        try:
            user = User(
                id=uuid4(),
                username=username,
                hashed_password=get_password_hash(password),
                role=UserRole.TEAM,
                is_active=True,
            )
            db.add(user)
            await db.flush()

            team = Team(
                id=uuid4(),
                user_id=user.id,
                team_name=team_name,
                college_name=college,
            )
            db.add(team)
            await db.flush()

            created.append({
                "team_name": team_name,
                "username": username,
                "password": password,
            })
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    return created
