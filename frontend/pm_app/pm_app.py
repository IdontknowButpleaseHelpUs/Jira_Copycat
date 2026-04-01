import reflex as rx

from pm_app import pages
from pm_app.state import AppState

app = rx.App(
    theme=rx.theme(
        accent_color="indigo",
        gray_color="slate",
        radius="medium",
    ),
)
app.add_page(pages.dashboard, route="/", title="Project Management", on_load=AppState.refresh_all)
