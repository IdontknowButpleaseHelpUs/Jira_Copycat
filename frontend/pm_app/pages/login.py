import reflex as rx
from pm_app.state import AppState


def login_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Welcome Back", size="6", color="var(--indigo-9)"),
                rx.text("Sign in with your User ID.", color="gray", size="2"),
                rx.input(
                    placeholder="User ID",
                    type="text",
                    value=AppState.auth_handle,
                    on_change=AppState.set_auth_handle,
                    width="100%",
                    size="3",
                ),
                rx.input(
                    placeholder="Password",
                    type="password",
                    value=AppState.auth_password,
                    on_change=AppState.set_auth_password,
                    width="100%",
                    size="3",
                ),
                rx.link("Forgot password?", href="/forgot-password", color="var(--indigo-9)", size="2"),
                rx.cond(
                    AppState.auth_message != "",
                    rx.text(
                        AppState.auth_message,
                        color=rx.cond(AppState.auth_is_error, "var(--red-9)", "var(--green-9)"),
                        size="2",
                    ),
                ),
                rx.button(
                    rx.cond(AppState.auth_is_loading, "Signing in...", "Login"),
                    on_click=AppState.login,
                    loading=AppState.auth_is_loading,
                    width="100%",
                    size="3",
                    color_scheme="indigo",
                ),
                rx.hstack(
                    rx.text("No account?", color="gray", size="2"),
                    rx.link("Register", href="/register", color="var(--indigo-9)", size="2"),
                    spacing="1",
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