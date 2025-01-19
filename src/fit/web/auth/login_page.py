import fasthtml.common as fh
from fit.web.common import page_outline


def get_login_page(req, fitbit_login_link: str):
    auth_card = fh.Form(
        fh.Div(
            fh.H5("Sign in with your fitness tracker", cls="text-xl font-medium text-primary-content mt-6 text-center mb-6"),
            fh.Div(
                fh.Button("Whoop", cls="btn btn-outline text-primary-content bg-base-100 rounded-lg"),
                fh.A("Fitbit", cls="btn btn-outline text-primary-content bg-base-100 rounded-lg", href=fitbit_login_link),
                cls="flex flex-col space-y-4 mt-4"
            )
        ),
        cls="w-full max-w-sm p-4 bg-primary border border-base-300 rounded-lg shadow sm:p-6 md:p-8"
    )
    page_content = fh.Div(
        fh.Div(
            auth_card,
            cls="flex items-center justify-center min-h-screen"
        )
    )
    return page_outline(7, "Login", False, False, page_content)