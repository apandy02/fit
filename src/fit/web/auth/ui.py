import fasthtml.common as fh
from fit.web.common import page_outline


def get_login_page(req, fitbit_login_link: str, whoop_login_link: str):
    auth_card = fh.Form(
        fh.Div(
            fh.H5("Sign in with your fitness tracker", cls="text-xl text-base-content mt-6 text-center mb-6"),
            fh.Div(
                fh.A("Whoop", cls="btn btn-outline text-base-content font-light bg-neutral rounded-lg", href=whoop_login_link),
                fh.A("Fitbit", cls="btn btn-outline text-base-content font-light bg-neutral rounded-lg", href=fitbit_login_link),
                cls="flex flex-col space-y-4 mt-4"
            )
        ),
        cls="w-full max-w-sm p-4 bg-base-200 border border-base-300 rounded-lg shadow sm:p-6 md:p-8 outline outline-1 outline-base-content"
    )
    page_content = fh.Div(
        fh.Div(
            auth_card,
            cls="flex items-center justify-center min-h-screen"
        )
    )
    return page_outline(7, "Login", False, False, page_content)