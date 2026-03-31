import reflex as rx
import httpx

API_BASE = "http://localhost:8000"

# type → radix color scheme
_TYPE_COLOR: dict[str, str] = {
    "DEADLINE": "yellow",
    "TASK_ASSIGNED": "blue",
    "WORK_RETURNED": "red",
    "COMMENT": "green",
}


class NotificationState(rx.State):
    """
    Drop-in state for notifications.
    Works for ALL roles: USER, MEMBER, SUPERVISOR.

    Before rendering, call:
        NotificationState.load_notifications(user_id)
    """

    notifications: list[dict] = []
    panel_open: bool = False
    recipient_id: int = 0

    @rx.var
    def unread_count(self) -> int:
        return sum(1 for n in self.notifications if not n.get("isRead", False))

    @rx.var
    def has_unread(self) -> bool:
        return self.unread_count > 0

    # ── events ────────────────────────────────────────────────────────────────

    @rx.event
    async def load_notifications(self, recipient_id: int):
        self.recipient_id = recipient_id
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_BASE}/notifications/{recipient_id}"
                )
                resp.raise_for_status()
                self.notifications = resp.json()
        except Exception:
            pass  # fail silently — notifications are non-critical

    @rx.event
    async def mark_read(self, notif_id: int):
        try:
            async with httpx.AsyncClient() as client:
                await client.patch(
                    f"{API_BASE}/notifications/{notif_id}/read"
                )
        except Exception:
            pass
        self.notifications = [
            {**n, "isRead": True} if n["notifId"] == notif_id else n
            for n in self.notifications
        ]

    @rx.event
    async def mark_all_read(self):
        try:
            async with httpx.AsyncClient() as client:
                await client.patch(
                    f"{API_BASE}/notifications/read-all",
                    params={"recipientId": self.recipient_id},
                )
        except Exception:
            pass
        self.notifications = [
            {**n, "isRead": True} for n in self.notifications
        ]

    @rx.event
    def toggle_panel(self):
        self.panel_open = not self.panel_open

    @rx.event
    def close_panel(self):
        self.panel_open = False


# ── sub-components ────────────────────────────────────────────────────────────

def _notif_item(notif: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            # unread dot
            rx.cond(
                ~notif["isRead"],
                rx.box(
                    width="7px",
                    height="7px",
                    min_width="7px",
                    border_radius="50%",
                    background="var(--blue-9)",
                    margin_top="5px",
                ),
                rx.box(width="7px", min_width="7px"),
            ),
            rx.vstack(
                rx.text(notif["notifTitle"], size="2", weight="medium"),
                rx.text(notif["message"], size="1", color_scheme="gray"),
                rx.hstack(
                    rx.badge(
                        notif["type"],
                        size="1",
                        variant="surface",
                        radius="full",
                    ),
                    rx.text(
                        notif["createdAt"], size="1", color_scheme="gray"
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="1",
                align="start",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        on_click=NotificationState.mark_read(notif["notifId"]),
        padding="8px 12px",
        cursor="pointer",
        border_left=rx.cond(
            ~notif["isRead"],
            "2px solid var(--blue-9)",
            "2px solid transparent",
        ),
        _hover={"background": "var(--gray-2)"},
        width="100%",
    )


def notification_panel() -> rx.Component:
    return rx.cond(
        NotificationState.panel_open,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text("Notifications", size="2", weight="medium"),
                    rx.button(
                        "Mark all read",
                        on_click=NotificationState.mark_all_read,
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                rx.separator(width="100%"),
                rx.cond(
                    NotificationState.notifications.length() == 0,
                    rx.center(
                        rx.text("No notifications", size="2", color_scheme="gray"),
                        padding_y="6",
                        width="100%",
                    ),
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(
                                NotificationState.notifications,
                                _notif_item,
                            ),
                            spacing="0",
                            width="100%",
                        ),
                        max_height="260px",
                        width="100%",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            width="320px",
            padding="0",
            overflow="hidden",
            position="fixed",
            top="52px",        
            right="16px",
            z_index="100",
        ),
        rx.fragment(),
    )


def notification_bell() -> rx.Component:
    """
    Nav bar bell icon with red badge.
    Place inside your nav rx.hstack.
    Pair with notification_panel() rendered below the nav.
    """
    return rx.box(
        rx.button(
            rx.hstack(
                rx.icon("bell", size=16),
                rx.cond(
                    NotificationState.has_unread,
                    rx.badge(
                        NotificationState.unread_count,
                        color_scheme="red",
                        variant="solid",
                        size="1",
                        radius="full",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align="center",
            ),
            on_click=NotificationState.toggle_panel,
            variant="ghost",
            size="2",
        ),
        position="relative",
    )


def notification_bubble() -> rx.Component:
    return rx.box(
        rx.button(
            rx.hstack(
                rx.cond(
                    NotificationState.has_unread,
                    rx.box(
                        width="7px",
                        height="7px",
                        border_radius="50%",
                        background="#E24B4A",
                        min_width="7px",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    NotificationState.has_unread,
                    rx.text(
                        NotificationState.unread_count.to_string() + " new notification",
                        size="2",
                    ),
                    rx.text("Notifications", size="2"),
                ),
                spacing="2",
                align="center",
            ),
            on_click=NotificationState.toggle_panel,
            variant="outline",
            border_radius="9999px",
        ),
        
        position="fixed",
        bottom="24px",
        right="24px",
        z_index="99",
    )