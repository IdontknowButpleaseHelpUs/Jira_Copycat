import reflex as rx
from pm_app.components.comment import comment_section
from pm_app.components.notification import notification_bell, notification_panel

from pm_app.constants import (
    ACTIVITY_CATEGORIES,
    FILE_RULE_PRESETS,
    SELECT_ALL_CATEGORIES,
    TASK_CATEGORIES,
)
from pm_app.state import AppState

_COL_GAP = "1.25rem"
_PAGE_PAD = "1.5rem"


def _page_heading(title: str, subtitle: str) -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="7", weight="bold", style={"letter_spacing": "-0.02em"}),
        rx.text(subtitle, size="3", color="gray"),
        spacing="1",
        align_items="start",
    )


def _toolbar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.box(
                rx.icon("layers", size=22, color="var(--indigo-9)"),
                padding="0.5rem",
                border_radius="8px",
                background="var(--indigo-3)",
            ),
            _page_heading("FlowBoard", "Kanban, teams, and delivery in one workspace."),
            spacing="3",
            align="center",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.icon("refresh-cw", size=16),
                "Sync",
                on_click=AppState.refresh_all,
                variant="soft",
                size="2",
            ),
            notification_bell(),
            rx.color_mode.button(size="2", variant="ghost"),
            # ── User avatar / profile trigger ─────────────────────────────────
            rx.cond(
                AppState.is_authenticated,
                rx.hstack(
                    rx.dialog.root(
                        rx.dialog.trigger(
                            rx.button(
                                rx.hstack(
                                    rx.avatar(
                                        src=AppState.current_user_image,
                                        fallback=AppState.current_user_name[:1],
                                        size="2",
                                        radius="full",
                                    ),
                                    rx.text(AppState.current_user_name, size="2"),
                                    spacing="2",
                                    align="center",
                                ),
                                variant="ghost",
                                size="2",
                                on_click=AppState.open_profile_dialog,
                            ),
                        ),
                        rx.dialog.content(
                            rx.dialog.title("Your Profile"),
                            rx.vstack(
                                rx.hstack(
                                    rx.avatar(
                                        src=AppState.current_user_image,
                                        fallback=AppState.current_user_name[:1],
                                        size="5",
                                        radius="full",
                                    ),
                                    rx.vstack(
                                        rx.text(AppState.current_user_name, size="4", weight="bold"),
                                        rx.text("@" + AppState.current_user_handle, size="2", color="gray"),
                                        rx.cond(
                                            AppState.current_user_email != "",
                                            rx.text(AppState.current_user_email, size="2", color="gray"),
                                            rx.text("No email on file", size="2", color="gray"),
                                        ),
                                        align_items="start",
                                        spacing="1",
                                    ),
                                    spacing="4",
                                    align="center",
                                ),
                                rx.divider(),
                                rx.text("Display name", size="2", weight="medium"),
                                rx.input(value=AppState.profile_edit_name, on_change=AppState.set_profile_edit_name, width="100%", size="2"),
                                rx.text("User ID", size="2", weight="medium"),
                                rx.input(
                                    value=AppState.profile_edit_handle,
                                    on_change=AppState.set_profile_edit_handle,
                                    width="100%",
                                    size="2",
                                    disabled=AppState.current_user_handle_changes_left <= 0,
                                ),
                                rx.cond(
                                    AppState.current_user_handle_changes_left <= 0,
                                    rx.text("User ID is locked — no more changes.", size="1", color="red"),
                                    rx.text(
                                        "You can change your User ID 1 more time.",
                                        size="1",
                                        color="gray",
                                    ),
                                ),
                                rx.text("Email (for password reset)", size="2", weight="medium"),
                                rx.input(
                                    placeholder="your@email.com (optional)",
                                    type="email",
                                    value=AppState.profile_edit_email,
                                    on_change=AppState.set_profile_edit_email,
                                    width="100%",
                                    size="2",
                                ),
                                rx.text("Description", size="2", weight="medium"),
                                rx.text_area(value=AppState.profile_edit_description, on_change=AppState.set_profile_edit_description, width="100%", size="2"),
                                rx.button("Save profile", on_click=AppState.save_profile, size="2", color_scheme="indigo"),
                                rx.divider(),
                                rx.text("Change password", size="3", weight="bold"),
                                rx.input(placeholder="Current password", type="password", value=AppState.change_pw_current, on_change=AppState.set_change_pw_current, width="100%", size="2"),
                                rx.input(placeholder="New password", type="password", value=AppState.change_pw_new, on_change=AppState.set_change_pw_new, width="100%", size="2"),
                                rx.input(placeholder="Confirm new password", type="password", value=AppState.change_pw_confirm, on_change=AppState.set_change_pw_confirm, width="100%", size="2"),
                                rx.cond(
                                    AppState.change_pw_message != "",
                                    rx.text(AppState.change_pw_message, size="2", color=rx.cond(AppState.change_pw_is_error, "var(--red-9)", "var(--green-9)")),
                                ),
                                rx.button("Change password", on_click=AppState.change_password, size="2", variant="soft", color_scheme="red"),
                                rx.divider(),
                                rx.hstack(
                                    rx.dialog.close(rx.button("Close", variant="soft", size="2")),
                                    rx.button("Logout", on_click=AppState.logout, size="2", color_scheme="red", variant="outline"),
                                    justify="between",
                                    width="100%",
                                ),
                                spacing="3",
                                align_items="start",
                                width="100%",
                                max_width="480px",
                            ),
                            size="3",
                        ),
                        open=AppState.profile_dialog_open,
                        on_open_change=AppState.set_profile_dialog_open,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.link(
                    rx.button("Login", size="2", variant="soft", color_scheme="indigo"),
                    href="/login",
                ),
            ),
            spacing="2",
            align="center",
        ),
        width="100%",
        align="center",
        padding_bottom="1.25rem",
        border_bottom="1px solid var(--gray-6)",
        margin_bottom="1.5rem",
    )


