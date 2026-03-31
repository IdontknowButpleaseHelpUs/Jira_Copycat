"""
pages/task_detail.py  —  example integration

Shows how to drop comment_section() and notification_bell() into a real page.
Your team replaces the dummy CURRENT_TASK / CURRENT_USER with your auth state.
"""

import reflex as rx
from AddOnStuffs.comment import CommentState, comment_section
from AddOnStuffs.Notification import (
    NotificationState,
    notification_bell,
    notification_panel,
    notification_bubble,
)

# ── REPLACE with your AuthState vars ─────────────────────────────────────────
CURRENT_USER_ID = 1
CURRENT_USER_NAME = "Alice"
CURRENT_USER_ROLE = "MEMBER"   # MEMBER | SUPERVISOR | USER
CURRENT_TASK_ID = 42
# ─────────────────────────────────────────────────────────────────────────────


class TaskPageState(rx.State):
    """
    Thin page-level state that bootstraps both modules on load.
    Extend this to hold the actual task data from your TaskService.
    """

    @rx.event
    async def on_load(self):
        # ── 1. inject current user into CommentState ─────────────────────────
        yield CommentState.set_var("current_user_id", CURRENT_USER_ID)
        yield CommentState.set_var("current_user_name", CURRENT_USER_NAME)
        yield CommentState.set_var("current_user_role", CURRENT_USER_ROLE)

        # ── 2. load comments for this task ────────────────────────────────────
        yield CommentState.load_comments(CURRENT_TASK_ID)

        # ── 3. load notifications for current user ────────────────────────────
        yield NotificationState.load_notifications(CURRENT_USER_ID)


# ── nav ───────────────────────────────────────────────────────────────────────

def nav() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text("JiraCopycat", size="3", weight="medium"),
            rx.spacer(),
            # ── bell goes here ────────────────────────────────────────────────
            notification_bell(),
        ),
        padding="12px 20px",
        border_bottom="0.5px solid var(--gray-4)",
        width="100%",
    )


# ── dummy task card (replace with your real task component) ───────────────────

def task_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Fix authentication bug", size="4"),
                rx.badge("IN_PROGRESS", color_scheme="blue"),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.text(
                "Login endpoint returns 500 on special characters in email.",
                size="2",
                color_scheme="gray",
            ),
            spacing="2",
        ),
        width="100%",
    )


# ── page ──────────────────────────────────────────────────────────────────────

def task_detail_page() -> rx.Component:
    return rx.vstack(

        nav(),

        # notification dropdown panel renders right below nav
        notification_panel(),

        # page content
        rx.box(
            rx.vstack(
                task_card(),
                rx.card(
                    comment_section(),
                    width="100%",
                ),
                spacing="4",
                width="100%",
                max_width="720px",
                margin="0 auto",
            ),
            padding="20px",
            width="100%",
        ),

        # floating notification bubble at the bottom
        notification_bubble(),

        spacing="0",
        width="100%",
        on_mount=TaskPageState.on_load,
    )