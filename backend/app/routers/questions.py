from uuid import UUID
"""
Question bank router.
Handles question CRUD, filtering, and CSV bulk upload.
"""

import csv
import io
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.question import Question, QuestionOption
from app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionFilter,
)
from app.utils.auth import get_current_admin, get_current_user

router = APIRouter(prefix="/api/questions", tags=["Questions"])


@router.get("/", response_model=dict)
async def list_questions(
    language: str = Query(None),
    difficulty: str = Query(None),
    question_type: str = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List questions with filtering and pagination."""
    query = select(Question).options(selectinload(Question.options))

    if language:
        query = query.where(Question.language == language)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if question_type:
        query = query.where(Question.question_type == question_type)
    if search:
        query = query.where(
            or_(
                Question.question_text.ilike(f"%{search}%"),
                Question.code_snippet.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.order_by(Question.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    questions = result.scalars().all()

    return {
        "items": [
            QuestionResponse(
                id=str(q.id), question_text=q.question_text,
                code_snippet=q.code_snippet, question_type=q.question_type.value,
                language=q.language.value, difficulty=q.difficulty.value,
                correct_answer=q.correct_answer, explanation=q.explanation,
                tags=q.tags or [], time_limit=q.time_limit,
                is_active=q.is_active,
                options=[
                    {"id": str(o.id), "option_text": o.option_text,
                     "option_label": o.option_label, "is_correct": o.is_correct, "order": o.order}
                    for o in q.options
                ],
                created_at=q.created_at,
            )
            for q in questions
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total else 0,
    }


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single question by ID."""
    result = await db.execute(
        select(Question).options(selectinload(Question.options))
        .where(Question.id == question_id)
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    return QuestionResponse(
        id=str(q.id), question_text=q.question_text,
        code_snippet=q.code_snippet, question_type=q.question_type.value,
        language=q.language.value, difficulty=q.difficulty.value,
        correct_answer=q.correct_answer, explanation=q.explanation,
        tags=q.tags or [], time_limit=q.time_limit, is_active=q.is_active,
        options=[
            {"id": str(o.id), "option_text": o.option_text,
             "option_label": o.option_label, "is_correct": o.is_correct, "order": o.order}
            for o in q.options
        ],
        created_at=q.created_at,
    )


@router.post("/", response_model=QuestionResponse)
async def create_question(
    data: QuestionCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new question."""
    q = Question(
        id=uuid4(), question_text=data.question_text,
        code_snippet=data.code_snippet, question_type=data.question_type,
        language=data.language, difficulty=data.difficulty,
        correct_answer=data.correct_answer, explanation=data.explanation,
        tags=data.tags or [], time_limit=data.time_limit,
    )
    db.add(q)
    await db.flush()

    options = []
    for o in data.options:
        opt = QuestionOption(
            id=uuid4(), question_id=q.id,
            option_text=o.option_text, option_label=o.option_label,
            is_correct=o.is_correct, order=o.order,
        )
        db.add(opt)
        options.append(opt)

    await db.flush()

    return QuestionResponse(
        id=str(q.id), question_text=q.question_text,
        code_snippet=q.code_snippet, question_type=q.question_type.value if hasattr(q.question_type, 'value') else q.question_type,
        language=q.language.value if hasattr(q.language, 'value') else q.language,
        difficulty=q.difficulty.value if hasattr(q.difficulty, 'value') else q.difficulty,
        correct_answer=q.correct_answer, explanation=q.explanation,
        tags=q.tags or [], time_limit=q.time_limit, is_active=q.is_active,
        options=[
            {"id": str(o.id), "option_text": o.option_text,
             "option_label": o.option_label, "is_correct": o.is_correct, "order": o.order}
            for o in options
        ],
        created_at=q.created_at,
    )


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: UUID, data: QuestionUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a question."""
    result = await db.execute(
        select(Question).options(selectinload(Question.options))
        .where(Question.id == question_id)
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "options":
            continue
        if value is not None:
            setattr(q, field, value)

    # Update options if provided
    if data.options is not None:
        for o in q.options:
            await db.delete(o)
        for o in data.options:
            opt = QuestionOption(
                id=uuid4(), question_id=q.id,
                option_text=o.option_text, option_label=o.option_label,
                is_correct=o.is_correct, order=o.order,
            )
            db.add(opt)

    await db.flush()

    # Refresh
    result = await db.execute(
        select(Question).options(selectinload(Question.options))
        .where(Question.id == question_id)
    )
    q = result.scalar_one()

    return QuestionResponse(
        id=str(q.id), question_text=q.question_text,
        code_snippet=q.code_snippet,
        question_type=q.question_type.value if hasattr(q.question_type, 'value') else q.question_type,
        language=q.language.value if hasattr(q.language, 'value') else q.language,
        difficulty=q.difficulty.value if hasattr(q.difficulty, 'value') else q.difficulty,
        correct_answer=q.correct_answer, explanation=q.explanation,
        tags=q.tags or [], time_limit=q.time_limit, is_active=q.is_active,
        options=[
            {"id": str(o.id), "option_text": o.option_text,
             "option_label": o.option_label, "is_correct": o.is_correct, "order": o.order}
            for o in q.options
        ],
        created_at=q.created_at,
    )


@router.delete("/{question_id}")
async def delete_question(
    question_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a question."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    await db.delete(q)
    await db.flush()
    return {"message": "Question deleted"}


@router.post("/bulk-upload")
async def bulk_upload_csv(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk upload questions from CSV.
    Expected columns: question_text, code_snippet, question_type, language,
    difficulty, correct_answer, explanation, tags, option_a, option_b, option_c, option_d
    """
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    count = 0
    for row in reader:
        q_text = row.get("question_text", "").strip()
        if not q_text:
            continue

        tags_str = row.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        q = Question(
            id=uuid4(), question_text=q_text,
            code_snippet=row.get("code_snippet", "").strip() or None,
            question_type=row.get("question_type", "multiple_choice").strip(),
            language=row.get("language", "python").strip(),
            difficulty=row.get("difficulty", "easy").strip(),
            correct_answer=row.get("correct_answer", "").strip(),
            explanation=row.get("explanation", "").strip() or None,
            tags=tags,
            time_limit=int(row.get("time_limit", "60")),
        )
        db.add(q)
        await db.flush()

        # Add options
        labels = ["A", "B", "C", "D"]
        for i, label in enumerate(labels):
            opt_text = row.get(f"option_{label.lower()}", "").strip()
            if opt_text:
                is_correct = row.get("correct_answer", "").strip().upper() == label
                opt = QuestionOption(
                    id=uuid4(), question_id=q.id,
                    option_text=opt_text, option_label=label,
                    is_correct=is_correct, order=i,
                )
                db.add(opt)

        count += 1

    await db.flush()
    return {"message": f"Uploaded {count} questions"}


@router.get("/stats/summary")
async def question_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get question bank statistics."""
    total = (await db.execute(select(func.count(Question.id)))).scalar()
    by_difficulty = {}
    for diff in ["easy", "medium", "hard"]:
        count = (await db.execute(
            select(func.count(Question.id)).where(Question.difficulty == diff)
        )).scalar()
        by_difficulty[diff] = count

    by_language = {}
    for lang in ["python", "java", "c", "cpp", "sql", "html", "javascript", "mixed"]:
        count = (await db.execute(
            select(func.count(Question.id)).where(Question.language == lang)
        )).scalar()
        if count > 0:
            by_language[lang] = count

    return {
        "total": total,
        "by_difficulty": by_difficulty,
        "by_language": by_language,
    }
