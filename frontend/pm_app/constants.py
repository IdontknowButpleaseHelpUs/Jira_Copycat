TASK_CATEGORIES: list[tuple[str, str]] = [
    ("general", "General"),
    ("bug", "Bug"),
    ("feature", "Feature"),
    ("improvement", "Improvement"),
    ("documentation", "Documentation"),
    ("spike", "Spike / research"),
    ("chore", "Chore"),
    ("security", "Security"),
]

ACTIVITY_CATEGORIES: list[tuple[str, str]] = [
    ("general", "General"),
    ("sprint", "Sprint"),
    ("release", "Release"),
    ("milestone", "Milestone"),
    ("meeting", "Meeting"),
    ("review", "Review"),
    ("planning", "Planning"),
]

SELECT_ALL_CATEGORIES = "__all__"
SELECT_NO_FILE_RULES = "__none__"

FILE_RULE_PRESETS: list[tuple[str, str]] = [
    (SELECT_NO_FILE_RULES, "No restriction"),
    ("pdf, doc, docx", "Documents (PDF, Word)"),
    ("png, jpg, jpeg, gif, webp", "Images"),
    ("zip, rar, 7z", "Archives"),
    ("py, js, ts, tsx, jsx", "Source code"),
    ("csv, xlsx", "Spreadsheets"),
    ("md, txt", "Text / Markdown"),
]

ROLE_OPTIONS: list[tuple[str, str]] = [
    ("member", "Member"),
    ("developer", "Developer"),
    ("designer", "Designer"),
    ("pm", "Product manager"),
    ("lead", "Team lead"),
    ("reviewer", "Reviewer"),
]