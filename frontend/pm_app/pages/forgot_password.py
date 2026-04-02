import reflex as rx
from pm_app.state import AppState


def forgot_password_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Forgot Password", size="6", color="var(--indigo-9)"),
                rx.text(
                    "Enter your User ID. If you have an email on file, we'll send a reset link.",
                    color="gray",
                    size="2",
                ),
                rx.input(
                    placeholder="User ID",
                    type="text",
                    value=AppState.forgot_handle,
                    on_change=AppState.set_forgot_handle,
                    width="100%",
                    size="3",
                ),
                rx.cond(
                    AppState.forgot_message != "",
                    rx.text(
                        AppState.forgot_message,
                        color=rx.cond(AppState.forgot_is_error, "var(--red-9)", "var(--green-9)"),
                        size="2",
                    ),
                ),
                rx.button(
                    "Send Reset Link",
                    on_click=AppState.forgot_password,
                    width="100%",
                    size="3",
                    color_scheme="indigo",
                ),
                rx.link("Back to Login", href="/login", color="var(--indigo-9)", size="2"),
                spacing="4",
                width="100%",
            ),
            width="400px",
            padding="2em",
        ),
        height="100vh",
        background="var(--gray-2)",
    )