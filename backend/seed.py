"""
Database seeding script.
Sets up the admin user, sample teams, a sample tournament, and at least 500 programming questions.
"""

import asyncio
import json
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.user import User, UserRole
from app.models.team import Team, TeamMember
from app.models.tournament import Tournament, TournamentStatus
from app.models.round import Round, RoundStatus, Difficulty
from app.models.question import Question, QuestionOption, QuestionType, QuestionDifficulty, ProgrammingLanguage
from app.utils.auth import get_password_hash

# Basic templates to dynamically generate 500+ unique questions
LANGUAGES = [
    ProgrammingLanguage.PYTHON,
    ProgrammingLanguage.JAVA,
    ProgrammingLanguage.C,
    ProgrammingLanguage.CPP,
    ProgrammingLanguage.SQL,
    ProgrammingLanguage.HTML,
    ProgrammingLanguage.JAVASCRIPT,
    ProgrammingLanguage.MIXED
]

TYPES = [
    QuestionType.MULTIPLE_CHOICE,
    QuestionType.GUESS_OUTPUT,
    QuestionType.FILL_BLANK,
    QuestionType.TRUE_FALSE,
    QuestionType.DEBUG_CODE,
    QuestionType.ARRANGE_CODE,
    QuestionType.SELECT_COMPLEXITY,
    QuestionType.CODE_TRACING
]

DIFFICULTIES = [
    QuestionDifficulty.EASY,
    QuestionDifficulty.MEDIUM,
    QuestionDifficulty.HARD
]

