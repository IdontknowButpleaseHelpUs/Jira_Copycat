import reflex as rx
import httpx
from typing import Dict, List, TypedDict

# ── swap this to an env var in production ────────────────────────────────────
API_BASE = "http://localhost:8001"

# ── helpers ───────────────────────────────────────────────────────────────────

def _get_initials(name: str) -> str:
    """Return 1-2 char initials from a display name."""
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif parts and parts[0]:
        return parts[0][:2].upper()
    return "?"


def _fmt_date(iso: str) -> str:
    """Turn ISO datetime string → 'Jan 15, 2024 · 10:30'."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%b %d, %Y · %H:%M")
    except Exception:
        return iso


def _enrich(comment: dict) -> dict:
    """Attach pre-computed display fields so Reflex Vars don't have to."""
    return {
        **comment,
        "initials": _get_initials(comment.get("authorName", "?")),
        "displayDate": _fmt_date(comment.get("createdAt", "")),
    }

class Comment(TypedDict):
    id: int
    authorId: int
    authorName: str
    authorRole: str
    content: str
    createdAt: str


class CommentState(rx.State):
    """
    Drop-in state for the comment section.
    Before rendering, call:  CommentState.load_comments(task_id)
    Set current_user_* from your auth state before mounting.
    """

    comments: List[dict] = []
    new_comment: str = ""
    is_loading: bool = False
    error_msg: str = ""
    task_id: int = 0

    # ── inject these from your AuthState ─────────────────────────────────────
    current_user_id: int = 4  # Demo user ID
    current_user_name: str = "Demo User"  # Demo user name
    current_user_role: str = "MEMBER"  # MEMBER | SUPERVISOR | USER

    @rx.var 
    def can_comment(self) -> bool:
        return self.current_user_role in ("MEMBER", "SUPERVISOR")

    @rx.var
    def comment_count(self) -> int:
        return len(self.comments)

    # ── events ────────────────────────────────────────────────────────────────

    @rx.event
    async def load_comments(self, task_id: int):
        self.task_id = task_id
        self.is_loading = True
        self.error_msg = ""
        yield
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_BASE}/tasks/{task_id}/comments"
                )
                resp.raise_for_status()
                self.comments = [_enrich(c) for c in resp.json()] # Added _enrinch function from fn helper
        except Exception as e:
            self.error_msg = f"Could not load comments: {e}"
        finally:
            self.is_loading = False

    @rx.event
    async def post_comment(self):
        if not self.new_comment.strip():
            return
        if not self.can_comment:
            return

        content = self.new_comment.strip()
        self.new_comment = ""
        yield

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_BASE}/tasks/{self.task_id}/comments",
                    json={
                        "authorId": self.current_user_id,
                        "authorRole": self.current_user_role,
                        "content": content,
                    },
                )
                resp.raise_for_status()
                self.comments = self.comments + [_enrich(resp.json())]  # Added _enrinch function from fn helper
        except Exception as e:
            self.error_msg = f"Could not post comment: {e}"
            self.new_comment = content

    @rx.event
    def set_new_comment(self, value: str):
        self.new_comment = value

    @rx.event
    def set_var(self, field: str, value):
        """Dynamically set a state variable. Used for injecting user data."""
        if hasattr(self, field):
            setattr(self, field, value)

    @rx.event
    def clear_error(self):
        self.error_msg = ""


# ── sub-components ────────────────────────────────────────────────────────────

def _avatar(initials: str, role: str) -> rx.Component:
    return rx.box(
        rx.text(
            initials,
            size="1",
            weight="bold",
        ),
        width="32px",
        height="32px",
        min_width="32px",
        border_radius="50%",
        display="flex",
        align_items="center",
        justify_content="center",
        background=rx.cond(
            role == "SUPERVISOR", "var(--yellow-3)", "var(--blue-3)"
        ),
        color=rx.cond(
            role == "SUPERVISOR", "var(--yellow-11)", "var(--blue-11)"
        ),
        font_size="11px",
        letter_spacing="0.5px",
    )


def _comment_item(comment: dict) -> rx.Component:
    return rx.hstack(
        _avatar(comment["initials"], comment["authorRole"]),
        rx.vstack(
            rx.hstack(
                rx.text(comment["authorName"], size="2", weight="medium"),
                rx.badge(
                    comment["authorRole"],
                    variant="surface",
                    size="1",
                    radius="full",
                ),
                spacing="2",
                align="center",
                wrap="wrap",
            ),
            rx.text(comment["content"], size="2"),
            rx.text(
                comment["displayDate"],   # 👈 formatted, not raw ISO
                size="1",
                color_scheme="gray",
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        spacing="3",
        align="start",
        width="100%",
    )


def comment_section() -> rx.Component:
    """
    Usage:
        # in your page/component:
        rx.box(
            comment_section(),
            on_mount=CommentState.load_comments(task_id),
        )
    """
    return rx.vstack(
        # ── comment count header ──────────────────────────────────────────────
        rx.hstack(
            rx.text("Comments", size="2", weight="medium"),
            rx.badge(
                CommentState.comment_count,
                variant="surface",
                size="1",
            ),
            spacing="2",
            align="center",
        ),

        rx.separator(width="100%"),

        # ── error banner ──────────────────────────────────────────────────────
        rx.cond(
            CommentState.error_msg != "",
            rx.callout(
                CommentState.error_msg,
                icon="triangle_alert",
                color_scheme="red",
                size="1",
                width="100%",
                on_click=CommentState.clear_error,
                cursor="pointer",
            ),
            rx.fragment(),
        ),

        # ── loading spinner ───────────────────────────────────────────────────
        rx.cond(
            CommentState.is_loading,
            rx.center(rx.spinner(size="2"), width="100%", padding_y="4"),
            rx.fragment(),
        ),

        # ── comment list ──────────────────────────────────────────────────────
        rx.vstack(
            rx.foreach(CommentState.comments.to(List[dict]), _comment_item),
            spacing="4",
            width="100%",
        ),

        rx.separator(width="100%"),

        # ── input area ────────────────────────────────────────────────────────
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
                        disabled=CommentState.new_comment.strip() == "",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            # ── USER role: blocked ────────────────────────────────────────────
            rx.callout(
                "Commenting is available to Members and Supervisors only.",
                icon="lock",
                variant="surface",
                color_scheme="gray",
                size="1",
                width="100%",
            ),
        ),

        spacing="4",
        width="100%",
    )