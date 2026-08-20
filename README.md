# Code Bingo Tournament 🏆

A multiplayer programming quiz game designed for coding competitions and hackathons. Each team uses a single login and laptop to compete on a randomized Bingo board, answering code tracing, debugging, complexity, and output prediction questions. 

## Features

### 👑 Admin Features
- **Dashboard & Monitoring**: Real-time stats on connected teams, questions pool, active rounds, and active brackets.
- **Tournament CRUD**: Dynamic creation of tournaments, setting qualification thresholds (e.g. Round 1 top 10 advance), and managing infinite round progression.
- **Dynamic Board Configuration**: Configure boards to be **3x3, 4x4, 5x5, or 6x6** with configurable round timers.
- **Team Registry**: Manually create credentials or batch import complete team sheets via CSV.
- **Question Bank Manager**: Search, filter by programming language/difficulty, create single items, or bulk upload hundreds via CSV template.
- **Live Leaderboard**: Projector view showing rank, total score, bingos, solved metrics, and WebSocket statuses.

### 💻 Team Features
- **One-Session Limit**: Anti-duplicate login system prevents team members from using multiple screens.
- **Randomized Game Board**: Every team receives a unique layout matching the round's difficulty and size configuration.
- **Real-time Synchronization**: Instant notification popup for round transitions, real-time timer countdown, and qualification statuses.
- **Instant Feedback**: Colored tiles represent status (Gray: Unanswered, Green: Correct, Red: Incorrect/Locked, Gold: Bingo line).

---

## Technical Stack

- **Backend**: Python FastAPI, SQLAlchemy (asyncio), PostgreSQL, JWT Auth, WebSockets.
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Framer Motion, Axios.
- **Orchestration**: Docker, Docker Compose.

---

## Quick Start (with Docker)

1. **Clone and Navigate**:
   ```bash
   cd "Web Bingo"
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. **Spin up Infrastructure**:
   ```bash
   docker-compose up --build
   ```

The script will automatically perform:
- Table migrations.
- **Admin account creation** (`admin` / `admin123`).
- **5 Registration Team accounts** (`team_binary`, `code_warriors`, etc., with password `pass123`).
- **500+ Programming Question templates** seeded across all supported languages (Python, Java, JS, C, C++, HTML, SQL, Mixed).

4. **Access the Portals**:
   - Frontend Portal: [http://localhost:5173](http://localhost:5173)
   - API Docs / Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Local Development (Without Docker)

### Backend Setup:
1. Create a virtual environment and activate:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   ```
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize tables & seed:
   ```bash
   python seed.py
   ```
4. Start development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup:
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Run development build:
   ```bash
   npm run dev
   ```
