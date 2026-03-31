"""Task Details Demo with Comments and Notifications."""

import reflex as rx

from AddOnStuffs.TaskDetails import task_detail_page


class State(rx.State):
    """The app state."""


def index() -> rx.Component:
    return task_detail_page()


app = rx.App()
app.add_page(index)
