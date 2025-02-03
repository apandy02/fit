import fasthtml.common as fh

from fit.web.common import DB, page_outline
from fit.web.databases import get_profile_data


def create_editable_input(name: str, value: str, input_type: str = "text", placeholder: str = "", required: bool = True):
    """Create an input field that can be toggled between read-only and editable"""
    input_id = f"{name}-input"
    return fh.Div(
        fh.Div(
            fh.Input(
                type=input_type,
                name=name,
                id=input_id,
                value=value,
                placeholder=placeholder,
                required=required,
                readonly=bool(value), 
                cls="input input-bordered w-full bg-base-200 text-primary-content focus:bg-base-200 focus:text-primary-content"
            ),
            cls="w-11/12" 
        ),
        fh.Button(
            "✎",  # pen symbol
            type="button",
            onclick=f"document.getElementById('{input_id}').readOnly = false; document.getElementById('{input_id}').focus();",
            cls="flex items-center justify-center h-12 w-12 hover:bg-slate-700 focus:bg-slate-700 rounded-lg bg-slate-600 border-none outline-none"
        ) if value else "", 
        cls="flex items-center gap-2" 
    )

def create_basic_info_card(user_data):
    """Create the basic information card section"""
    return fh.Card(
        fh.Header(
            fh.H3("Basic Information", cls="text-xl font-bold text-center mb-2 text-primary-content"),
            cls="mb-6 bg-base-200"
        ),
        fh.Div(
            # Name
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
            # Gender
            create_form_row("Gender", fh.Select(
                fh.Option("Select gender", value="", selected=not user_data.get("gender"), disabled=True),
                fh.Option("Male", value="male", selected=user_data.get("gender") == "male"),
                fh.Option("Female", value="female", selected=user_data.get("gender") == "female"),
                name="gender",
                required=True,
                cls="select select-bordered w-full bg-base-200 text-primary-content"
            )),
            # Date of Birth
            create_form_row("Date of Birth", create_editable_input(
                "date_of_birth",
                user_data.get("date_of_birth", ""),
                input_type="date",
                placeholder="MM/DD/YYYY"
            )),
            cls="space-y-4"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6 mb-8"
    )

def create_dietary_restrictions_card(restrictions, hx_target="restrictions-list"):
    """Create the dietary restrictions card section"""
    return fh.Card(
        fh.Header(
            fh.H3("Dietary Restrictions", cls="text-xl font-bold text-center mb-2 text-primary-content"),
            cls="mb-6 bg-base-200"
        ),
        fh.Div(
            create_form_row("Restrictions", fh.Div(
                # Dropdown for adding restrictions
                fh.Select(
                    fh.Option("Select a restriction", value="", selected=True, disabled=True),
                    fh.Option("Vegetarian", value="vegetarian"),
                    fh.Option("Vegan", value="vegan"),
                    fh.Option("Gluten-Free", value="gluten_free"),
                    fh.Option("Dairy-Free", value="dairy_free"),
                    fh.Option("Nut-Free", value="nut_free"),
                    fh.Option("Kosher", value="kosher"),
                    fh.Option("Halal", value="halal"),
                    name="dietary_restrictions",
                    hx_post="/add_restriction",
                    hx_target=f"#{hx_target}",
                    cls="select select-bordered w-full bg-base-200 text-primary-content mb-4"
                ),
                # Container for restriction tags
                fh.Div(
                    # Pre-populate existing restrictions
                    *[
                        fh.Div(
                            fh.Div(
                                r.replace('_', ' ').title(),
                                cls="flex-grow mr-8"
                            ),
                            fh.Button(
                                "×",
                                hx_post="/remove_restriction",
                                hx_vals=f'{{"restriction": "{r}"}}',
                                hx_target=f"#{hx_target}",
                                cls="text-lg hover:text-error focus:outline-none focus:ring-0 border-none"
                            ),
                            cls="bg-neutral flex items-center justify-between px-4 py-2 rounded-lg mr-2 mb-2"
                        )
                        for r in restrictions
                    ],
                    # Hidden inputs to maintain state
                    *[
                        fh.Input(
                            type="hidden",
                            name="existing_restrictions[]",
                            value=r
                        )
                        for r in restrictions
                    ],
                    id=hx_target,
                    cls="flex flex-wrap"
                ),
                cls="w-full"
            )),
            cls="space-y-4"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6 mb-8"
    )

def create_preferences_card(user_data):
    """Create the preferences card section"""
    return fh.Card(
        fh.Header(
            fh.H3("Preferences", cls="text-xl font-bold text-center mb-2 text-primary-content"),
            cls="mb-6 bg-base-200"
        ),
        fh.Div(
            create_form_row("Units", fh.Select(
                fh.Option("Imperial (lbs, inches)", value="imperial", selected=user_data.get("units") == "imperial"),
                fh.Option("Metric (kg, cm)", value="metric", selected=user_data.get("units") == "metric"),
                name="units",
                cls="select select-bordered w-full bg-base-200 text-primary-content"
            )),
            cls="space-y-4"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6 mb-8"
    )

def get(session):
    """Return the profile page content"""
    # Get user data
    user_data = get_profile_data(DB, session["user_id"])
    restrictions = user_data.get("dietary_restrictions", "")
    print(f"restrictions: {restrictions}")
    if restrictions == "" or restrictions is None:
        restrictions = []
    else:
        restrictions = restrictions.split(",")

    content = fh.Article(
        fh.Div(
            # User Profile Section
            fh.Card(
                fh.Header(
                    fh.H3("User Profile", cls="text-2xl font-bold text-center mb-2 text-primary-content"),
                    cls="mb-6 bg-base-200"
                ),
                fh.Form(
                    hx_post="/update_profile",
                    hx_target="#profile-result",
                    cls="space-y-6"
                )(
                    create_basic_info_card(user_data),
                    create_dietary_restrictions_card(restrictions),
                    create_preferences_card(user_data),
                    fh.Button(
                        "Save Changes",
                        type="submit",
                        cls="btn btn-primary outline outline-1 outline-primary-content w-full"
                    ),
                    fh.Div(id="profile-result")
                ),
                cls="bg-base-200 shadow-lg rounded-lg p-6 mb-8"
            ),
            cls="max-w-2xl mx-auto p-6 space-y-6"
        ),
        cls="bg-base-100"
    )
    return page_outline(6, "Profile", True, True, content)


def create_form_row(label: str, input_element):
    """Create a form row with label on the left and input on the right"""
    return fh.Div(
        fh.Label(label, cls="text-primary-content w-1/3 h-12 flex items-center"),
        fh.Div(input_element, cls="w-2/3"),
        cls="flex gap-4"
    )



def create_login_input_section(label: str, name: str, input_type: str = "text", **input_props):
    """Create a form input section with label and input, styled for login forms"""
    return fh.Div(
        fh.Label(label, cls="label text-primary-content"),
        fh.Input(
            type=input_type,
            name=name,
            cls="input input-bordered w-full bg-base-200 outline outline-1 outline-primary-content text-primary-content placeholder-primary-content placeholder-opacity-50",
            required=True,
            **input_props
        ),
        cls="form-control"
    )



async def update_profile(session, request: fh.Request):
    """Handle profile update"""
    try:
        form = await request.form()
        
        restrictions = form.getlist("existing_restrictions[]")
        form_data = dict(form)
        form_data["dietary_restrictions"] = ",".join(restrictions) if restrictions else ""
        form_data["user_id"] = session["user_id"]
        if "existing_restrictions[]" in form_data:
            form_data.pop("existing_restrictions[]")
        
        print(form_data)
        DB.t.profile.update(form_data)
        
        return fh.P(
            "Profile updated successfully!",
            cls="text-success font-semibold text-center mt-4"
        )
    except Exception as e:
        print(e)
        return fh.P(
            f"Error updating profile: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        )

async def add_restriction(request: fh.Request):
    """Handle adding a dietary restriction"""
    try:
        form = await request.form()
        restriction = form.get("dietary_restrictions")
        existing_restrictions = form.getlist("existing_restrictions[]")
        if restriction not in existing_restrictions:
            existing_restrictions.append(restriction)
        
        restriction_divs = [
            fh.Div(
                fh.Div(
                    r.replace('_', ' ').title(),
                    cls="flex-grow mr-8"
                ),
                fh.Button(
                    "×",
                    hx_post="/remove_restriction",
                    hx_vals=f'{{"restriction": "{r}"}}',
                    hx_target="#restrictions-list",
                    cls="text-lg hover:text-error focus:outline-none focus:ring-0 border-none"
                ),
                cls="bg-neutral flex items-center justify-between px-4 py-2 rounded-lg mr-2 mb-2"
            )
            for r in existing_restrictions
        ]
        
        return fh.Div(
            *restriction_divs,
            *[
                fh.Input(
                    type="hidden",
                    name="existing_restrictions[]",
                    value=r
                )
                for r in existing_restrictions
            ],
            id="restrictions-list",
            cls="flex flex-wrap"
        )
    except Exception as e:
        return fh.P(
            f"Error adding restriction: {str(e)}",
            cls="text-error text-sm mt-1"
        )


async def remove_restriction(request: fh.Request):
    """Handle removing a dietary restriction"""
    try:
        form = await request.form()
        restriction_to_remove = form.get("restriction")
        existing_restrictions = form.getlist("existing_restrictions[]")
        
        if restriction_to_remove in existing_restrictions:
            existing_restrictions.remove(restriction_to_remove)
        
        restriction_divs = [
            fh.Div(
                fh.Div(
                    r.replace('_', ' ').title(),
                    cls="flex-grow mr-8"
                ),
                fh.Button(
                    "×",
                    hx_post="/remove_restriction",
                    hx_vals=f'{{"restriction": "{r}"}}',
                    hx_target="#restrictions-list",
                    cls="text-lg hover:text-error focus:outline-none focus:ring-0 border-none"
                ),
                cls="bg-neutral flex items-center justify-between px-4 py-2 rounded-lg mr-2 mb-2"
            )
            for r in existing_restrictions
        ]
        
        return fh.Div(
            *restriction_divs,
            *[
                fh.Input(
                    type="hidden",
                    name="existing_restrictions[]",
                    value=r
                )
                for r in existing_restrictions
            ],
            id="restrictions-list",
            cls="flex flex-wrap"
        )
    except Exception as e:
        return fh.P(
            f"Error removing restriction: {str(e)}",
            cls="text-error text-sm mt-1"
        ) 