import httpx
import reflex as rx
from reflex.app import UploadFile

from pm_app.constants import SELECT_ALL_CATEGORIES, SELECT_NO_FILE_RULES

API_BASE = "http://127.0.0.1:8001"


class AppState(rx.State):
    # ── Auth ─────────────────────────────────────────────────────────────────
    is_authenticated: bool = False
    access_token: str = ""
    refresh_token_val: str = ""
    current_user_handle: str = ""
    current_user_name: str = ""
    current_user_email: str = ""
    current_user_id: int = 0
    current_user_role: str = "member"
    current_user_theme: str = "light"
    current_user_image: str = ""
    current_user_description: str = ""
    current_user_handle_changes_left: int = 1

    # ── Auth form fields ─────────────────────────────────────────────────────
    auth_handle: str = ""
    auth_password: str = ""
    auth_confirm_password: str = ""
    auth_name: str = ""
    auth_email: str = ""
    auth_message: str = ""
    auth_is_error: bool = False
    auth_is_loading: bool = False
    forgot_handle: str = ""
    forgot_message: str = ""
    forgot_is_error: bool = False
    reset_token: str = ""
    reset_new_password: str = ""
    reset_confirm_password: str = ""
    reset_message: str = ""
    reset_is_error: bool = False
    reset_is_success: bool = False

    # ── Profile edit fields ───────────────────────────────────────────────────
    profile_edit_handle: str = ""
    profile_edit_name: str = ""
    profile_edit_email: str = ""
    profile_edit_description: str = ""
    profile_dialog_open: bool = False
    change_pw_current: str = ""
    change_pw_new: str = ""
    change_pw_confirm: str = ""
    change_pw_message: str = ""
    change_pw_is_error: bool = False

    # ── Teams / Members / Tasks / Planning ───────────────────────────────────
    teams: list[dict] = []
    members: list[dict] = []
    tasks: list[dict] = []
    activities: list[dict] = []
    performance: list[dict] = []
    kanban: dict[str, list[dict]] = {
        "backlog": [], "todo": [], "in_progress": [],
        "review": [], "done": [], "returned": [],
    }
    active_team_id: int = 0
    category_filter: str = SELECT_ALL_CATEGORIES
    team_name: str = ""
    team_description: str = ""
    team_join_code: str = ""
    member_invite_handle: str = ""
    join_code_input: str = ""
    join_requests: list[dict] = []
    i_am_supervisor: bool = False
    current_member_id: int = 0  # TeamMember.id for the current user in current team
    task_name: str = ""
    task_description: str = ""
    task_attachment: str = ""
    task_file_rules: str = SELECT_NO_FILE_RULES
    task_category: str = "general"
    task_creator: str = ""
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
    detail_submissions: list[dict] = []
    i_am_detail_assignee: bool = False
    detail_assignee_label: str = "Unassigned"
    submit_work_title: str = ""
    submit_work_description: str = ""
    return_reason: str = ""
    detail_grade: str = ""
    detail_assignee_value: str = "none"
    detail_title: str = ""
    detail_status_value: str = "backlog"
    detail_grade_locked: bool = False
    detail_task_closed: bool = False
    new_subtask_title: str = ""
    has_teams: bool = False

    # ── HELPERS ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_error_detail(res) -> str:
        try:
            data = res.json()
        except Exception:
            return f"Server error (HTTP {res.status_code})"
        detail = data.get("detail") if isinstance(data, dict) else data
        if isinstance(detail, list):
            msgs = []
            for item in detail:
                if isinstance(item, dict):
                    field = " -> ".join(str(x) for x in item.get("loc", []))
                    msg = item.get("msg", "")
                    msgs.append(f"{field}: {msg}" if field else msg)
            return "; ".join(msgs) if msgs else str(detail)
        return str(detail) if detail else f"Unexpected error (HTTP {res.status_code})"

    def _clear_user_state(self):
        """Wipe all user-specific state — call on logout and before login."""
        self.is_authenticated = False
        self.access_token = ""
        self.refresh_token_val = ""
        self.current_user_handle = ""
        self.current_user_name = ""
        self.current_user_email = ""
        self.current_user_id = 0
        self.current_user_role = "member"
        self.current_user_image = ""
        self.current_user_description = ""
        self.current_user_handle_changes_left = 1
        self.current_member_id = 0  # Reset member ID
        self.teams = []
        self.members = []
        self.tasks = []
        self.activities = []
        self.performance = []
        self.kanban = {"backlog": [], "todo": [], "in_progress": [], "review": [], "done": [], "returned": []}
        self.active_team_id = 0
        self.join_requests = []
        self.i_am_supervisor = False
        self.detail_task = {}
        self.detail_subtasks = []
        self.detail_logs = []
        self.detail_submissions = []
        self.i_am_detail_assignee = False
        self.detail_assignee_label = "Unassigned"
        self.detail_grade_locked = False
        self.detail_task_closed = False
        self.task_dialog_open = False
        self.has_teams = False

    # ── AUTH EVENTS ──────────────────────────────────────────────────────────

    def set_auth_handle(self, v: str): self.auth_handle = v
    def set_auth_password(self, v: str): self.auth_password = v
    def set_auth_confirm_password(self, v: str): self.auth_confirm_password = v
    def set_auth_name(self, v: str): self.auth_name = v
    def set_auth_email(self, v: str): self.auth_email = v
    def set_forgot_handle(self, v: str): self.forgot_handle = v
    def set_reset_new_password(self, v: str): self.reset_new_password = v
    def set_reset_confirm_password(self, v: str): self.reset_confirm_password = v

    def on_reset_load(self):
        token = self.router.page.params.get("token", "")
        self.reset_token = token
        if not token:
            self.reset_message = "Invalid or missing reset token."
            self.reset_is_error = True

    async def _refresh_data(self):
        """Internal — no yield, safe to await."""
        await self.load_teams()
        await self.load_members()
        await self.load_join_requests()
        await self.load_tasks()
        await self.load_kanban()
        await self.load_activities()
        await self.load_performance()

    async def refresh_all(self):
        """Page-load handler — can yield."""
        if not self.is_authenticated:
            yield rx.redirect("/login")
            return
        await self._refresh_data()

    async def login(self):
        if not self.auth_handle or not self.auth_password:
            self.auth_message = "Please fill in all fields."
            self.auth_is_error = True
            return
        self.auth_is_loading = True
        self.auth_message = ""
        # wipe previous session before loading new one
        self._clear_user_state()
        yield
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{API_BASE}/auth/login",
                    json={"handle": self.auth_handle, "password": self.auth_password},
                )
            if res.status_code == 200:
                data = res.json()
                self.access_token = data["access_token"]
                self.refresh_token_val = data["refresh_token"]
                await self._fetch_user_profile(self.auth_handle)
                self.is_authenticated = True
                self.auth_message = ""
                self.auth_handle = ""
                self.auth_password = ""
                yield rx.redirect("/")
            else:
                self.auth_message = self._parse_error_detail(res)
                self.auth_is_error = True
        except Exception as e:
            self.auth_message = f"Error: {e}"
            self.auth_is_error = True
        self.auth_is_loading = False

    async def register(self):
        if not self.auth_handle or not self.auth_name or not self.auth_password:
            self.auth_message = "Please fill in all required fields."
            self.auth_is_error = True
            return
        if self.auth_password != self.auth_confirm_password:
            self.auth_message = "Passwords do not match."
            self.auth_is_error = True
            return
        if len(self.auth_password) < 6:
            self.auth_message = "Password must be at least 6 characters."
            self.auth_is_error = True
            return
        self.auth_is_loading = True
        self.auth_message = ""
        yield
        try:
            payload = {
                "handle": self.auth_handle,
                "name": self.auth_name,
                "password": self.auth_password,
            }
            if self.auth_email.strip():
                payload["email"] = self.auth_email.strip()
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{API_BASE}/auth/register", json=payload)
            if res.status_code == 201:
                self.auth_message = "Account created! Redirecting..."
                self.auth_is_error = False
                self.auth_handle = ""
                self.auth_name = ""
                self.auth_email = ""
                self.auth_password = ""
                self.auth_confirm_password = ""
                yield rx.redirect("/login")
            else:
                self.auth_message = self._parse_error_detail(res)
                self.auth_is_error = True
        except Exception as e:
            self.auth_message = f"Error: {e}"
            self.auth_is_error = True
        self.auth_is_loading = False

    async def logout(self):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{API_BASE}/auth/logout",
                    json={"handle": self.current_user_handle},
                )
        except Exception:
            pass
        self._clear_user_state()
        yield rx.redirect("/login")

    async def forgot_password(self):
        if not self.forgot_handle:
            self.forgot_message = "Please enter your User ID."
            self.forgot_is_error = True
            return
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{API_BASE}/auth/forgot-password",
                    json={"handle": self.forgot_handle},
                )
            self.forgot_message = "If this User ID has an email on file, a reset link has been sent."
            self.forgot_is_error = False
        except Exception as e:
            self.forgot_message = f"Error: {e}"
            self.forgot_is_error = True

    async def reset_password(self):
        if not self.reset_new_password or not self.reset_confirm_password:
            self.reset_message = "Please fill in all fields."
            self.reset_is_error = True
            return
        if self.reset_new_password != self.reset_confirm_password:
            self.reset_message = "Passwords do not match."
            self.reset_is_error = True
            return
        if len(self.reset_new_password) < 6:
            self.reset_message = "Password must be at least 6 characters."
            self.reset_is_error = True
            return
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{API_BASE}/auth/reset-password",
                    json={"token": self.reset_token, "new_password": self.reset_new_password},
                )
            if res.status_code == 200:
                self.reset_message = "Password reset! You can now log in."
                self.reset_is_error = False
                self.reset_is_success = True
            else:
                self.reset_message = res.json().get("detail", "Reset failed.")
                self.reset_is_error = True
        except Exception as e:
            self.reset_message = f"Error: {e}"
            self.reset_is_error = True

    async def _fetch_user_profile(self, handle: str):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{API_BASE}/users/{handle}")
            if res.status_code == 200:
                data = res.json()
                self.current_user_handle = data["handle"]
                self.current_user_name = data["name"]
                self.current_user_email = data.get("email") or ""
                self.current_user_id = data["id"]
                self.current_user_image = data.get("profile_image") or ""
                self.current_user_description = data.get("description") or ""
                self.current_user_theme = data.get("theme", "light")
                self.current_user_handle_changes_left = data.get("handle_changes_left", 0)
                self.task_creator = data["name"]
                self.profile_edit_name = data["name"]
                self.profile_edit_handle = data["handle"]
                self.profile_edit_email = data.get("email") or ""
                self.profile_edit_description = data.get("description") or ""
        except Exception:
            pass

    # ── PROFILE EDIT EVENTS ──────────────────────────────────────────────────

    def set_profile_edit_handle(self, v: str): self.profile_edit_handle = v
    def set_profile_edit_name(self, v: str): self.profile_edit_name = v
    def set_profile_edit_email(self, v: str): self.profile_edit_email = v
    def set_profile_edit_description(self, v: str): self.profile_edit_description = v
    def set_change_pw_current(self, v: str): self.change_pw_current = v
    def set_change_pw_new(self, v: str): self.change_pw_new = v
    def set_change_pw_confirm(self, v: str): self.change_pw_confirm = v

    def open_profile_dialog(self):
        self.profile_dialog_open = True

    def set_profile_dialog_open(self, v: bool):
        self.profile_dialog_open = v
        if not v:
            self.change_pw_message = ""

    def close_profile_dialog(self):
        self.profile_dialog_open = False
        self.change_pw_message = ""

    async def save_profile(self):
        if not self.current_user_handle:
            return
        payload = {
            "name": self.profile_edit_name,
            "description": self.profile_edit_description,
        }
        if self.profile_edit_email.strip():
            payload["email"] = self.profile_edit_email.strip()
        if (
            self.current_user_handle_changes_left > 0
            and self.profile_edit_handle != self.current_user_handle
        ):
            payload["handle"] = self.profile_edit_handle
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API_BASE}/users/{self.current_user_handle}",
                    json=payload,
                )
            if resp.status_code >= 400:
                return rx.toast.error(self._parse_error_detail(resp))
            new_handle = payload.get("handle", self.current_user_handle)
            await self._fetch_user_profile(new_handle)
            return rx.toast.success("Profile updated!")
        except Exception as e:
            return rx.toast.error(str(e))

    async def change_password(self):
        if self.change_pw_new != self.change_pw_confirm:
            self.change_pw_message = "New passwords do not match."
            self.change_pw_is_error = True
            return
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{API_BASE}/users/{self.current_user_handle}/change-password",
                    json={"current_password": self.change_pw_current, "new_password": self.change_pw_new},
                )
            if res.status_code == 200:
                self.change_pw_message = "Password changed!"
                self.change_pw_is_error = False
                self.change_pw_current = ""
                self.change_pw_new = ""
                self.change_pw_confirm = ""
            else:
                self.change_pw_message = res.json().get("detail", "Failed.")
                self.change_pw_is_error = True
        except Exception as e:
            self.change_pw_message = str(e)
            self.change_pw_is_error = True

    # ── TEAM / TASK EVENTS ───────────────────────────────────────────────────

    async def load_teams(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_BASE}/teams",
                    params={"handle": self.current_user_handle},
                )
            if resp.status_code == 200:
                self.teams = resp.json()
        except Exception:
            pass
        self.has_teams = len(self.teams) > 0
        if self.teams:
            ids = {t["id"] for t in self.teams}
            if self.active_team_id not in ids:
                self.active_team_id = self.teams[0]["id"]
        else:
            self.active_team_id = 0

    async def load_members(self):
        if not self.active_team_id:
            self.members = []
            self._sync_supervisor_flag()
            return
        await self._load_members_for_team(self.active_team_id)
        self._sync_supervisor_flag()

    async def _load_members_for_team(self, team_id: int):
        """Load members for a specific team (used when opening tasks from other teams)."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE}/teams/{team_id}/members")
            if resp.status_code == 200:
                self.members = resp.json()
        except Exception:
            pass

    def _sync_supervisor_flag(self):
        self.i_am_supervisor = False
        self.current_member_id = 0
        h = (self.current_user_handle or "").strip().lower()
        if not h:
            return
        for m in self.members:
            if str(m.get("handle", "")).strip().lower() == h:
                self.current_member_id = m.get("id", 0)
                self.current_user_role = m.get("role_name", "member")
                if m.get("role_name") in ("supervisor", "lead"):
                    self.i_am_supervisor = True
                break

    async def load_join_requests(self):
        if not self.active_team_id or not self.i_am_supervisor or not self.current_user_handle:
            self.join_requests = []
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_BASE}/teams/{self.active_team_id}/join-requests",
                    params={"supervisor_handle": self.current_user_handle},
                )
            if resp.status_code == 200:
                self.join_requests = resp.json()
            else:
                self.join_requests = []
        except Exception:
            self.join_requests = []

    async def load_tasks(self):
        params = {"team_id": self.active_team_id} if self.active_team_id else {}
        if self.category_filter and self.category_filter != SELECT_ALL_CATEGORIES:
            params["category"] = self.category_filter
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE}/tasks", params=params)
            if resp.status_code == 200:
                self.tasks = resp.json()
        except Exception:
            pass

    async def load_kanban(self):
        if not self.active_team_id:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE}/tasks/kanban", params={"team_id": self.active_team_id})
            if resp.status_code == 200:
                self.kanban = resp.json()
        except Exception:
            pass

    async def load_activities(self):
        if not self.active_team_id:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE}/planning", params={"team_id": self.active_team_id})
            if resp.status_code == 200:
                self.activities = resp.json()
        except Exception:
            pass

    async def load_performance(self):
        if not self.active_team_id:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE}/planning/performance", params={"team_id": self.active_team_id})
            if resp.status_code == 200:
                self.performance = resp.json()
        except Exception:
            pass

    async def on_category_filter_change(self, category: str):
        self.category_filter = category
        await self.load_tasks()

    async def on_team_selected(self, team_id: str):
        self.active_team_id = int(team_id) if team_id else 0
        await self.load_members()
        await self.load_join_requests()
        await self.load_tasks()
        await self.load_kanban()
        await self.load_activities()
        await self.load_performance()

    def set_team_name(self, v: str): self.team_name = v
    def set_team_description(self, v: str): self.team_description = v
    def set_team_join_code(self, v: str): self.team_join_code = v

    async def create_team(self):
        payload = {
            "name": self.team_name,
            "description": self.team_description,
            "join_code": self.team_join_code,
            "creator_handle": self.current_user_handle,
            "creator_display_name": self.current_user_name,
        }
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_BASE}/teams", json=payload)
        self.team_name = ""
        self.team_description = ""
        self.team_join_code = ""
        await self._refresh_data()

    def set_member_invite_handle(self, v: str): self.member_invite_handle = v
    def set_join_code_input(self, v: str): self.join_code_input = v

    async def join_team_by_code(self):
        if not self.join_code_input.strip():
            return
        if not self.current_user_handle.strip():
            return rx.toast.error("You must be logged in.")
        payload = {
            "handle": self.current_user_handle,
            "display_name": (self.current_user_name or self.current_user_handle).strip() or self.current_user_handle,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE}/teams/join/{self.join_code_input.strip()}", json=payload)
        if resp.status_code == 404:
            return rx.toast.error("Join code not found.")
        elif resp.status_code >= 400:
            return rx.toast.error(self._parse_error_detail(resp))
        self.join_code_input = ""
        await self._refresh_data()
        return rx.toast.success("Request sent. Your supervisor must approve you.")

    async def add_member(self):
        if not self.active_team_id:
            return
        if not self.member_invite_handle.strip():
            return rx.toast.error("Enter the invitee's User ID.")
        payload = {
            "team_id": self.active_team_id,
            "invitee_handle": self.member_invite_handle.strip(),
            "inviter_handle": self.current_user_handle,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE}/teams/members", json=payload)
        if resp.status_code >= 400:
            return rx.toast.error(self._parse_error_detail(resp))
        self.member_invite_handle = ""
        await self._refresh_data()
        return rx.toast.success("Member invited.")

    async def approve_join_request(self, request_id: int):
        if not self.active_team_id:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_BASE}/teams/{self.active_team_id}/join-requests/{request_id}/approve",
                params={"supervisor_handle": self.current_user_handle},
            )
        if resp.status_code >= 400:
            return rx.toast.error(self._parse_error_detail(resp))
        await self._refresh_data()
        return rx.toast.success("Member approved.")

    async def reject_join_request(self, request_id: int):
        if not self.active_team_id:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_BASE}/teams/{self.active_team_id}/join-requests/{request_id}/reject",
                params={"supervisor_handle": self.current_user_handle},
            )
        if resp.status_code >= 400:
            return rx.toast.error(self._parse_error_detail(resp))
        await self._refresh_data()
        return rx.toast.success("Request rejected.")

    async def remove_member(self, member_id: int):
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{API_BASE}/teams/members/{member_id}",
                params={"supervisor_handle": self.current_user_handle},
            )
        if resp.status_code >= 400:
            return rx.toast.error(self._parse_error_detail(resp))
        await self._refresh_data()

    def set_task_name(self, v: str): self.task_name = v
    def set_task_description(self, v: str): self.task_description = v
    def set_task_attachment(self, v: str): self.task_attachment = v
    def set_task_file_rules(self, v: str): self.task_file_rules = v
    def set_task_category(self, v: str): self.task_category = v
    def set_task_creator(self, v: str): self.task_creator = v
    def set_task_deadline(self, v: str): self.task_deadline = v
    def set_task_assignee_choice(self, v: str): self.task_assignee_choice = v

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
            return rx.toast.error("Select a team first.")
        payload = {
            "team_id": self.active_team_id,
            "creator_name": self.task_creator.strip() or self.current_user_name or "unknown",
            "creator_handle": self.current_user_handle,
            "name": self.task_name.strip(),
            "description": self.task_description,
            "attachment_url": self.task_attachment,
            "file_rules": "" if self.task_file_rules in ("", SELECT_NO_FILE_RULES) else self.task_file_rules,
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
            return rx.toast.error(f"Cannot reach API. ({exc})")
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
        await self._refresh_data()
        return rx.toast.success("Task created.")

    def set_activity_title(self, v: str): self.activity_title = v
    def set_activity_start(self, v: str): self.activity_start = v
    def set_activity_end(self, v: str): self.activity_end = v
    def set_activity_category(self, v: str): self.activity_category = v

    async def create_activity(self):
        if not self.active_team_id:
            return rx.toast.error("Select a team first.")
        if not self.activity_start or not self.activity_end:
            return rx.toast.error("Please fill in start and end time.")
        if not self.activity_title.strip():
            return rx.toast.error("Please enter an activity title.")
        payload = {
            "team_id": self.active_team_id,
            "title": self.activity_title.strip(),
            "timeline_start": self._normalize_datetime_local(self.activity_start),
            "timeline_end": self._normalize_datetime_local(self.activity_end),
            "category": self.activity_category,
            "member_handle": self.current_user_handle,
        }
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{API_BASE}/planning", json=payload)
        except Exception as exc:
            return rx.toast.error(f"Cannot reach API. ({exc})")
        if r.status_code >= 400:
            detail = self._parse_error_detail(r)
            return rx.toast.error(f"Failed: {detail}")
        self.activity_title = ""
        self.activity_start = ""
        self.activity_end = ""
        await self._refresh_data()
        return rx.toast.success("Activity added.")

    def on_task_dialog_open_change(self, is_open: bool):
        self.task_dialog_open = is_open
        if not is_open:
            self.detail_task = {}
            self.detail_subtasks = []
            self.detail_logs = []
            self.detail_submissions = []
            self.i_am_detail_assignee = False
            self.detail_assignee_label = "Unassigned"
            self.submit_work_title = ""
            self.submit_work_description = ""
            self.return_reason = ""
            self.new_subtask_title = ""
            self.detail_assignee_value = "none"
            self.detail_title = ""
            self.detail_status_value = "backlog"
            self.detail_grade_locked = False
            self.detail_task_closed = False

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
                self.detail_task_closed = bool(self.detail_task.get("closed", False))
                if self.i_am_supervisor:
                    self.detail_grade_locked = self.detail_task.get("grade") is not None
                else:
                    self.detail_grade_locked = False
                self._sync_detail_assignee_flags()

    def _sync_detail_assignee_flags(self):
        self.i_am_detail_assignee = False
        self.detail_assignee_label = "Unassigned"
        if not self.detail_task:
            return
        aid = self.detail_task.get("assignee_id")
        uh = (self.current_user_handle or "").strip().lower()
        my_mid = None
        for m in self.members:
            h = str(m.get("handle", "")).strip().lower()
            if h == uh:
                my_mid = m.get("id")
                break
        if aid is not None and my_mid is not None and aid == my_mid:
            self.i_am_detail_assignee = True
        if aid is not None:
            for m in self.members:
                if m.get("id") == aid:
                    self.detail_assignee_label = str(
                        m.get("display_name") or m.get("handle") or "—"
                    )
                    break

    async def _reload_subtasks_logs(self, task_id: int):
        async with httpx.AsyncClient() as client:
            sr = await client.get(f"{API_BASE}/tasks/{task_id}/subtasks")
            if sr.status_code == 200:
                self.detail_subtasks = sr.json()
            lr = await client.get(f"{API_BASE}/tasks/{task_id}/logs")
            if lr.status_code == 200:
                self.detail_logs = lr.json()
            subr = await client.get(f"{API_BASE}/tasks/{task_id}/submissions")
            if subr.status_code == 200:
                self.detail_submissions = subr.json()
            else:
                self.detail_submissions = []

    async def open_task(self, task_id: int):
        from pm_app.components.comment import CommentState
        await self._reload_detail_task(task_id)
        if not self.detail_task.get("id"):
            return
        # Ensure members are loaded for the task's team (may differ from active_team_id)
        task_team_id = self.detail_task.get("team_id")
        if task_team_id and task_team_id != self.active_team_id:
            await self._load_members_for_team(task_team_id)
            # Re-sync assignee flags now that correct members are loaded
            self._sync_detail_assignee_flags()
        await self._reload_subtasks_logs(task_id)
        self.return_reason = ""
        self.new_subtask_title = ""
        self.task_dialog_open = True
        yield CommentState.set_user_context(
            self.current_member_id,  # Use TeamMember.id, not User.id
            self.current_user_name,
            self.current_user_role.upper(),  # Use role_name from team_members
        )
        yield CommentState.load_comments(task_id)

    def set_return_reason(self, v: str): self.return_reason = v
    def set_detail_grade(self, v: str): self.detail_grade = v
    def set_new_subtask_title(self, v: str): self.new_subtask_title = v
    def set_submit_work_title(self, v: str): self.submit_work_title = v
    def set_submit_work_description(self, v: str): self.submit_work_description = v

    async def update_detail_status(self, status: str):
        if not self.detail_task:
            return
        if self.detail_task_closed:
            return rx.toast.error("This task is completed.")
        self.detail_status_value = status
        tid = self.detail_task["id"]
        async with httpx.AsyncClient() as client:
            await client.patch(f"{API_BASE}/tasks/{tid}", json={"status": status})
        await self._reload_detail_task(tid)
        await self._refresh_data()

    async def update_detail_assignee(self, choice: str):
        if not self.i_am_supervisor:
            return rx.toast.error("Only the supervisor can change assignee.")
        if self.detail_task_closed:
            return rx.toast.error("This task is completed.")
        if not self.detail_task:
            return
        tid = self.detail_task["id"]
        body = {"assignee_id": None if choice in ("", "none") else int(choice)}
        async with httpx.AsyncClient() as client:
            await client.patch(f"{API_BASE}/tasks/{tid}", json=body)
        await self._reload_detail_task(tid)
        await self._refresh_data()

    def unlock_detail_grade(self):
        if self.detail_task_closed:
            return rx.toast.error("This task is completed.")
        self.detail_grade_locked = False

    async def save_detail_grade(self):
        if not self.i_am_supervisor:
            return rx.toast.error("Only the supervisor can set grades.")
        if self.detail_task_closed:
            return rx.toast.error("This task is completed.")
        if not self.detail_task:
            return
        tid = self.detail_task["id"]
        raw = self.detail_grade.strip()
        if not raw.isdigit():
            body = {"grade": None}
        else:
            g = int(raw)
            if g < 0 or g > 100:
                return rx.toast.error("Grade must be between 0 and 100.")
            body = {"grade": g}
        try:
            async with httpx.AsyncClient() as client:
                r = await client.patch(f"{API_BASE}/tasks/{tid}", json=body)
        except Exception as exc:
            return rx.toast.error(f"Cannot reach API. ({exc})")
        if r.status_code >= 400:
            return rx.toast.error(self._parse_error_detail(r))
        await self._reload_detail_task(tid)
        await self._refresh_data()
        if body.get("grade") is not None:
            self.detail_grade_locked = True
        else:
            self.detail_grade_locked = False
        return rx.toast.success("Grade saved.")

    async def complete_task_and_close(self):
        if not self.i_am_supervisor:
            return rx.toast.error("Only the supervisor can complete this task.")
        if not self.detail_task:
            return
        if self.detail_task_closed:
            return rx.toast.error("This task is already completed.")
        if self.detail_task.get("grade") is None:
            return rx.toast.error("Save a grade before completing this task.")
        tid = int(self.detail_task["id"])
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{API_BASE}/tasks/{tid}/complete",
                    params={"supervisor_handle": self.current_user_handle},
                )
        except Exception as exc:
            return rx.toast.error(f"Cannot reach API. ({exc})")
        if r.status_code >= 400:
            return rx.toast.error(self._parse_error_detail(r))
        self.on_task_dialog_open_change(False)
        await self._refresh_data()
        return rx.toast.success("Task completed and closed.")

    async def submit_return_task(self):
        if not self.i_am_supervisor:
            return rx.toast.error("Only the supervisor can return work.")
        if self.detail_task_closed:
            return rx.toast.error("This task is completed.")
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
        await self._refresh_data()

    async def submit_work(self, files: list[UploadFile]):
        if not self.detail_task:
            return rx.toast.error("No task selected.")
        if self.detail_task.get("closed"):
            return rx.toast.error("This task is completed; submissions are closed.")
        if not self.submit_work_title.strip():
            return rx.toast.error("Please enter a submission title.")
        if not self.i_am_detail_assignee:
            return rx.toast.error("Only the assignee can submit work.")
        tid = int(self.detail_task["id"])
        data = {
            "title": self.submit_work_title.strip(),
            "description": (self.submit_work_description or "").strip(),
            "submitter_handle": self.current_user_handle,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if files:
                    f0 = files[0]
                    body = await f0.read()
                    fname = f0.filename or "upload.bin"
                    ct = getattr(f0, "content_type", None) or "application/octet-stream"
                    r = await client.post(
                        f"{API_BASE}/tasks/{tid}/submissions",
                        data=data,
                        files={"file": (fname, body, ct)},
                    )
                else:
                    r = await client.post(
                        f"{API_BASE}/tasks/{tid}/submissions",
                        data=data,
                    )
        except Exception as exc:
            return rx.toast.error(f"Upload failed: {exc}")
        if r.status_code >= 400:
            return rx.toast.error(self._parse_error_detail(r))
        self.submit_work_title = ""
        self.submit_work_description = ""
        await self._reload_subtasks_logs(tid)
        return [
            rx.clear_selected_files("work_submit"),
            rx.toast.success("Work submitted."),
        ]

    async def add_subtask(self):
        if not self.detail_task or not self.new_subtask_title.strip():
            return
        tid = self.detail_task["id"]
        payload = {"task_id": tid, "title": self.new_subtask_title.strip()}
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_BASE}/tasks/{tid}/subtasks",
                json=payload,
                params={"creator_handle": self.current_user_handle},
            )
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
        await self._refresh_data()

    async def move_task_status(self, task_id: int, new_status: str):
        async with httpx.AsyncClient() as client:
            await client.patch(f"{API_BASE}/tasks/{task_id}", json={"status": new_status})
        if self.detail_task and self.detail_task.get("id") == task_id:
            await self._reload_detail_task(task_id)
        await self._refresh_data()