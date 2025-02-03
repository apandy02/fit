import fasthtml.common as fh
from fit.web.common import DB, page_outline


def get_login_page(req, fitbit_login_link: str, whoop_login_link: str):
    auth_card = fh.Form(
        fh.Div(
            fh.H5("Sign in with your fitness tracker", cls="text-xl font-medium text-primary-content mt-6 text-center mb-6"),
            fh.Div(
                fh.A("Whoop", cls="btn btn-outline text-primary-content bg-base-100 rounded-lg", href=whoop_login_link),
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


def create_editable_input(name: str, value: str, input_type: str = "text", placeholder: str = "", required: bool = True):
    """Create an input field for the onboarding form"""
    return fh.Input(
        type=input_type,
        name=name,
        value=value if value else "",
        placeholder=placeholder,
        required=required,
        cls="input input-bordered w-full bg-base-200 text-primary-content focus:bg-base-200 focus:text-primary-content"
    )

def create_form_row(label: str, input_element):
    """Create a form row with label on the left and input on the right"""
    return fh.Div(
        fh.Label(label, cls="text-primary-content w-1/3 h-12 flex items-center"),
        fh.Div(input_element, cls="w-2/3"),
        cls="flex gap-4"
    )