import reflex as rx

config = rx.Config(
    app_name="pm_app",
    app_module_import="pm_app.app",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)