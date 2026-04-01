import httpx
import reflex as rx

from pm_app.constants import SELECT_ALL_CATEGORIES, SELECT_NO_FILE_RULES

API_BASE = "http://127.0.0.1:8000"


class AppState(rx.State):
    teams: list[dict] = []
    members: list[dict] = []
    tasks: list[dict] = []
    activities: list[dict] = []
    performance: list[dict] = []
    kanban: dict[str, list[dict]] = {
        "backlog": [],
        "todo": [],
        "in_progress": [],
        "review": [],
        "done": [],
        "returned": [],
    }
    active_team_id: int = 0
    category_filter: str = SELECT_ALL_CATEGORIES
    team_name: str = ""
    team_description: str = ""
    team_join_code: str = ""
    member_name: str = ""
    member_email: str = ""
    member_role: str = "member"
    join_code_input: str = ""
    join_display_name: str = ""
    join_email: str = ""
    join_role: str = "member"
    task_name: str = ""
    task_description: str = ""
    task_attachment: str = ""
    task_file_rules: str = SELECT_NO_FILE_RULES
    task_category: str = "general"
    task_creator: str = "manager"
    task_deadline: str = ""
    task_assignee_choice: str = "none"
    activity_title: str = ""
    activity_start: str = ""
    activity_end: str = ""
    activity_category: str = "general"
    task_dialog_open: bool = False
    detail_task: dict = {}
    detail_subtasks: list[dict] = []
    detail_logs: list[dict] = []
    return_reason: str = ""
    detail_grade: str = ""
    detail_assignee_value: str = "none"
    detail_title: str = ""
    detail_status_value: str = "backlog"
    new_subtask_title: str = ""
    has_teams: bool = False

    async def load_teams(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/teams")
            self.teams = resp.json()
        self.has_teams = len(self.teams) > 0
        if self.teams:
            ids = {t["id"] for t in self.teams}
            if self.active_team_id not in ids:
                self.active_team_id = self.teams[0]["id"]
        else:
            self.active_team_id = 0

    async def load_members(self):
        if not self.active_team_id:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/teams/{self.active_team_id}/members")
            self.members = resp.json()

    async def load_tasks(self):
        params = {"team_id": self.active_team_id} if self.active_team_id else {}
        if self.category_filter and self.category_filter != SELECT_ALL_CATEGORIES:
            params["category"] = self.category_filter
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/tasks", params=params)
            self.tasks = resp.json()

    async def load_kanban(self):
        if not self.active_team_id:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/tasks/kanban", params={"team_id": self.active_team_id})
            self.kanban = resp.json()

    async def load_activities(self):
        if not self.active_team_id:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/planning", params={"team_id": self.active_team_id})
            self.activities = resp.json()

    async def load_performance(self):
        if not self.active_team_id:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/planning/performance", params={"team_id": self.active_team_id})
            self.performance = resp.json()

    async def refresh_all(self):
        await self.load_teams()
        await self.load_members()
        await self.load_tasks()
        await self.load_kanban()
        await self.load_activities()
        await self.load_performance()

    def set_category_filter(self, category: str):
        self.category_filter = category

    async def on_category_filter_change(self, category: str):
        self.category_filter = category
        await self.load_tasks()

    async def on_team_selected(self, team_id: str):
        self.active_team_id = int(team_id) if team_id else 0
        await self.load_members()
        await self.load_tasks()
        await self.load_kanban()
        await self.load_activities()
        await self.load_performance()

    def set_team_name(self, value: str):
        self.team_name = value

    def set_team_description(self, value: str):
        self.team_description = value

    def set_team_join_code(self, value: str):
        self.team_join_code = value

    async def create_team(self):
        payload = {
            "name": self.team_name,
            "description": self.team_description,
            "join_code": self.team_join_code,
        }
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_BASE}/teams", json=payload)
        self.team_name = ""
        self.team_description = ""
        self.team_join_code = ""
        await self.refresh_all()

    def set_member_name(self, value: str):
        self.member_name = value

    def set_member_email(self, value: str):
        self.member_email = value

    def set_member_role(self, value: str):
        self.member_role = value

    def set_join_code_input(self, value: str):
        self.join_code_input = value

    def set_join_display_name(self, value: str):
        self.join_display_name = value

    def set_join_email(self, value: str):
        self.join_email = value

    def set_join_role(self, value: str):
        self.join_role = value

    async def join_team_by_code(self):
        if not self.join_code_input.strip():
            return
        payload = {
            "display_name": self.join_display_name,
            "email": self.join_email,
            "role_name": self.join_role,
        }
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_BASE}/teams/join/{self.join_code_input.strip()}", json=payload)
        self.join_code_input = ""
        self.join_display_name = ""
        self.join_email = ""
        self.join_role = "member"
        await self.refresh_all()

    async def add_member(self):
        if not self.active_team_id:
            return
        payload = {
            "team_id": self.active_team_id,
            "display_name": self.member_name,
            "email": self.member_email,
            "role_name": self.member_role,
        }
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_BASE}/teams/members", json=payload)
        self.member_name = ""
        self.member_email = ""
        self.member_role = "member"
        await self.refresh_all()

    async def remove_member(self, member_id: int):
        async with httpx.AsyncClient() as client:
            await client.delete(f"{API_BASE}/teams/members/{member_id}")
        await self.refresh_all()

    def set_task_name(self, value: str):
        self.task_name = value

    def set_task_description(self, value: str):
        self.task_description = value

    def set_task_attachment(self, value: str):
        self.task_attachment = value

    def set_task_file_rules(self, value: str):
        self.task_file_rules = value

    def set_task_category(self, value: str):
        self.task_category = value

    def set_task_creator(self, value: str):
        self.task_creator = value

    def set_task_deadline(self, value: str):
        self.task_deadline = value

    def set_task_assignee_choice(self, value: str):
        self.task_assignee_choice = value

    @staticmethod
    def _normalize_datetime_local(s: str) -> str:
        s = s.strip()
        if not s:
            return s
        if len(s) == 16 and s[10] == "T":
            return f"{s}:00"
        return s

    async def create_task(self):
        if not self.task_name.strip():
            return rx.toast.error("Enter a task title.")
        if not self.active_team_id:
            return rx.toast.error("Create a team in the Team tab, then choose it in Active workspace.")
        payload = {
            "team_id": self.active_team_id,
            "creator_name": self.task_creator.strip() or "unknown",
            "name": self.task_name.strip(),
            "description": self.task_description,
            "attachment_url": self.task_attachment,
            "file_rules": ""
            if self.task_file_rules in ("", SELECT_NO_FILE_RULES)
            else self.task_file_rules,
            "category": self.task_category,
        }
        dl = self._normalize_datetime_local(self.task_deadline)
        if dl:
            payload["deadline"] = dl
        if self.task_assignee_choice and self.task_assignee_choice != "none":
            payload["assignee_id"] = int(self.task_assignee_choice)
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{API_BASE}/tasks", json=payload)
        except Exception as exc:
            return rx.toast.error(f"Cannot reach API at {API_BASE}. Is the backend running? ({exc})")
        if r.status_code >= 400:
            msg = r.text
            try:
                err = r.json()
                if isinstance(err, dict) and "detail" in err:
                    msg = str(err["detail"])
            except Exception:
                pass
            return rx.toast.error(f"Create task failed ({r.status_code}): {msg}"[:400])
        self.task_name = ""
        self.task_description = ""
        self.task_attachment = ""
        self.task_file_rules = SELECT_NO_FILE_RULES
        self.task_deadline = ""
        self.task_assignee_choice = "none"
        self.task_category = "general"
        await self.refresh_all()
        return rx.toast.success("Task created.")

    def set_activity_title(self, value: str):
        self.activity_title = value

    def set_activity_start(self, value: str):
        self.activity_start = value

    def set_activity_end(self, value: str):
        self.activity_end = value

    def set_activity_category(self, value: str):
        self.activity_category = value

    async def create_activity(self):
        if not self.active_team_id or not self.activity_start or not self.activity_end:
            return
        payload = {
            "team_id": self.active_team_id,
            "title": self.activity_title,
            "timeline_start": self._normalize_datetime_local(self.activity_start),
            "timeline_end": self._normalize_datetime_local(self.activity_end),
            "category": self.activity_category,
        }
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_BASE}/planning", json=payload)
        self.activity_title = ""
        self.activity_start = ""
        self.activity_end = ""
        await self.refresh_all()

    def on_task_dialog_open_change(self, is_open: bool):
        self.task_dialog_open = is_open
        if not is_open:
            self.detail_task = {}
            self.detail_subtasks = []
            self.detail_logs = []
            self.return_reason = ""
            self.new_subtask_title = ""
            self.detail_assignee_value = "none"
            self.detail_title = ""
            self.detail_status_value = "backlog"

    async def _reload_detail_task(self, task_id: int):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{API_BASE}/tasks/{task_id}")
            if r.status_code == 200:
                self.detail_task = r.json()
                self.detail_grade = ""
                g = self.detail_task.get("grade")
                if g is not None:
                    self.detail_grade = str(g)
                aid = self.detail_task.get("assignee_id")
                self.detail_assignee_value = "none" if aid is None else str(aid)
                self.detail_title = str(self.detail_task.get("name", ""))
                self.detail_status_value = str(self.detail_task.get("status", "backlog"))

    async def _reload_subtasks_logs(self, task_id: int):
        async with httpx.AsyncClient() as client:
            sr = await client.get(f"{API_BASE}/tasks/{task_id}/subtasks")
            if sr.status_code == 200:
                self.detail_subtasks = sr.json()
            lr = await client.get(f"{API_BASE}/tasks/{task_id}/logs")
            if lr.status_code == 200:
                self.detail_logs = lr.json()

    async def open_task(self, task_id: int):
        await self._reload_detail_task(task_id)
        if not self.detail_task.get("id"):
            return
        await self._reload_subtasks_logs(task_id)
        self.return_reason = ""
        self.new_subtask_title = ""
        self.task_dialog_open = True

    def set_return_reason(self, value: str):
        self.return_reason = value

    def set_detail_grade(self, value: str):
        self.detail_grade = value

    def set_new_subtask_title(self, value: str):
        self.new_subtask_title = value

    async def update_detail_status(self, status: str):
        if not self.detail_task:
            return
        self.detail_status_value = status
        tid = self.detail_task["id"]
        async with httpx.AsyncClient() as client:
            await client.patch(f"{API_BASE}/tasks/{tid}", json={"status": status})
        await self._reload_detail_task(tid)
        await self.refresh_all()

    async def update_detail_assignee(self, choice: str):
        if not self.detail_task:
            return
        tid = self.detail_task["id"]
        body = {"assignee_id": None if choice in ("", "none") else int(choice)}
        async with httpx.AsyncClient() as client:
            await client.patch(f"{API_BASE}/tasks/{tid}", json=body)
        await self._reload_detail_task(tid)
        await self.refresh_all()

    async def save_detail_grade(self):
        if not self.detail_task:
            return
        tid = self.detail_task["id"]
        raw = self.detail_grade.strip()
        body = {"grade": int(raw)} if raw.isdigit() else {"grade": None}
        async with httpx.AsyncClient() as client:
            await client.patch(f"{API_BASE}/tasks/{tid}", json=body)
        await self._reload_detail_task(tid)
        await self.refresh_all()

    async def submit_return_task(self):
        if not self.detail_task or not self.return_reason.strip():
            return
        tid = self.detail_task["id"]
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_BASE}/tasks/{tid}/return",
                params={"reason": self.return_reason.strip()},
            )
        self.return_reason = ""
        await self._reload_detail_task(tid)
        await self.refresh_all()

    async def add_subtask(self):
        if not self.detail_task or not self.new_subtask_title.strip():
            return
        tid = self.detail_task["id"]
        payload = {"task_id": tid, "title": self.new_subtask_title.strip()}
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_BASE}/tasks/{tid}/subtasks", json=payload)
        self.new_subtask_title = ""
        await self._reload_subtasks_logs(tid)

    async def flip_subtask(self, subtask_id: int):
        if not self.detail_task:
            return
        tid = self.detail_task["id"]
        current = None
        for s in self.detail_subtasks:
            if s["id"] == subtask_id:
                current = s["is_done"]
                break
        if current is None:
            return
        async with httpx.AsyncClient() as client:
            await client.patch(f"{API_BASE}/tasks/subtasks/{subtask_id}", json={"is_done": not current})
        await self._reload_subtasks_logs(tid)
        await self.refresh_all()

    async def move_task_status(self, task_id: int, new_status: str):
        async with httpx.AsyncClient() as client:
            await client.patch(f"{API_BASE}/tasks/{task_id}", json={"status": new_status})
        if self.detail_task and self.detail_task.get("id") == task_id:
            await self._reload_detail_task(task_id)
        await self.refresh_all()
