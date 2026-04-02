import httpx
import reflex as rx

API_BASE = "http://127.0.0.1:8001"


class NotificationState(rx.State):
    notifications: list[dict] = []
    panel_open: bool = False
    recipient_id: int = 0

    @rx.var
    def unread_count(self) -> int:
        return sum(1 for n in self.notifications if not n.get("isRead", False))

    @rx.var
    def has_unread(self) -> bool:
        return self.unread_count > 0

    @rx.event
    async def load_notifications(self, recipient_id: int):
        self.recipient_id = recipient_id
        if not recipient_id:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE}/notifications/{recipient_id}")
                resp.raise_for_status()
                self.notifications = resp.json()
        except Exception:
            pass

    @rx.event
    async def mark_read(self, notif_id: int):
        try:
            async with httpx.AsyncClient() as client:
                await client.patch(f"{API_BASE}/notifications/{notif_id}/read")
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
                    params={"recipient_id": self.recipient_id},
                )
        except Exception:
            pass
        self.notifications = [{**n, "isRead": True} for n in self.notifications]

    @rx.event
    def toggle_panel(self):
        self.panel_open = not self.panel_open

    @rx.event
    def close_panel(self):
        self.panel_open = False


def _notif_item(notif: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.cond(
                ~notif["isRead"],
                rx.box(
                    width="7px", height="7px", min_width="7px",
                    border_radius="50%", background="var(--blue-9)", margin_top="5px",
                ),
                rx.box(width="7px", min_width="7px"),
            ),
            rx.vstack(
                rx.text(notif["notifTitle"], size="2", weight="medium"),
                rx.text(notif["message"], size="1", color_scheme="gray"),
                rx.hstack(
                    rx.badge(notif["type"], size="1", variant="surface", radius="full"),
                    rx.text(notif["createdAt"], size="1", color_scheme="gray"),
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
        border_left=rx.cond(~notif["isRead"], "2px solid var(--blue-9)", "2px solid transparent"),
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
                            rx.foreach(NotificationState.notifications, _notif_item),
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
            top="68px",
            right="16px",
            z_index="100",
        ),
        rx.fragment(),
    )


def notification_bell() -> rx.Component:
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