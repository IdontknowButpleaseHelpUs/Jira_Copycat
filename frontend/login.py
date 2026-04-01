import reflex as rx
import httpx


class LoginState(rx.State):
    email: str = ""
    password: str = ""
    message: str = ""
    is_loading: bool = False
    is_error: bool = False

    async def submit(self):
        if not self.email or not self.password:
            self.message = "Please fill in all fields."
            self.is_error = True
            return

        self.is_loading = True
        self.message = ""
        yield
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "http://localhost:8001/auth/login",
                    json={
                        "email": self.email,
                        "password": self.password,
                    },
                )
            if res.status_code == 200:
                self.message = "Login successful! Redirecting..."
                self.is_error = False
                yield rx.redirect("/dashboard")
            else:
                self.message = res.json().get("detail", "Login failed.")
                self.is_error = True
        except Exception as e:
            self.message = f"Error: {str(e)}"
            self.is_error = True
        self.is_loading = False


def login_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Welcome Back", size="6", color="#2563eb"),
                rx.text("Sign in to your account.", color="#6b7280", size="2"),
                rx.input(
                    placeholder="Email address",
                    type="email",
                    value=LoginState.email,
                    on_change=LoginState.set_email,
                    width="100%",
                ),
                rx.input(
                    placeholder="Password",
                    type="password",
                    value=LoginState.password,
                    on_change=LoginState.set_password,
                    width="100%",
                ),
                rx.link(
                    "Forgot password?",
                    href="/forgot-password",
                    color="#2563eb",
                    size="2",
                ),
                rx.cond(
                    LoginState.message != "",
                    rx.text(
                        LoginState.message,
                        color=rx.cond(LoginState.is_error, "#dc2626", "#16a34a"),
                        size="2",
                    ),
                ),
                rx.button(
                    rx.cond(LoginState.is_loading, "Signing in...", "Login"),
                    on_click=LoginState.submit,
                    loading=LoginState.is_loading,
                    width="100%",
                    background_color="#2563eb",
                    color="white",
                    cursor="pointer",
                ),
                rx.hstack(
                    rx.text("Don't have an account?", color="#6b7280", size="2"),
                    rx.link("Register", href="/register", color="#2563eb", size="2"),
                    spacing="1",
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