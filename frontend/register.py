import reflex as rx
import httpx


class RegisterState(rx.State):
    email: str = ""
    name: str = ""
    password: str = ""
    message: str = ""
    is_loading: bool = False
    is_error: bool = False

    async def submit(self):
        if not self.email or not self.name or not self.password:
            self.message = "Please fill in all fields."
            self.is_error = True
            return
        if len(self.password) < 6:
            self.message = "Password must be at least 6 characters."
            self.is_error = True
            return

        self.is_loading = True
        self.message = ""
        yield
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "http://localhost:8001/auth/register",
                    json={
                        "email": self.email,
                        "name": self.name,
                        "password": self.password,
                    },
                )
            if res.status_code == 201:
                self.message = "Account created! Redirecting to login..."
                self.is_error = False
                yield rx.redirect("/login")
            else:
                self.message = res.json().get("detail", "Registration failed.")
                self.is_error = True
        except Exception as e:
            self.message = f"Error: {str(e)}"
            self.is_error = True
        self.is_loading = False


def register_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Create Account", size="6", color="#2563eb"),
                rx.text("Join us today.", color="#6b7280", size="2"),
                rx.input(
                    placeholder="Username",
                    value=RegisterState.name,
                    on_change=RegisterState.set_name,
                    width="100%",
                ),
                rx.input(
                    placeholder="Email address",
                    type="email",
                    value=RegisterState.email,
                    on_change=RegisterState.set_email,
                    width="100%",
                ),
                rx.input(
                    placeholder="Password",
                    type="password",
                    value=RegisterState.password,
                    on_change=RegisterState.set_password,
                    width="100%",
                ),
                rx.cond(
                    RegisterState.message != "",
                    rx.text(
                        RegisterState.message,
                        color=rx.cond(RegisterState.is_error, "#dc2626", "#16a34a"),
                        size="2",
                    ),
                ),
                rx.button(
                    rx.cond(RegisterState.is_loading, "Creating account...", "Register"),
                    on_click=RegisterState.submit,
                    loading=RegisterState.is_loading,
                    width="100%",
                    background_color="#2563eb",
                    color="white",
                    cursor="pointer",
                ),
                rx.hstack(
                    rx.text("Already have an account?", color="#6b7280", size="2"),
                    rx.link("Login", href="/login", color="#2563eb", size="2"),
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