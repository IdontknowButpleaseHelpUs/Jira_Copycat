import reflex as rx

from . import pages
from .state import AppState

app = rx.App(
    theme=rx.theme(
        accent_color="indigo",
        gray_color="slate",
        radius="medium",
    ),
)

app.add_page(pages.dashboard, route="/", title="FlowBoard", on_load=AppState.refresh_all)
app.add_page(pages.login_page, route="/login", title="Login")
app.add_page(pages.register_page, route="/register", title="Register")
app.add_page(pages.forgot_password_page, route="/forgot-password", title="Forgot Password")
app.add_page(
    pages.reset_password_page,
    route="/reset-password/[token]",
    title="Reset Password",
    on_load=AppState.on_reset_load,
)
