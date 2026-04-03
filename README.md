# Jira_Copycat (FlowBoard)

Stack:
- Frontend: Reflex
- Backend: FastAPI
- Database: MySQL

Excluded in this implementation:
- Authentication
- Comments
- Notifications

## Features Included

- Kanban task board
- Task creation with name, description, link, file rule restriction, deadline, category
- Cross-team assignment support by team/member model
- Reject/return work with flag and reason
- One-layer subtasks
- Task permissions by role
- Task access and grading fields
- Activity planning and timeline
- Backlog log via task status and action logs
- Team management (add/remove members, roles)
- Progress and team performance visualization data endpoint
- Theme toggle in UI
- Basic profile-compatible member fields (name, email)

## Backend Setup

1. Go to `backend`
2. Create `.env` from `.env.example`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Run API:
   - `uvicorn app.main:app --reload`

## Frontend Setup

1. Go to `frontend`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run Reflex:
   - `reflex init`
   - `reflex run`

Backend base URL is currently `http://127.0.0.1:8000` in `frontend/pm_app/state.py`.
