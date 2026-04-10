# FlowBoard (Jira Copycat) — Presentation Brief + Claude Prompt

## 1) Project Overview (high-level)

**FlowBoard** is a lightweight Jira-style project management web app that combines:
- Team management (join codes, invitations, join requests)
- Kanban task board (status lanes)
- Task delivery workflow (assignee submissions + file upload)
- Activity planning + performance views
- In-app notifications
- Task comments

It is built as a **FastAPI + SQLAlchemy backend** with a **Reflex (Python) frontend**.

### Target users / roles
- **Supervisor (team owner/lead)**
  - Creates teams and tasks
  - Assigns tasks and manages team membership
  - Can grade/close tasks (complete workflow)
  - Can review submissions
- **Member**
  - Joins teams via join code (subject to approval)
  - Works on assigned tasks
  - Submits work (title/description + optional file)
  - Comments on tasks

### Key value proposition
- Everything needed for a small team workflow:
  - Create tasks -> assign -> track -> submit deliverables -> close/grade
  - Communication via comments + notifications
  - Planning/activities in the same workspace

---

## 2) Tech Stack & Architecture

### Frontend
- **Framework**: Reflex (Python full-stack UI framework)
- **Styling**: Tailwind plugin enabled via Reflex config
- **State management**: Central `AppState` (frontend/pm_app/state.py)
- **Pages**:
  - Dashboard (main workspace)
  - Login / Register
  - Forgot password / Reset password
- **Components**:
  - Comments (`pm_app/components/comment.py`)
  - Notifications (`pm_app/components/notification.py`)

Frontend talks to backend through HTTP calls to:
- `API_BASE = http://127.0.0.1:8001`

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **DB**: SQLite by default for local dev (can switch to MySQL via env)
- **Auth**: JWT tokens (access + refresh) + optional email reset
- **Uploads**:
  - Stores task submission files on server under `backend/uploads/task_submissions`
  - Size limit: 25MB

Backend entry point:
- `backend/app/main.py`

Key modules:
- `backend/app/models.py` — SQLAlchemy models (User, Team, TeamMember, Task, SubTask, TaskSubmission, Comment, Notification, etc.)
- `backend/app/routers/*` — route handlers
- `backend/app/database.py` — engine creation + schema safety helpers

---

## 3) Data Model (what entities exist and why)

### Core entities
- **User**
  - Global account: handle (User ID), name, email (optional), password hash
- **Team**
  - Name, join code, description
- **TeamMember**
  - Links a user handle to a team with:
    - `display_name`
    - `handle`
    - `role_name` (e.g., `member`, `supervisor`, `lead`)

### Task system
- **Task**
  - Belongs to a team (`team_id`)
  - Optional assignee (`assignee_id` -> TeamMember)
  - Status enum: backlog / todo / in_progress / review / done / returned
  - Deadline, category, description, file rules
  - `closed` boolean (prevents further submissions)
  - Optional `grade`
- **SubTask**
  - Checklist items for a task
- **TaskSubmission**
  - Deliverable submitted by assignee
  - Contains title/description and optional uploaded file metadata:
    - stored path
    - original filename
    - content type
    - size
- **TaskLog**
  - Audit trail of task actions

### Collaboration
- **Comment**
  - Task-level comments
  - Stores `author_id` as **TeamMember.id** (important detail)
  - Stores `author_name` and `author_role`
- **Notification**
  - For join requests, task assigned, new comment, work submitted, etc.

---

## 4) Key User Flows (end-to-end)

### A) Authentication flow
- Register -> login
- Backend issues JWT access + refresh tokens
- Optional password reset email flow if SMTP env vars are set

### B) Team creation + membership
- Supervisor creates a team (becomes TeamMember role `supervisor`)
- Members join using a **join code** -> creates a pending join request
- Supervisor approves/rejects join requests

### C) Task lifecycle (Kanban)
- Supervisor creates tasks in a team
- Tasks appear in a kanban board grouped by status
- Supervisor assigns tasks to a TeamMember
- Status changes move cards across lanes

### D) Work submission (with file upload)
- Only the **assignee** may submit
- Submission contains:
  - title (required)
  - description (optional)
  - optional file upload (<= 25MB)
- Backend stores file and returns metadata + a download URL