def _team_switcher() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text("Active workspace", size="1", weight="bold", color="gray", text_transform="uppercase"),
                rx.text("Choose the team whose board and data you are editing.", size="2", color="gray"),
                rx.text(
                    "Accounts: new users register at /register and sign in at /login. "
                    "Invites and join requests only work for registered User IDs.",
                    size="1",
                    color="gray",
                    style={"max_width": "480px"},
                ),
                spacing="1",
                align_items="start",
            ),
            rx.spacer(),
            rx.cond(
                AppState.has_teams,
                rx.select.root(
                    rx.select.trigger(placeholder="Select a team", width="280px"),
                    rx.select.content(
                        rx.foreach(
                            AppState.teams,
                            lambda t: rx.select.item(t["name"], value=t["id"].to_string()),
                        ),
                    ),
                    value=AppState.active_team_id.to_string(),
                    on_change=AppState.on_team_selected,
                    size="3",
                    variant="surface",
                ),
                rx.callout(
                    "No team yet. Open the Team tab, create a team, then pick it here.",
                    color="amber",
                    size="2",
                ),
            ),
            width="100%",
            align="center",
            spacing="4",
            flex_wrap="wrap",
        ),
        variant="surface",
    )


def _form_row(*children: rx.Component) -> rx.Component:
    return rx.hstack(
        *children,
        spacing="3",
        width="100%",
        align="start",
        flex_wrap="wrap",
    )


def _labeled_input(
    label: str,
    placeholder: str,
    value,
    on_change,
    width: str | None = None,
    **kwargs,
) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        rx.input(placeholder=placeholder, value=value, on_change=on_change, width=width or "100%", size="3", **kwargs),
        spacing="1",
        align_items="start",
        min_width="200px",
        flex="1",
    )


def _labeled_select(
    label: str,
    items: list[tuple[str, str]],
    value,
    on_change,
    width: str = "100%",
    min_width: str = "200px",
    size: str = "3",
) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        rx.select.root(
            rx.select.trigger(width=width),
            rx.select.content(
                *[rx.select.item(text, value=val) for val, text in items],
            ),
            value=value,
            on_change=on_change,
            size=size,
            variant="surface",
        ),
        spacing="1",
        align_items="start",
        min_width=min_width,
        flex="1",
    )


def _labeled_datetime(label: str, value, on_change, min_width: str = "220px") -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        rx.input(
            type="datetime-local",
            value=value,
            on_change=on_change,
            width="100%",
            size="3",
        ),
        spacing="1",
        align_items="start",
        min_width=min_width,
        flex="1",
    )


def _category_filter_select() -> rx.Component:
    return rx.vstack(
        rx.text("Category filter", size="2", weight="medium"),
        rx.select.root(
            rx.select.trigger(width="240px"),
            rx.select.content(
                rx.select.item("All categories", value=SELECT_ALL_CATEGORIES),
                *[rx.select.item(text, value=val) for val, text in TASK_CATEGORIES],
            ),
            value=AppState.category_filter,
            on_change=AppState.on_category_filter_change,
            size="2",
            variant="surface",
        ),
        spacing="1",
        align_items="start",
    )


def _task_move_menu(task) -> rx.Component:
    return rx.dropdown_menu.root(
        rx.dropdown_menu.trigger(
            rx.button(rx.icon("arrow-right-left", size=14), "Move", variant="ghost", size="1"),
        ),
        rx.dropdown_menu.content(
            rx.dropdown_menu.item("Backlog", on_click=AppState.move_task_status(task["id"], "backlog")),
            rx.dropdown_menu.item("To do", on_click=AppState.move_task_status(task["id"], "todo")),
            rx.dropdown_menu.item("In progress", on_click=AppState.move_task_status(task["id"], "in_progress")),
            rx.dropdown_menu.item("Review", on_click=AppState.move_task_status(task["id"], "review")),
            rx.dropdown_menu.item("Done", on_click=AppState.move_task_status(task["id"], "done")),
            rx.dropdown_menu.item("Returned", on_click=AppState.move_task_status(task["id"], "returned")),
        ),
    )


