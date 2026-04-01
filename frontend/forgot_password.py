import reflex as rx
import httpx


class ForgotPasswordState(rx.State):
    email: str = ""
    message: str = ""
    is_loading: bool = False
    is_error: bool = False

    async def submit(self):
        if not self.email:
            self.message = "Please enter your email."
            self.is_error = True
            return

        self.is_loading = True
        self.message = ""
        yield
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8001/auth/forgot-password",
                    json={"email": self.email},
                )
            self.message = "If this email is registered, a reset link has been sent."
            self.is_error = False
        except Exception as e:
            self.message = f"Error: {str(e)}"
            self.is_error = True
        self.is_loading = False


def forgot_password_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Forgot Password", size="6", color="#2563eb"),
                rx.text(
                    "Enter your email and we'll send you a reset link.",
                    color="#6b7280",
                    size="2",
                ),
                rx.input(
                    placeholder="Email address",
                    type="email",
                    value=ForgotPasswordState.email,
                    on_change=ForgotPasswordState.set_email,
                    width="100%",
                ),
                rx.cond(
                    ForgotPasswordState.message != "",
                    rx.text(
                        ForgotPasswordState.message,
                        color=rx.cond(ForgotPasswordState.is_error, "#dc2626", "#16a34a"),
                        size="2",
                    ),
                ),
                rx.button(
                    rx.cond(ForgotPasswordState.is_loading, "Sending...", "Send Reset Link"),
                    on_click=ForgotPasswordState.submit,
                    loading=ForgotPasswordState.is_loading,
                    width="100%",
                    background_color="#2563eb",
                    color="white",
                    cursor="pointer",
                ),
                rx.link("Back to Login", href="/login", color="#2563eb", size="2"),
                spacing="4",
                width="100%",
            ),
            width="400px",
            padding="2em",
        ),
        height="100vh",
        background_color="#f1f5f9",
    )