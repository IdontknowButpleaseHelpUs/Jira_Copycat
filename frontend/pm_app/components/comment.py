import httpx
import reflex as rx
from typing import List

API_BASE = "http://127.0.0.1:8001"


def _get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif parts and parts[0]:
        return parts[0][:2].upper()
    return "?"


def _fmt_date(iso: str) -> str:
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%b %d, %Y · %H:%M")
    except Exception:
        return iso


def _enrich(comment: dict) -> dict:
    return {
        **comment,
        "initials": _get_initials(comment.get("author_name", "?")),
        "displayDate": _fmt_date(comment.get("created_at", "")),
    }


class CommentState(rx.State):
    comments: List[dict] = []
    new_comment: str = ""
    is_loading: bool = False
    error_msg: str = ""
    task_id: int = 0
    current_user_id: int = 0
    current_user_name: str = ""
    current_user_role: str = "MEMBER"

    @rx.var
    def can_comment(self) -> bool:
        return self.current_user_role in ("MEMBER", "SUPERVISOR", "member", "lead", "reviewer", "developer", "designer", "pm")

    @rx.var
    def comment_count(self) -> int:
        return len(self.comments)

    @rx.event
    async def load_comments(self, task_id: int):
        self.task_id = task_id
        self.is_loading = True
        self.error_msg = ""
        yield
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE}/tasks/{task_id}/comments")
                resp.raise_for_status()
                self.comments = [_enrich(c) for c in resp.json()]
        except Exception as e:
            self.error_msg = f"Could not load comments: {e}"
        finally:
            self.is_loading = False

    @rx.event
    async def post_comment(self):
        if not self.new_comment.strip() or not self.current_user_id:
            return
        content = self.new_comment.strip()
        self.new_comment = ""
        yield
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_BASE}/tasks/{self.task_id}/comments",
                    json={
                        "author_id": self.current_user_id,
                        "author_role": self.current_user_role,
                        "content": content,
                    },
                )
                resp.raise_for_status()
                self.comments = self.comments + [_enrich(resp.json())]
        except Exception as e:
            self.error_msg = f"Could not post comment: {e}"
            self.new_comment = content

    @rx.event
    def set_new_comment(self, value: str):
        self.new_comment = value

    @rx.event
    def set_user_context(self, user_id: int, user_name: str, user_role: str):
        self.current_user_id = user_id
        self.current_user_name = user_name
        self.current_user_role = user_role

    @rx.event
    def clear_error(self):
        self.error_msg = ""

    @rx.event
    def clear_comments(self):
        self.comments = []
        self.new_comment = ""
        self.task_id = 0


def _avatar(initials: str, role: str) -> rx.Component:
    return rx.box(
        rx.text(initials, size="1", weight="bold"),
        width="32px",
        height="32px",
        min_width="32px",
        border_radius="50%",
        display="flex",
        align_items="center",
        justify_content="center",
        background=rx.cond(role == "SUPERVISOR", "var(--yellow-3)", "var(--blue-3)"),
        color=rx.cond(role == "SUPERVISOR", "var(--yellow-11)", "var(--blue-11)"),
        font_size="11px",
        letter_spacing="0.5px",
    )


def _comment_item(comment: dict) -> rx.Component:
    return rx.hstack(
        _avatar(comment["initials"], comment["author_role"]),
        rx.vstack(
            rx.hstack(
                rx.text(comment["author_name"], size="2", weight="medium"),
                rx.badge(comment["author_role"], variant="surface", size="1", radius="full"),
                spacing="2",
                align="center",
                wrap="wrap",
            ),
            rx.text(comment["content"], size="2"),
            rx.text(comment["displayDate"], size="1", color_scheme="gray"),
            spacing="1",
            align="start",
            width="100%",
        ),
        spacing="3",
        align="start",
        width="100%",
    )


def comment_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Comments", size="2", weight="medium"),
            rx.badge(CommentState.comment_count, variant="surface", size="1"),
            spacing="2",
            align="center",
        ),
        rx.separator(width="100%"),
        rx.cond(
            CommentState.error_msg != "",
            rx.callout(
                CommentState.error_msg,
                color_scheme="red",
                size="1",
                width="100%",
                on_click=CommentState.clear_error,
                cursor="pointer",
            ),
            rx.fragment(),
        ),
        rx.cond(
            CommentState.is_loading,
            rx.center(rx.spinner(size="2"), width="100%", padding_y="4"),
            rx.fragment(),
        ),
        rx.vstack(
            rx.foreach(CommentState.comments.to(List[dict]), _comment_item),
            spacing="4",
            width="100%",
        ),
        rx.separator(width="100%"),
        rx.cond(
            CommentState.can_comment,
            rx.vstack(
                rx.text_area(
                    placeholder="Add a comment...",
                    value=CommentState.new_comment,
                    on_change=CommentState.set_new_comment,
                    width="100%",
                    min_height="64px",
                    resize="vertical",
                ),
                rx.hstack(
                    rx.text(
                        "Posting as " + CommentState.current_user_name,
                        size="1",
                        color_scheme="gray",
                    ),
                    rx.button(
                        "Post comment",
                        on_click=CommentState.post_comment,
                        size="2",
                        variant="outline",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.callout(
                "Log in to comment.",
                variant="surface",
                color_scheme="gray",
                size="1",
                width="100%",
            ),
        ),
        spacing="4",
        width="100%",
    )