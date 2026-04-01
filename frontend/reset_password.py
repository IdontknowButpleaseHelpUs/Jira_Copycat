import reflex as rx
import httpx


class ResetPasswordState(rx.State):
    reset_token: str = ""
    new_password: str = ""
    confirm_password: str = ""
    message: str = ""
    is_loading: bool = False
    is_error: bool = False
    is_success: bool = False

    def on_load(self):
        print("PARAMS:", self.router.page.params)
        token = self.router.page.params.get("token", "")
        self.reset_token = token
        if not token:
            self.message = "Invalid or missing reset token."
            self.is_error = True
    async def submit(self):
        if not self.new_password or not self.confirm_password:
            self.message = "Please fill in all fields."
            self.is_error = True
            return
        if self.new_password != self.confirm_password:
            self.message = "Passwords do not match."
            self.is_error = True
            return
        if len(self.new_password) < 6:
            self.message = "Password must be at least 6 characters."
            self.is_error = True
            return

        self.is_loading = True
        self.message = ""
        yield
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "http://localhost:8001/auth/reset-password",
                    json={
                        "token": self.reset_token,
                        "new_password": self.new_password,
                    },
                )
            if res.status_code == 200:
                self.message = "Password reset successfully! You can now log in."
                self.is_error = False
                self.is_success = True
            else:
                self.message = res.json().get("detail", "Reset failed. Link may have expired.")
                self.is_error = True
        except Exception as e:
            self.message = f"Error: {str(e)}"
            self.is_error = True
        self.is_loading = False


def reset_password_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Reset Password", size="6", color="#2563eb"),
                rx.text(
                    "Enter your new password below.",
                    color="#6b7280",
                    size="2",
                ),
                rx.cond(
                    ~ResetPasswordState.is_success,
                    rx.vstack(
                        rx.input(
                            placeholder="New password",
                            type="password",
                            value=ResetPasswordState.new_password,
                            on_change=ResetPasswordState.set_new_password,
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Confirm new password",
                            type="password",
                            value=ResetPasswordState.confirm_password,
                            on_change=ResetPasswordState.set_confirm_password,
                            width="100%",
                        ),
                        rx.button(
                            rx.cond(
                                ResetPasswordState.is_loading,
                                "Resetting...",
                                "Reset Password",
                            ),
                            on_click=ResetPasswordState.submit,
                            loading=ResetPasswordState.is_loading,
                            width="100%",
                            background_color="#2563eb",
                            color="white",
                            cursor="pointer",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                ),
                rx.cond(
                    ResetPasswordState.message != "",
                    rx.text(
                        ResetPasswordState.message,
                        color=rx.cond(
                            ResetPasswordState.is_error, "#dc2626", "#16a34a"
                        ),
                        size="2",
                    ),
                ),
                rx.cond(
                    ResetPasswordState.is_success,
                    rx.link("Go to Login", href="/login", color="#2563eb", size="2"),
                ),
                spacing="4",
                width="100%",
            ),
            width="400px",
            padding="2em",
        ),
        height="100vh",
        background_color="#f1f5f9",
    )