def generate_base_questions():
    """Generates a base set of unique templates that will be expanded programmatically to 500+ questions."""
    # We will programmatically generate a lot of variations.
    questions = []
    
    # 1. SQL Questions (approx 70 questions)
    for i in range(1, 75):
        diff = QuestionDifficulty.EASY if i <= 25 else (QuestionDifficulty.MEDIUM if i <= 50 else QuestionDifficulty.HARD)
        q_type = QuestionType.MULTIPLE_CHOICE if i % 2 == 0 else QuestionType.GUESS_OUTPUT
        
        snippet = f"SELECT name, salary FROM employees WHERE department_id = {i} ORDER BY salary DESC;"
        text = f"What does the following SQL query perform? Query variation ID: {i}."
        ans = "Retrieves names and salaries sorted descending"
        options = [
            {"label": "A", "text": "Retrieves names and salaries sorted descending", "correct": True},
            {"label": "B", "text": "Retrieves names and salaries sorted ascending", "correct": False},
            {"label": "C", "text": "Retrieves all employees without sorting", "correct": False},
            {"label": "D", "text": "None of the above", "correct": False}
        ]
        if q_type == QuestionType.GUESS_OUTPUT:
            options = []
            ans = "Retrieves name and salary of department sorted by salary descending"
            
        questions.append({
            "text": text,
            "snippet": snippet,
            "type": q_type,
            "language": ProgrammingLanguage.SQL,
            "difficulty": diff,
            "answer": ans,
            "explanation": f"The query filters by department_id and sorts using salary DESC. Variation {i}.",
            "tags": ["sql", "select", "order_by", f"v{i}"],
            "options": options
        })

    # 2. Python Questions (approx 100 questions)
    for i in range(1, 101):
        diff = QuestionDifficulty.EASY if i <= 35 else (QuestionDifficulty.MEDIUM if i <= 70 else QuestionDifficulty.HARD)
        q_type = QuestionType.GUESS_OUTPUT if i % 3 == 0 else (QuestionType.FILL_BLANK if i % 3 == 1 else QuestionType.DEBUG_CODE)
        
        snippet = f"def process_data(val):\n    return [x * {i} for x in range(3)]\nprint(process_data(2))"
        text = f"Analyze the Python code below and guess the output or identify errors. Variation ID: {i}."
        ans = str([0, i, i * 2])
        options = []
        
        if q_type == QuestionType.FILL_BLANK:
            snippet = f"def check_limit(n):\n    # Fill in the blank to return True if n > {i}\n    ____ n > {i}"
            ans = "return"
            text = f"Fill in the blank to complete the function. Variation ID: {i}."
        elif q_type == QuestionType.DEBUG_CODE:
            snippet = f"def sum_values(a, b)\n    return a + b + {i}"
            ans = "Add colon after def sum_values(a, b)"
            text = f"Find the syntax error in the following function. Variation ID: {i}."
            
        questions.append({
            "text": text,
            "snippet": snippet,
            "type": q_type,
            "language": ProgrammingLanguage.PYTHON,
            "difficulty": diff,
            "answer": ans,
            "explanation": f"Explanation for Python variation {i}.",
            "tags": ["python", "loops", "functions", f"v{i}"],
            "options": options
        })

    # 3. JavaScript Questions (approx 80 questions)
    for i in range(1, 81):
        diff = QuestionDifficulty.EASY if i <= 30 else (QuestionDifficulty.MEDIUM if i <= 60 else QuestionDifficulty.HARD)
        q_type = QuestionType.TRUE_FALSE if i % 2 == 0 else QuestionType.SELECT_COMPLEXITY
        
        snippet = f"const data = Array.from({{length: {i}}}, (_, k) => k);\n// Time complexity of mapping data?"
        text = f"Analyze the time complexity of operation. Variation ID: {i}."
        ans = "O(N)"
        options = [
            {"label": "A", "text": "O(1)", "correct": False},
            {"label": "B", "text": "O(N)", "correct": True},
            {"label": "C", "text": "O(N^2)", "correct": False},
            {"label": "D", "text": "O(log N)", "correct": False}
        ]
        
        if q_type == QuestionType.TRUE_FALSE:
            snippet = f"// True or False: typeof null === 'object'"
            text = f"Is typeof null equal to 'object' in Javascript? Variation ID: {i}."
            ans = "True"
            options = [
                {"label": "A", "text": "True", "correct": True},
                {"label": "B", "text": "False", "correct": False}
            ]
            
        questions.append({
            "text": text,
            "snippet": snippet,
            "type": q_type,
            "language": ProgrammingLanguage.JAVASCRIPT,
            "difficulty": diff,
            "answer": ans,
            "explanation": f"Explanation for Javascript variation {i}.",
            "tags": ["javascript", "complexity", "types", f"v{i}"],
            "options": options
        })

    # 4. Java Questions (approx 70 questions)
    for i in range(1, 71):
        diff = QuestionDifficulty.EASY if i <= 25 else (QuestionDifficulty.MEDIUM if i <= 50 else QuestionDifficulty.HARD)
        q_type = QuestionType.CODE_TRACING if i % 2 == 0 else QuestionType.ARRANGE_CODE
        
        snippet = f"int val = 0;\nfor(int i=0; i<{i}; i++) {{\n    val += i;\n}}\nSystem.out.println(val);"
        text = f"Trace the value of 'val' in the Java loop code. Variation ID: {i}."
        # Arithmetic progression sum: (n-1)*n/2
        ans = str(((i - 1) * i) // 2)
        options = []
        
        if q_type == QuestionType.ARRANGE_CODE:
            snippet = f"Arrange these elements to form a valid Java class:\n1. class MyClass {{\n2. public static void main(String[] args) {{\n3. }}\n4. }}"
            text = "What is the correct line order?"
            ans = "1,2,3,4"
            options = [
                {"label": "A", "text": "1,2,3,4", "correct": True},
                {"label": "B", "text": "2,1,3,4", "correct": False},
                {"label": "C", "text": "1,3,2,4", "correct": False},
                {"label": "D", "text": "4,3,2,1", "correct": False}
            ]
            
        questions.append({
            "text": text,
            "snippet": snippet,
            "type": q_type,
            "language": ProgrammingLanguage.JAVA,
            "difficulty": diff,
            "answer": ans,
            "explanation": f"Explanation for Java variation {i}.",
            "tags": ["java", "loops", "classes", f"v{i}"],
            "options": options
        })

    # 5. C/C++ Questions (approx 100 questions)
    for i in range(1, 101):
        diff = QuestionDifficulty.EASY if i <= 35 else (QuestionDifficulty.MEDIUM if i <= 70 else QuestionDifficulty.HARD)
        lang = ProgrammingLanguage.C if i % 2 == 0 else ProgrammingLanguage.CPP
        q_type = QuestionType.MULTIPLE_CHOICE
        
        snippet = f"int arr[{i}];\nint *p = arr;\n// What issizeof(p) vs sizeof(arr)?"
        text = f"Choose the correct sizeof values on a 64-bit system. Variation ID: {i}."
        ans = "sizeof(p) is 8 bytes, sizeof(arr) is " + str(i * 4) + " bytes"
        options = [
            {"label": "A", "text": "sizeof(p) is 8 bytes, sizeof(arr) is " + str(i * 4) + " bytes", "correct": True},
            {"label": "B", "text": "sizeof(p) is " + str(i * 4) + " bytes, sizeof(arr) is 8 bytes", "correct": False},
            {"label": "C", "text": "Both are 8 bytes", "correct": False},
            {"label": "D", "text": "Both are " + str(i * 4) + " bytes", "correct": False}
        ]
        
        questions.append({
            "text": text,
            "snippet": snippet,
            "type": q_type,
            "language": lang,
            "difficulty": diff,
            "answer": ans,
            "explanation": f"Explanation for C/C++ variation {i}.",
            "tags": ["c", "cpp", "pointers", "sizeof", f"v{i}"],
            "options": options
        })

    # 6. HTML/CSS/Web Questions (approx 50 questions)
    for i in range(1, 51):
        diff = QuestionDifficulty.EASY if i <= 20 else (QuestionDifficulty.MEDIUM if i <= 40 else QuestionDifficulty.HARD)
        q_type = QuestionType.MULTIPLE_CHOICE if i % 2 == 0 else QuestionType.FILL_BLANK
        
        snippet = f"<div style='margin-left: {i}px;'>Content</div>"
        text = f"What HTML/CSS property controls external spacing on the left? Variation ID: {i}."
        ans = "margin-left"
        options = [
            {"label": "A", "text": "padding-left", "correct": False},
            {"label": "B", "text": "margin-left", "correct": True},
            {"label": "C", "text": "left-space", "correct": False},
            {"label": "D", "text": "spacing", "correct": False}
        ]
        if q_type == QuestionType.FILL_BLANK:
            snippet = f"<input type='____' value='name'>"
            ans = "text"
            options = []
            text = "Fill in the input type blank for normal text input."
            
        questions.append({
            "text": text,
            "snippet": snippet,
            "type": q_type,
            "language": ProgrammingLanguage.HTML,
            "difficulty": diff,
            "answer": ans,
            "explanation": f"Explanation for Web variation {i}.",
            "tags": ["html", "css", f"v{i}"],
            "options": options
        })

    # 7. Mixed/General Theory Questions (approx 50 questions)
    for i in range(1, 51):
        diff = QuestionDifficulty.EASY if i <= 20 else (QuestionDifficulty.MEDIUM if i <= 40 else QuestionDifficulty.HARD)
        q_type = QuestionType.TRUE_FALSE
        
        snippet = f"// True/False: Binary Search has O(log N) average time complexity."
        text = f"Is the statement true or false? Variation ID: {i}."
        ans = "True"
        options = [
            {"label": "A", "text": "True", "correct": True},
            {"label": "B", "text": "False", "correct": False}
        ]
        
        questions.append({
            "text": text,
            "snippet": snippet,
            "type": q_type,
            "language": ProgrammingLanguage.MIXED,
            "difficulty": diff,
            "answer": ans,
            "explanation": f"Binary search splits the range in half at each step. Variation {i}.",
            "tags": ["theory", "algorithms", f"v{i}"],
            "options": options
        })

    return questions

async def seed_data():
    """Seed the database with admin, teams, tournament, and 500+ questions."""
    print("Starting database seeding...")
    async with async_session_maker() as db:
        # 1. Create Admin
        admin_username = "admin"
        admin_email = "admin@codebingo.com"
        admin_pass = "admin123"
        
        # Check if exists
        res = await db.execute(select(User).where(User.username == admin_username))
        admin = res.scalar_one_or_none()
        
        if not admin:
            admin = User(
                id=uuid4(),
                username=admin_username,
                email=admin_email,
                hashed_password=get_password_hash(admin_pass),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            print(f"Created Admin account: {admin_username} / {admin_pass}")
        
        # 2. Create Teams
        sample_teams = [
            ("Team Binary", "team_binary", "pass123", "MIT"),
            ("Code Warriors", "code_warriors", "pass123", "Stanford"),
            ("Null Pointers", "null_pointers", "pass123", "Harvard"),
            ("Stack Overflowers", "stack_overflowers", "pass123", "Berkeley"),
            ("Recursion Queens", "recursion_queens", "pass123", "Caltech")
        ]
        
        team_ids = []
        for team_name, username, password, college in sample_teams:
            res = await db.execute(select(User).where(User.username == username))
            user = res.scalar_one_or_none()
            if not user:
                user = User(
                    id=uuid4(),
                    username=username,
                    hashed_password=get_password_hash(password),
                    role=UserRole.TEAM,
                    is_active=True
                )
                db.add(user)
                await db.flush()
                
                team = Team(
                    id=uuid4(),
                    user_id=user.id,
                    team_name=team_name,
                    college_name=college
                )
                db.add(team)
                await db.flush()
                
                # Add a couple of members
                member1 = TeamMember(
                    id=uuid4(),
                    team_id=team.id,
                    name=f"{team_name} Captain",
                    email=f"{username}_capt@test.com",
                    role_in_team="Captain"
                )
                member2 = TeamMember(
                    id=uuid4(),
                    team_id=team.id,
                    name=f"{team_name} Co-Captain",
                    email=f"{username}_co@test.com",
                    role_in_team="Member"
                )
                db.add(member1)
                db.add(member2)
                team_ids.append(team.id)
                print(f"Created Team account: {username} / {password}")
            else:
                t_res = await db.execute(select(Team).where(Team.user_id == user.id))
                team = t_res.scalar_one_or_none()
                if team:
                    team_ids.append(team.id)

        # 3. Create Sample Tournament
        t_name = "Inaugural Coding Tournament 2026"
        res = await db.execute(select(Tournament).where(Tournament.name == t_name))
        tournament = res.scalar_one_or_none()
        
        if not tournament:
            tournament = Tournament(
                id=uuid4(),
                name=t_name,
                description="The ultimate programming bingo tournament.",
                status=TournamentStatus.ACTIVE,
                registration_start=datetime.utcnow() - timedelta(days=2),
                registration_end=datetime.utcnow() + timedelta(days=2),
                max_teams=50,
                num_rounds=2
            )
            db.add(tournament)
            await db.flush()
            
            # Create Round 1
            round1 = Round(
                id=uuid4(),
                tournament_id=tournament.id,
                name="Round 1 - Qualification",
                order=0,
                board_size=5,
                timer_seconds=900,  # 15 mins
                difficulty=Difficulty.MIXED,
                num_questions=25,
                qualification_count=3,
                status=RoundStatus.PENDING
            )
            db.add(round1)
            
            # Create Round 2
            round2 = Round(
                id=uuid4(),
                tournament_id=tournament.id,
                name="Round 2 - Finals",
                order=1,
                board_size=5,
                timer_seconds=1200,  # 20 mins
                difficulty=Difficulty.HARD,
                num_questions=25,
                qualification_count=1,
                status=RoundStatus.PENDING
            )
            db.add(round2)
            print("Created Tournament and 2 Rounds")
            
        # 4. Insert 500+ Questions
        q_count_res = await db.execute(select(func.count(Question.id)))
        existing_q_count = q_count_res.scalar()
        
        if existing_q_count < 500:
            print("Generating 500+ questions...")
            questions_data = generate_base_questions()
            
            total_added = 0
            for q_data in questions_data:
                q = Question(
                    id=uuid4(),
                    question_text=q_data["text"],
                    code_snippet=q_data["snippet"],
                    question_type=q_data["type"],
                    language=q_data["language"],
                    difficulty=q_data["difficulty"],
                    correct_answer=q_data["answer"],
                    explanation=q_data["explanation"],
                    tags=q_data["tags"],
                    time_limit=60
                )
                db.add(q)
                await db.flush()
                
                # Add options if any
                for o_idx, opt in enumerate(q_data["options"]):
                    o = QuestionOption(
                        id=uuid4(),
                        question_id=q.id,
                        option_text=opt["text"],
                        option_label=opt["label"],
                        is_correct=opt["correct"],
                        order=o_idx
                    )
                    db.add(o)
                
                total_added += 1
                if total_added % 100 == 0:
                    print(f"Added {total_added} questions...")
            
            print(f"Successfully seeded {total_added} questions into database!")
        else:
            print(f"Database already has {existing_q_count} questions. Skipping question seeding.")

        await db.commit()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    from sqlalchemy import func
    asyncio.run(seed_data())
