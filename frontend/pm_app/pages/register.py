import reflex as rx
from pm_app.state import AppState


def register_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Create Account", size="6", color="var(--indigo-9)"),
                rx.text("Join FlowBoard today.", color="gray", size="2"),
                rx.input(
                    placeholder="Display name *",
                    value=AppState.auth_name,
                    on_change=AppState.set_auth_name,
                    width="100%",
                    size="3",
                ),
                rx.input(
                    placeholder="User ID * (unique, e.g. john_42)",
                    value=AppState.auth_handle,
                    on_change=AppState.set_auth_handle,
                    width="100%",
                    size="3",
                ),
                rx.input(
                    placeholder="Email (optional — needed for password reset)",
                    type="email",
                    value=AppState.auth_email,
                    on_change=AppState.set_auth_email,
                    width="100%",
                    size="3",
                ),
                rx.input(
                    placeholder="Password * (min 6 chars)",
                    type="password",
                    value=AppState.auth_password,
                    on_change=AppState.set_auth_password,
                    width="100%",
                    size="3",
                ),
                rx.input(
                    placeholder="Confirm password *",
                    type="password",
                    value=AppState.auth_confirm_password,
                    on_change=AppState.set_auth_confirm_password,
                    width="100%",
                    size="3",
                ),
                rx.cond(
                    AppState.auth_message != "",
                    rx.text(
                        AppState.auth_message,
                        color=rx.cond(AppState.auth_is_error, "var(--red-9)", "var(--green-9)"),
                        size="2",
                    ),
                ),
                rx.button(
                    rx.cond(AppState.auth_is_loading, "Creating...", "Register"),
                    on_click=AppState.register,
                    loading=AppState.auth_is_loading,
                    width="100%",
                    size="3",
                    color_scheme="indigo",
                ),
                rx.hstack(
                    rx.text("Already have an account?", color="gray", size="2"),
                    rx.link("Login", href="/login", color="var(--indigo-9)", size="2"),
                    spacing="1",
                ),
                spacing="4",
                width="100%",
            ),
            width="420px",
            padding="2em",
        ),
        height="100vh",
        background="var(--gray-2)",
    )