def _task_detail_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(AppState.detail_title),
            rx.vstack(
                rx.text(AppState.detail_task["description"], size="2", color="gray"),
                rx.hstack(
                    rx.badge(AppState.detail_task["category"], variant="soft"),
                    rx.text("Creator: ", AppState.detail_task["creator_name"], size="2", color="gray"),
                    rx.text(
                        "Due: ",
                        rx.cond(AppState.detail_task["deadline"] != None, AppState.detail_task["deadline"], "—"),
                        size="2",
                        color="gray",
                    ),
                    spacing="3",
                    flex_wrap="wrap",
                    align="center",
                ),
                rx.cond(
                    AppState.detail_task["attachment_url"] != "",
                    rx.link(
                        rx.hstack(rx.icon("paperclip", size=14), rx.text("Attachment link"), spacing="2"),
                        href=AppState.detail_task["attachment_url"],
                        is_external=True,
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.detail_task["file_rules"] != "",
                    rx.callout(AppState.detail_task["file_rules"], title="File rules", color="blue", size="1"),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.detail_task["rejection_flag"],
                    rx.callout(
                        AppState.detail_task["rejection_reason"],
                        title="Returned for rework",
                        color="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.divider(),
                rx.heading("Workflow", size="3"),
                _form_row(
                    rx.cond(
                        AppState.detail_task_closed,
                        rx.vstack(
                            rx.text("Status", size="2", weight="medium"),
                            rx.badge(AppState.detail_status_value, variant="soft", size="2"),
                            spacing="1",
                            align_items="start",
                            flex="1",
                            min_width="180px",
                        ),
                        rx.vstack(
                            rx.text("Status", size="2", weight="medium"),
                            rx.select.root(
                                rx.select.trigger(width="100%"),
                                rx.select.content(
                                    rx.select.item("Backlog", value="backlog"),
                                    rx.select.item("To do", value="todo"),
                                    rx.select.item("In progress", value="in_progress"),
                                    rx.select.item("Review", value="review"),
                                    rx.select.item("Done", value="done"),
                                    rx.select.item("Returned", value="returned"),
                                ),
                                value=AppState.detail_status_value,
                                on_change=AppState.update_detail_status,
                                size="2",
                            ),
                            spacing="1",
                            align_items="start",
                            flex="1",
                            min_width="180px",
                        ),
                    ),
                    rx.cond(
                        AppState.i_am_supervisor,
                        rx.cond(
                            AppState.detail_task_closed,
                            rx.vstack(
                                rx.text("Assignee", size="2", weight="medium"),
                                rx.text(AppState.detail_assignee_label, size="2", color="gray"),
                                spacing="1",
                                align_items="start",
                                flex="1",
                                min_width="200px",
                            ),
                            rx.vstack(
                                rx.text("Assignee", size="2", weight="medium"),
                                rx.select.root(
                                    rx.select.trigger(placeholder="Unassigned", width="100%"),
                                    rx.select.content(
                                        rx.select.item("Unassigned", value="none"),
                                        rx.foreach(
                                            AppState.members,
                                            lambda m: rx.select.item(m["display_name"], value=m["id"].to_string()),
                                        ),
                                    ),
                                    value=AppState.detail_assignee_value,
                                    on_change=AppState.update_detail_assignee,
                                    size="2",
                                ),
                                spacing="1",
                                align_items="start",
                                flex="1",
                                min_width="200px",
                            ),
                        ),
                        rx.vstack(
                            rx.text("Assignee", size="2", weight="medium"),
                            rx.text(AppState.detail_assignee_label, size="2", color="gray"),
                            spacing="1",
                            align_items="start",
                            flex="1",
                            min_width="200px",
                        ),
                    ),
                    rx.cond(
                        AppState.i_am_supervisor,
                        rx.cond(
                            AppState.detail_task_closed,
                            rx.vstack(
                                rx.text("Grade (0–100)", size="2", weight="medium"),
                                rx.text(AppState.detail_grade, size="2", weight="medium"),
                                spacing="1",
                                align_items="start",
                            ),
                            rx.vstack(
                                rx.text("Grade (0–100)", size="2", weight="medium"),
                                rx.hstack(
                                    rx.input(
                                        value=AppState.detail_grade,
                                        on_change=AppState.set_detail_grade,
                                        width="100px",
                                        size="2",
                                        disabled=AppState.detail_grade_locked,
                                    ),
                                    rx.cond(
                                        AppState.detail_grade_locked,
                                        rx.button("Edit", on_click=AppState.unlock_detail_grade, size="2", variant="outline"),
                                        rx.button("Save", on_click=AppState.save_detail_grade, size="2", variant="soft"),
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                spacing="1",
                                align_items="start",
                            ),
                        ),
                        rx.box(),
                    ),
                ),
                rx.cond(
                    AppState.i_am_supervisor,
                    rx.cond(
                        AppState.detail_task_closed,
                        rx.fragment(),
                        rx.fragment(
                            rx.divider(),
                            rx.heading("Return work", size="3"),
                            rx.text("Send back to assignee with a reason.", size="2", color="gray"),
                            rx.hstack(
                                rx.input(
                                    placeholder="Describe what needs fixing",
                                    value=AppState.return_reason,
                                    on_change=AppState.set_return_reason,
                                    flex="1",
                                    size="2",
                                ),
                                rx.button(
                                    "Return",
                                    on_click=AppState.submit_return_task,
                                    color_scheme="red",
                                    variant="solid",
                                    size="2",
                                ),
                                width="100%",
                                spacing="2",
                            ),
                        ),
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.i_am_detail_assignee,
                    rx.cond(
                        AppState.detail_task_closed,
                        rx.fragment(
                            rx.divider(),
                            rx.callout(
                                "This task is completed. You cannot submit more work.",
                                title="Task closed",
                                color="green",
                                size="1",
                            ),
                        ),
                        rx.fragment(
                            rx.divider(),
                            rx.card(
                            rx.vstack(
                                rx.heading("Submit work", size="3"),
                                rx.text(
                                    "Deliver your work to the supervisor. Add an optional attachment (max 25MB).",
                                    size="2",
                                    color="gray",
                                ),
                                rx.text("Title", size="2", weight="medium"),
                                rx.input(
                                    placeholder="e.g. Sprint 3 deliverable",
                                    value=AppState.submit_work_title,
                                    on_change=AppState.set_submit_work_title,
                                    width="100%",
                                    size="2",
                                ),
                                rx.text("Description", size="2", weight="medium"),
                                rx.text_area(
                                    placeholder="Notes for your supervisor…",
                                    value=AppState.submit_work_description,
                                    on_change=AppState.set_submit_work_description,
                                    width="100%",
                                    size="2",
                                    min_height="80px",
                                ),
                                rx.text("Attachment (optional)", size="2", weight="medium"),
                                rx.upload(
                                    rx.vstack(
                                        rx.icon("upload", size=22),
                                        rx.text("Drop a file or click to browse", size="2", color="gray"),
                                        spacing="2",
                                        align="center",
                                    ),
                                    id="work_submit",
                                    multiple=False,
                                    max_files=1,
                                    padding="1rem",
                                    border="1px dashed var(--gray-7)",
                                    border_radius="8px",
                                    width="100%",
                                ),
                                rx.button(
                                    "Submit",
                                    on_click=AppState.submit_work(rx.upload_files(upload_id="work_submit")),
                                    size="2",
                                ),
                                spacing="3",
                                align_items="start",
                                width="100%",
                            ),
                            width="100%",
                        ),
                        ),
                    ),
                    rx.fragment(),
                ),
                rx.divider(),
                rx.heading("Work submissions", size="3"),
                rx.text(
                    "Deliverables uploaded for this task (newest first).",
                    size="2",
                    color="gray",
                ),
                rx.vstack(
                    rx.foreach(
                        AppState.detail_submissions,
                        lambda s: rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.text(s["title"], weight="bold", size="2"),
                                    rx.badge(s["submitter_handle"], variant="soft", size="1"),
                                    spacing="2",
                                    align="center",
                                    flex_wrap="wrap",
                                ),
                                rx.text(s["created_at"], size="1", color="gray"),
                                rx.cond(
                                    s["description"],
                                    rx.text(s["description"], size="2", color="gray"),
                                    rx.fragment(),
                                ),
                                rx.cond(
                                    s["file_url"],
                                    rx.link(
                                        rx.hstack(
                                            rx.icon("paperclip", size=14),
                                            rx.text(
                                                rx.cond(
                                                    s["original_filename"],
                                                    s["original_filename"],
                                                    "Download attachment",
                                                ),
                                            ),
                                            spacing="2",
                                            align="center",
                                        ),
                                        href=s["file_url"],
                                        is_external=True,
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="2",
                                align_items="start",
                                width="100%",
                            ),
                            width="100%",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                    align_items="stretch",
                ),
                rx.divider(),
                rx.heading("Subtasks", size="3"),
                rx.vstack(
                    rx.foreach(
                        AppState.detail_subtasks,
                        lambda st: rx.hstack(
                            rx.button(
                                rx.icon("check", size=14),
                                on_click=AppState.flip_subtask(st["id"]),
                                variant="outline",
                                size="1",
                                color_scheme="green",
                            ),
                            rx.text(
                                st["title"],
                                size="2",
                                style={"text_decoration": rx.cond(st["is_done"], "line-through", "none")},
                            ),
                            spacing="2",
                            align="center",
                            width="100%",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                    align_items="stretch",
                ),
                rx.hstack(
                    rx.input(
                        placeholder="New subtask",
                        value=AppState.new_subtask_title,
                        on_change=AppState.set_new_subtask_title,
                        flex="1",
                        size="2",
                    ),
                    rx.button("Add", on_click=AppState.add_subtask, size="2"),
                    width="100%",
                    spacing="2",
                ),
                rx.divider(),
                rx.heading("Activity", size="3"),
                rx.vstack(
                    rx.foreach(
                        AppState.detail_logs,
                        lambda log: rx.hstack(
                            rx.text(log["created_at"], size="1", color="gray", style={"white_space": "nowrap"}),
                            rx.badge(log["action"], variant="soft", size="1"),
                            rx.text(log["details"], size="2"),
                            rx.text("·", color="gray"),
                            rx.text(log["actor"], size="1", color="gray"),
                            spacing="2",
                            align="start",
                            width="100%",
                            flex_wrap="wrap",
                        ),
                    ),
                    spacing="2",
                    align_items="start",
                    max_height="200px",
                    overflow_y="auto",
                    width="100%",
                ),
                # ── Comments ─────────────────────────────────────────────────
                rx.divider(),
                rx.heading("Comments", size="3"),
                comment_section(),
                # ─────────────────────────────────────────────────────────────
                rx.hstack(
                    rx.cond(
                        AppState.i_am_supervisor,
                        rx.cond(
                            AppState.detail_grade_locked,
                            rx.cond(
                                AppState.detail_task_closed,
                                rx.dialog.close(rx.button("Close", variant="soft", size="2")),
                                rx.button(
                                    "Complete",
                                    on_click=AppState.complete_task_and_close,
                                    variant="solid",
                                    color_scheme="green",
                                    size="2",
                                ),
                            ),
                            rx.dialog.close(rx.button("Close", variant="soft", size="2")),
                        ),
                        rx.dialog.close(rx.button("Close", variant="soft", size="2")),
                    ),
                    justify="end",
                    width="100%",
                    padding_top="2",
                ),
                spacing="4",
                align_items="start",
                max_width="560px",
                width="100%",
            ),
            size="3",
        ),
        open=AppState.task_dialog_open,
        on_open_change=AppState.on_task_dialog_open_change,
    )


def team_panel() -> rx.Component:
    return rx.vstack(
        _team_switcher(),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("id-card", size=18),
                    rx.heading("Who are you?", size="4"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "You are signed in. Your User ID and profile come from your account (profile menu). "
                    "Supervisors invite others by User ID; join requests use your logged-in identity.",
                    size="2",
                    color="gray",
                ),
                _form_row(
                    rx.vstack(
                        rx.text("User ID", size="2", weight="medium"),
                        rx.text(AppState.current_user_handle, size="3", weight="bold"),
                        spacing="1",
                        align_items="start",
                    ),
                    rx.vstack(
                        rx.text("Display name", size="2", weight="medium"),
                        rx.text(AppState.current_user_name, size="3"),
                        spacing="1",
                        align_items="start",
                    ),
                ),
                rx.text("To change your name or password, use the profile menu (avatar, top right).", size="2", color="gray"),
                spacing="3",
                align_items="start",
                width="100%",
            ),
            variant="surface",
        ),
        rx.hstack(
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.icon("building-2", size=18),
                        rx.heading("New team", size="4"),
                        spacing="2",
                        align="center",
                    ),
                    rx.callout(
                        "Who is the supervisor? No one picks it manually. The account you are logged in with right now "
                        "becomes the team Supervisor when you create the team—there is only one per team. "
                        "After creating, open Members on this team and look for the amber Supervisor badge on your row. "
                        "Invited or approved members are always regular members, not supervisors.",
                        icon="info",
                        color="blue",
                        size="1",
                    ),
                    _form_row(
                        _labeled_input("Name", "e.g. Platform squad", AppState.team_name, AppState.set_team_name),
                        _labeled_input("Join code", "Unique invite code", AppState.team_join_code, AppState.set_team_join_code),
                    ),
                    _labeled_input(
                        "Description",
                        "What this team owns",
                        AppState.team_description,
                        AppState.set_team_description,
                    ),
                    rx.button(rx.icon("plus", size=16), "Create team", on_click=AppState.create_team, size="3"),
                    spacing="4",
                    align_items="start",
                    width="100%",
                ),
                variant="classic",
                flex="2",
                min_width="320px",
            ),
            rx.cond(
                AppState.i_am_supervisor,
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("user-plus", size=18),
                            rx.heading("Invite member", size="4"),
                            spacing="2",
                            align="center",
                        ),
                        rx.text(
                            "Only the team supervisor can invite. The person must already have registered a User ID.",
                            size="2",
                            color="gray",
                        ),
                        _labeled_input(
                            "Invitee User ID",
                            "john_doe",
                            AppState.member_invite_handle,
                            AppState.set_member_invite_handle,
                        ),
                        rx.button("Invite member", on_click=AppState.add_member, size="3", color_scheme="indigo"),
                        spacing="4",
                        align_items="start",
                        width="100%",
                    ),
                    variant="classic",
                    flex="1",
                    min_width="280px",
                ),
                rx.card(
                    rx.callout(
                        "Only your team supervisor can invite people by User ID.",
                        color="amber",
                        size="2",
                    ),
                    variant="classic",
                    flex="1",
                    min_width="280px",
                ),
            ),
            spacing="4",
            width="100%",
            align="start",
            flex_wrap="wrap",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("key-round", size=18),
                    rx.heading("Request to join", size="4"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Uses your logged-in User ID. The team supervisor gets a notification and must approve you.",
                    size="2",
                    color="gray",
                ),
                _labeled_input("Join code", "e.g. alpha-2026", AppState.join_code_input, AppState.set_join_code_input),
                rx.button("Send join request", on_click=AppState.join_team_by_code, size="3", variant="surface"),
                spacing="4",
                align_items="start",
                width="100%",
            ),
            variant="classic",
        ),
        rx.cond(
            AppState.i_am_supervisor,
            rx.card(
                rx.vstack(
                    rx.heading("Pending join requests", size="4"),
                    rx.text("Approve or reject people who asked to join this team.", size="2", color="gray"),
                    rx.divider(),
                    rx.cond(
                        AppState.join_requests.length() == 0,
                        rx.text("No pending requests.", size="2", color="gray"),
                        rx.vstack(
                            rx.foreach(
                                AppState.join_requests,
                                lambda jr: rx.hstack(
                                    rx.vstack(
                                        rx.text(jr["display_name"], weight="bold", size="2"),
                                        rx.text(jr["handle"], size="1", color="gray"),
                                        spacing="0",
                                        align_items="start",
                                    ),
                                    rx.spacer(),
                                    rx.button(
                                        "Approve",
                                        size="2",
                                        variant="solid",
                                        color_scheme="green",
                                        on_click=AppState.approve_join_request(jr["id"]),
                                    ),
                                    rx.button(
                                        "Reject",
                                        size="2",
                                        variant="surface",
                                        color_scheme="red",
                                        on_click=AppState.reject_join_request(jr["id"]),
                                    ),
                                    width="100%",
                                    align="center",
                                    padding_y="8px",
                                    border_bottom="1px solid var(--gray-5)",
                                ),
                            ),
                            spacing="0",
                            width="100%",
                        ),
                    ),
                    spacing="3",
                    align_items="start",
                    width="100%",
                ),
                variant="surface",
            ),
        ),
        rx.card(
            rx.vstack(
                rx.heading("Directory", size="4"),
                rx.divider(),
                rx.grid(
                    rx.foreach(
                        AppState.teams,
                        lambda team: rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.heading(team["name"], size="3"),
                                    rx.badge(team["join_code"], variant="soft", color_scheme="gray"),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.text(team["description"], size="2", color="gray"),
                                align_items="start",
                                spacing="2",
                            ),
                            variant="surface",
                        ),
                    ),
                    columns="3",
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                align_items="start",
                width="100%",
            ),
            variant="surface",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Members on this team", size="4"),
                rx.text(
                    "The account with the amber “Supervisor” badge is the team owner: they invite members, "
                    "approve join requests, create tasks, and plan activities. Everyone else is a member.",
                    size="2",
                    color="gray",
                ),
                rx.divider(),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Name"),
                            rx.table.column_header_cell("User ID"),
                            rx.table.column_header_cell("Role"),
                            rx.table.column_header_cell(""),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            AppState.members,
                            lambda m: rx.table.row(
                                rx.table.cell(m["display_name"]),
                                rx.table.cell(m["handle"]),
                                rx.table.cell(
                                    rx.cond(
                                        m["role_name"] == "supervisor",
                                        rx.badge("Supervisor", variant="solid", color_scheme="amber"),
                                        rx.cond(
                                            m["role_name"] == "lead",
                                            rx.badge("Supervisor", variant="solid", color_scheme="amber"),
                                            rx.badge(m["role_name"], variant="soft", color_scheme="blue"),
                                        ),
                                    ),
                                ),
                                rx.table.cell(
                                    rx.cond(
                                        AppState.i_am_supervisor,
                                        rx.button(
                                            "Remove",
                                            size="1",
                                            variant="ghost",
                                            color_scheme="red",
                                            on_click=AppState.remove_member(m["id"]),
                                        ),
                                        rx.text(""),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                spacing="3",
                align_items="start",
                width="100%",
            ),
            variant="surface",
        ),
        spacing="4",
        width="100%",
    )


