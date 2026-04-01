import reflex as rx
from .register import register_page, RegisterState
from .login import login_page, LoginState
from .forgot_password import forgot_password_page, ForgotPasswordState
from .reset_password import reset_password_page, ResetPasswordState


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Welcome", size="6", color="#2563eb"),
            rx.link("Login", href="/login", color="#2563eb"),
            rx.link("Register", href="/register", color="#2563eb"),
            spacing="4",
        ),
        height="100vh",
        background_color="#f1f5f9",
    )


app = rx.App()
app.add_page(index, route="/")
app.add_page(login_page, route="/login")
app.add_page(register_page, route="/register")
app.add_page(forgot_password_page, route="/forgot-password")
app.add_page(
    reset_password_page,
    route="/reset-password/[token]",
    on_load=ResetPasswordState.on_load,
)