### E) Comments + Notifications
- Team members comment on tasks
- Backend writes comment + may notify assignee
- Notification panel shows recent events (comment/task assigned/etc.)

---

## 5) Important Implementation Details (useful for presenting)

### Backend environment configuration
In `backend/app/database.py`:
- If `DATABASE_URL` is set -> uses it
- Else if `USE_SQLITE=true` (default) -> uses `sqlite:///./local.db`
- Else -> constructs MySQL URL from MYSQL_* env vars

### File uploads
In `backend/app/routers/task.py`:
- Submission endpoint: `POST /tasks/{task_id}/submissions`
- File streamed as multipart
- Saved under `backend/uploads/task_submissions/<uuid>.<ext>`
- Download endpoint: `GET /tasks/submissions/{submission_id}/file`

### Role model
- Global account role is not a single field; **team membership** carries `role_name`.
- UI logic should use the user’s role in the currently viewed team.

---

## 6) Bugs Fixed During This Work (for the presentation / changelog)

### 6.1 Task submission blocked for members
**Symptom**: Assigned members could not see/perform submission.

**Root cause**: Assignee check relied on `self.members` loaded for `active_team_id`, but tasks can belong to a different team. That caused `i_am_detail_assignee` to be false.

**Fix**:
- Load members for the task’s real team when opening the task detail
- Re-sync assignee flags after loading correct members

### 6.2 Backend crash on first run: `no such table: tasks`
**Symptom**: Backend startup crashed with SQLite `OperationalError` when trying to `ALTER TABLE tasks`.

**Root cause**: `ensure_sqlite_schema()` ran before `Base.metadata.create_all()`, so the `tasks` table did not exist yet.

**Fix**:
- Re-ordered startup in `backend/app/main.py`:
  - Create tables first
  - Then run the schema “ensure” helpers

### 6.3 Comments show wrong author / wrong role badge
**Symptom**:
- Account 2 comments appeared as Account 3 (and vice versa)
- Supervisor’s role displayed as `MEMBER`

**Root cause**:
- Comment API stores `author_id` as **TeamMember.id**
- Frontend was sending **User.id** instead
- Role should come from TeamMember `role_name`, not from the global user profile

**Fix**:
- Track `current_member_id` in frontend state
- Compute it from the team member list when members are loaded
- Pass `current_member_id` and team role to CommentState when opening tasks

---

## 7) Suggested Presentation Structure (slide-by-slide)

1. **Title**
   - FlowBoard: Jira-style Kanban + Team workflow

2. **Problem & Motivation**
   - Small teams need lightweight task delivery + visibility

3. **Key Features**
   - Teams & membership approval
   - Kanban board
   - Task submissions + file upload
   - Comments & notifications
   - Planning & performance

4. **User Roles & Permissions**
   - Supervisor vs Member capabilities

5. **System Architecture**
   - Reflex frontend
   - FastAPI backend
   - SQLAlchemy + SQLite/MySQL

6. **Data Model Overview**
   - User / Team / TeamMember / Task / Submission / Comment / Notification

7. **Workflow Demo (happy path)**
   - Create team -> join -> create task -> assign -> submit -> notify -> close

8. **Engineering Highlights**
   - File storage and download endpoint
   - Logs & notifications

9. **Bug Fixes & Improvements**
   - Submission assignee check fix
   - DB startup order fix
   - Comment author/role fix

10. **Future Work**
   - Role-based UI polish
   - Better file storage (cloud)
   - Pagination/search
   - CI + tests

---

## 8) Claude Prompt (copy/paste)

Use the following prompt in Claude to generate your slides + script.

---

### Prompt to Claude

You are helping me create a professional presentation for a university software engineering project.

Project name: **FlowBoard** (a Jira-style project/task management web app).

I will provide a project brief below. Based on it, produce:
1) A slide deck outline with **10 slides** maximum.
2) For each slide:
   - Title
   - 3–6 bullet points (short, clear)
   - Speaker notes (what I should say)
3) A 3–5 minute speaking script (continuous) that matches the slide flow.
4) A 2-minute demo plan (what to click/show in the app).

Constraints:
- Keep language clear for a mixed technical/non-technical audience.
- Highlight roles/permissions, task lifecycle, and file submissions.
- Include a short section describing the 3 major bugs we fixed and how.

Here is the project brief:

[PASTE EVERYTHING FROM SECTIONS 1–7 HERE]

---