def _kanban_column(status: str, title: str, accent: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.box(width="3px", height="100%", min_height="1rem", background=accent, border_radius="2px"),
                rx.heading(title, size="3", weight="bold"),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.divider(),
            rx.vstack(
                rx.foreach(
                    AppState.kanban[status],
                    lambda task: rx.card(
                        rx.vstack(
                            rx.text(task["name"], size="2", weight="bold"),
                            rx.hstack(
                                rx.badge(task["category"], variant="soft", color_scheme="gray", size="1"),
                                rx.badge(
                                    task["status"],
                                    variant="outline",
                                    size="1",
                                    color_scheme="indigo",
                                ),
                                spacing="2",
                                flex_wrap="wrap",
                            ),
                            rx.text(
                                rx.cond(task["deadline"] != None, task["deadline"], "No deadline"),
                                size="1",
                                color="gray",
                            ),
                            rx.hstack(
                                rx.button(
                                    "Open",
                                    size="1",
                                    variant="soft",
                                    on_click=AppState.open_task(task["id"]),
                                ),
                                _task_move_menu(task),
                                spacing="2",
                                width="100%",
                                justify="between",
                                padding_top="2",
                            ),
                            spacing="2",
                            align_items="start",
                            width="100%",
                        ),
                        variant="surface",
                        size="1",
                        width="100%",
                    ),
                ),
                spacing="2",
                width="100%",
                align_items="stretch",
            ),
            spacing="3",
            align_items="start",
            width="100%",
            min_height="280px",
        ),
        variant="classic",
        min_width="272px",
        max_width="272px",
        flex_shrink="0",
    )


