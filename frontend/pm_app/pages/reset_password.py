import reflex as rx
from pm_app.state import AppState


def reset_password_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Reset Password", size="6", color="var(--indigo-9)"),
                rx.text("Enter your new password below.", color="gray", size="2"),
                rx.cond(
                    ~AppState.reset_is_success,
                    rx.vstack(
                        rx.input(
                            placeholder="New password",
                            type="password",
                            value=AppState.reset_new_password,
                            on_change=AppState.set_reset_new_password,
                            width="100%",
                            size="3",
                        ),
                        rx.input(
                            placeholder="Confirm new password",
                            type="password",
                            value=AppState.reset_confirm_password,
                            on_change=AppState.set_reset_confirm_password,
                            width="100%",
                            size="3",
                        ),
                        rx.button(
                            "Reset Password",
                            on_click=AppState.reset_password,
                            width="100%",
                            size="3",
                            color_scheme="indigo",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                ),
                rx.cond(
                    AppState.reset_message != "",
                    rx.text(
                        AppState.reset_message,
                        color=rx.cond(AppState.reset_is_error, "var(--red-9)", "var(--green-9)"),
                        size="2",
                    ),
                ),
                rx.cond(
                    AppState.reset_is_success,
                    rx.link("Go to Login", href="/login", color="var(--indigo-9)", size="2"),
                ),
                spacing="4",
                width="100%",
            ),
            width="400px",
            padding="2em",
        ),
        height="100vh",
        background="var(--gray-2)",
    )