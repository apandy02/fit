import fasthtml.common as fh
from fit.web.common import DB, page_outline
from fit.web.databases import get_user_data


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

def get_profile_page(session):
    """Return the profile completion page"""
    user_data = get_user_data(DB, session["user_id"])
    print(user_data)
    
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Div(
                    fh.Header(
                        fh.H3("Complete Your Profile", cls="text-2xl font-bold text-center mb-6 text-primary-content"),
                        cls="mb-6 bg-base-200"
                    ),
                    fh.Form(
                        hx_post="/onboarding/complete_profile",
                        cls="space-y-6"
                    )(
                        fh.Div(
                            create_form_row("Name", create_editable_input(
                                "name",
                                user_data.get("name", ""),
                                placeholder="John Doe"
                            )),
                            create_form_row("Email", create_editable_input(
                                "email",
                                user_data.get("email", ""),
                                input_type="email",
                                placeholder="john@example.com"
                            )),
                            create_form_row("Gender", fh.Select(
                                fh.Option("Select gender", value="", selected=not user_data.get("gender"), disabled=True),
                                fh.Option("Male", value="male", selected=user_data.get("gender") == "male"),
                                fh.Option("Female", value="female", selected=user_data.get("gender") == "female"),
                                name="gender",
                                required=True,
                                cls="select select-bordered w-full bg-base-200 text-primary-content"
                            )),
                            create_form_row("Date of Birth", create_editable_input(
                                "date_of_birth",
                                user_data.get("date_of_birth", ""),
                                input_type="date",
                                placeholder="MM/DD/YYYY"
                            )),
                            create_form_row("Units", fh.Select(
                                fh.Option("Imperial (lbs, inches)", value="imperial", selected=user_data.get("units") == "imperial"),
                                fh.Option("Metric (kg, cm)", value="metric", selected=user_data.get("units") == "metric"),
                                name="units",
                                cls="select select-bordered w-full bg-base-200 text-primary-content"
                            )),
                            cls="space-y-4"
                        ),
                        fh.Button(
                            "Next →",
                            type="submit",
                            cls="btn btn-primary outline outline-1 outline-primary-content w-full mt-8"
                        ),
                        cls="p-6"
                    ),
                    cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6"
                ),
                cls="bg-base-200 shadow-lg rounded-lg"
            ),
            cls="max-w-2xl mx-auto p-6"
        ),
        cls="bg-base-100 min-h-screen flex items-center"
    )
    
    return page_outline(None, "Complete Profile", False, False, content)

def get_activity_page(session):
    """Return the activity selection page"""
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Div(
                    fh.Header(
                        fh.H3("How Active Are You?", cls="text-2xl font-bold text-center mb-6 text-primary-content"),
                        cls="mb-6 bg-base-200"
                    ),
                    fh.Form(
                        hx_post="/onboarding/activity",
                        cls="space-y-6"
                    )(
                        fh.Div(
                            fh.Button(
                                fh.Div(
                                    fh.H4("Not at all", cls="text-lg font-bold mb-2 text-primary-content"),
                                    fh.P("0 workouts per week", cls="text-sm"),
                                    cls="text-center"
                                ),
                                type="submit",
                                name="activity_level",
                                value="sedentary",
                                cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                            ),
                            fh.Button(
                                fh.Div(
                                    fh.H4("Lightly active", cls="text-lg font-bold mb-2 text-primary-content"),
                                    fh.P("1-2 workouts per week", cls="text-sm"),
                                    cls="text-center"
                                ),
                                type="submit",
                                name="activity_level",
                                value="lightly_active",
                                cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                            ),
                            fh.Button(
                                fh.Div(
                                    fh.H4("Active", cls="text-lg font-bold mb-2 text-primary-content"),
                                    fh.P("3-5 workouts per week", cls="text-sm"),
                                    cls="text-center"
                                ),
                                type="submit",
                                name="activity_level",
                                value="active",
                                cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                            ),
                            fh.Button(
                                fh.Div(
                                    fh.H4("Very active", cls="text-lg font-bold mb-2 text-primary-content"),
                                    fh.P("6+ workouts per week", cls="text-sm"),
                                    cls="text-center"
                                ),
                                type="submit",
                                name="activity_level",
                                value="very_active",
                                cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24"
                            ),
                            cls="space-y-4"
                        ),
                        cls="p-6"
                    ),
                    cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6"
                ),
                cls="bg-base-200 shadow-lg rounded-lg"
            ),
            cls="max-w-2xl mx-auto p-6"
        ),
        cls="bg-base-100 min-h-screen flex items-center"
    )
    
    return page_outline(None, "Activity Level", False, False, content)

async def handle_profile_completion(session, request: fh.Request):
    """Handle profile form submission"""
    try:
        form = await request.form()
        form_data = dict(form)
        form_data["user_id"] = session["user_id"]
        
        DB.t.profile.update(form_data)
        
        return fh.Response(headers={"HX-Redirect": "/onboarding/activity"})
    except Exception as e:
        print(f"Error updating profile: {e}")
        return fh.P(
            f"Error updating profile: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        )

async def handle_activity_selection(session, request: fh.Request):
    """Handle activity level selection"""
    try:
        form = await request.form()
        activity_level = form.get("activity_level")
        
        # Store activity level in profile
        DB.t.profile.update({
            "user_id": session["user_id"],
            "activity_level": activity_level
        })
        
        return fh.Response(headers={"HX-Redirect": "/nutrition"})
    except Exception as e:
        print(f"Error updating activity level: {e}")
        return fh.P(
            f"Error updating activity level: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        ) 