def board_panel() -> rx.Component:
    return rx.vstack(
        _team_switcher(),
        rx.box(
            rx.hstack(
                _kanban_column("backlog", "Backlog", "var(--gray-9)"),
                _kanban_column("todo", "To do", "var(--blue-9)"),
                _kanban_column("in_progress", "In progress", "var(--amber-9)"),
                _kanban_column("review", "Review", "var(--violet-9)"),
                _kanban_column("done", "Done", "var(--green-9)"),
                _kanban_column("returned", "Returned", "var(--red-9)"),
                spacing="3",
                width="max-content",
                align="start",
            ),
            width="100%",
            overflow_x="auto",
            padding_bottom="0.5rem",
            style={"scrollbar_width": "thin"},
        ),
        spacing="4",
        width="100%",
    )


def work_panel() -> rx.Component:
    return rx.vstack(
        _team_switcher(),
        rx.cond(
            AppState.i_am_supervisor,
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.icon("circle-plus", size=20),
                        rx.heading("New task", size="4"),
                        spacing="2",
                        align="center",
                    ),
                    _form_row(
                        _labeled_input("Title", "Task title", AppState.task_name, AppState.set_task_name),
                        _labeled_select("Category", TASK_CATEGORIES, AppState.task_category, AppState.set_task_category),
                        _labeled_input("Creator", "Your name", AppState.task_creator, AppState.set_task_creator),
                    ),
                    _labeled_input(
                        "Description",
                        "Acceptance criteria, context…",
                        AppState.task_description,
                        AppState.set_task_description,
                    ),
                    _form_row(
                        _labeled_datetime("Deadline (optional)", AppState.task_deadline, AppState.set_task_deadline),
                        rx.vstack(
                            rx.text("Assignee", size="2", weight="medium"),
                            rx.select.root(
                                rx.select.trigger(placeholder="Unassigned", width="100%"),
                                rx.select.content(
                                    rx.select.item("Unassigned", value="none"),
                                    rx.foreach(
                                        AppState.members,
                                        lambda m: rx.select.item(m["display_name"], value=m["id"].to_string()),
                                    ),
                                ),
                                value=AppState.task_assignee_choice,
                                on_change=AppState.set_task_assignee_choice,
                                size="3",
                            ),
                            spacing="1",
                            align_items="start",
                            flex="1",
                            min_width="200px",
                        ),
                    ),
                    _form_row(
                        _labeled_input("Link / attachment URL", "https://…", AppState.task_attachment, AppState.set_task_attachment),
                        _labeled_select(
                            "Allowed file types",
                            FILE_RULE_PRESETS,
                            AppState.task_file_rules,
                            AppState.set_task_file_rules,
                        ),
                    ),
                    rx.button("Create task", on_click=AppState.create_task, size="3", color_scheme="indigo"),
                    spacing="4",
                    align_items="start",
                    width="100%",
                ),
                variant="classic",
            ),
            rx.callout(
                "Only the team supervisor can create tasks. Open a task on the board to add subtasks.",
                color="amber",
                size="2",
            ),
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading("Task list", size="4"),
                    rx.spacer(),
                    _category_filter_select(),
                    width="100%",
                    align="center",
                ),
                rx.divider(),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Task"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell("Category"),
                            rx.table.column_header_cell("Deadline"),
                            rx.table.column_header_cell(""),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            AppState.tasks,
                            lambda task: rx.table.row(
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(task["name"], weight="medium"),
                                        rx.text(task["description"], size="1", color="gray", style={"max_width": "360px"}),
                                        spacing="0",
                                        align_items="start",
                                    ),
                                ),
                                rx.table.cell(rx.badge(task["status"], variant="soft", color_scheme="indigo")),
                                rx.table.cell(task["category"]),
                                rx.table.cell(rx.cond(task["deadline"] != None, task["deadline"], "—")),
                                rx.table.cell(
                                    rx.hstack(
                                        rx.button(
                                            "Open",
                                            size="1",
                                            variant="soft",
                                            on_click=AppState.open_task(task["id"]),
                                        ),
                                        _task_move_menu(task),
                                        spacing="2",
                                    ),
                                ),
                            ),
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                spacing="3",
                align_items="start",
                width="100%",
            ),
            variant="surface",
        ),
        spacing="4",
        width="100%",
    )


def plan_panel() -> rx.Component:
    return rx.vstack(
        _team_switcher(),
        rx.cond(
            AppState.i_am_supervisor,
            rx.card(
                rx.vstack(
                    rx.heading("Schedule activity", size="4"),
                    _form_row(
                        _labeled_input("Title", "Milestone name", AppState.activity_title, AppState.set_activity_title),
                        _labeled_datetime("Start", AppState.activity_start, AppState.set_activity_start),
                        _labeled_datetime("End", AppState.activity_end, AppState.set_activity_end),
                        _labeled_select(
                            "Category",
                            ACTIVITY_CATEGORIES,
                            AppState.activity_category,
                            AppState.set_activity_category,
                        ),
                    ),
                    rx.button("Add to timeline", on_click=AppState.create_activity, size="3"),
                    spacing="4",
                    align_items="start",
                    width="100%",
                ),
                variant="classic",
            ),
            rx.callout(
                "Only the team supervisor can add planning activities.",
                color="amber",
                size="2",
            ),
        ),
        rx.vstack(
            rx.heading("Timeline", size="4"),
            rx.foreach(
                AppState.activities,
                lambda item: rx.card(
                    rx.hstack(
                        rx.box(
                            width="4px",
                            align_self="stretch",
                            min_height="3rem",
                            background="var(--indigo-9)",
                            border_radius="2px",
                        ),
                        rx.vstack(
                            rx.text(item["title"], size="3", weight="bold"),
                            rx.hstack(
                                rx.badge(item["category"], variant="soft"),
                                rx.text(
                                    item["timeline_start"],
                                    size="2",
                                    color="gray",
                                ),
                                rx.text("→", size="2", color="gray"),
                                rx.text(
                                    item["timeline_end"],
                                    size="2",
                                    color="gray",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                            align_items="start",
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                    variant="surface",
                ),
            ),
            spacing="3",
            width="100%",
            align_items="stretch",
        ),
        spacing="4",
        width="100%",
    )


def insights_panel() -> rx.Component:
    return rx.vstack(
        _team_switcher(),
        rx.grid(
            rx.foreach(
                AppState.performance,
                lambda p: rx.card(
                    rx.vstack(
                        rx.text(p["member_name"], size="4", weight="bold"),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Assigned", size="1", color="gray", text_transform="uppercase"),
                                rx.text(p["assigned_tasks"], size="6", weight="bold"),
                                spacing="0",
                                align_items="start",
                            ),
                            rx.vstack(
                                rx.text("Done", size="1", color="gray", text_transform="uppercase"),
                                rx.text(p["completed_tasks"], size="6", weight="bold"),
                                spacing="0",
                                align_items="start",
                            ),
                            rx.vstack(
                                rx.text("Rate", size="1", color="gray", text_transform="uppercase"),
                                rx.text(
                                    p["completion_rate"].to_string() + "%",
                                    size="6",
                                    weight="bold",
                                ),
                                spacing="0",
                                align_items="start",
                            ),
                            rx.vstack(
                                rx.text("Avg grade", size="1", color="gray", text_transform="uppercase"),
                                rx.text(
                                    rx.cond(p["avg_grade"] != None, p["avg_grade"], "—"),
                                    size="6",
                                    weight="bold",
                                ),
                                spacing="0",
                                align_items="start",
                            ),
                            width="100%",
                            spacing="4",
                            justify="between",
                            flex_wrap="wrap",
                        ),
                        spacing="3",
                        align_items="start",
                        width="100%",
                    ),
                    variant="classic",
                ),
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def dashboard() -> rx.Component:
    return rx.fragment(
        rx.toast.provider(),
        notification_panel(),
        rx.box(
            rx.vstack(
                _toolbar(),
                _task_detail_dialog(),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(rx.hstack(rx.icon("columns-3", size=16), rx.text("Board"), spacing="2"), value="board"),
                        rx.tabs.trigger(rx.hstack(rx.icon("list-checks", size=16), rx.text("Work"), spacing="2"), value="work"),
                        rx.tabs.trigger(rx.hstack(rx.icon("users", size=16), rx.text("Team"), spacing="2"), value="team"),
                        rx.tabs.trigger(rx.hstack(rx.icon("calendar-range", size=16), rx.text("Plan"), spacing="2"), value="plan"),
                        rx.tabs.trigger(rx.hstack(rx.icon("chart-no-axes-column", size=16), rx.text("Insights"), spacing="2"), value="insights"),
                        size="2",
                        wrap="wrap",
                    ),
                    rx.tabs.content(board_panel(), value="board", padding_top=_COL_GAP),
                    rx.tabs.content(work_panel(), value="work", padding_top=_COL_GAP),
                    rx.tabs.content(team_panel(), value="team", padding_top=_COL_GAP),
                    rx.tabs.content(plan_panel(), value="plan", padding_top=_COL_GAP),
                    rx.tabs.content(insights_panel(), value="insights", padding_top=_COL_GAP),
                    default_value="board",
                    width="100%",
                ),
                spacing="2",
                width="100%",
                max_width="1400px",
                margin_x="auto",
                padding=_PAGE_PAD,
                min_height="100vh",
            ),
            width="100%",
            background="var(--gray-2)",
        ),
    )