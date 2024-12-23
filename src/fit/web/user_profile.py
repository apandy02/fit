import fasthtml.common as fh
from fit.web.common import page_outline
from fit.nutrition.data import Goals
from fit.trackers.manager import get_active_tracker_type, load_secrets, save_secrets


def get():
    """Return the profile page content"""
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
                    # Basic Information
                    fh.Card(
                        fh.Header(
                            fh.H3("Basic Information", cls="text-xl font-bold text-center mb-2 text-primary-content"),
                            cls="mb-6 bg-base-200"
                        ),
                        fh.Div(
                            # Name
                            create_form_row("Name", fh.Input(
                                type="text",
                                name="name",
                                placeholder="John Doe",
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-primary-content"
                            )),
                            # Email
                            create_form_row("Email", fh.Input(
                                type="email",
                                name="email",
                                placeholder="john@example.com",
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-primary-content"
                            )),
                            # Age
                            create_form_row("Age", fh.Input(
                                type="number",
                                name="age",
                                placeholder="30",
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-primary-content"
                            )),
                            cls="space-y-4"
                        ),
                        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6 mb-8"
                    ),
                    # Dietary Restrictions
                    fh.Card(
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
                                    name="dietary_restriction",
                                    hx_post="/add_restriction",
                                    hx_target="#restrictions-list",
                                    cls="select select-bordered w-full bg-base-200 text-primary-content mb-4"
                                ),
                                # Container for restriction tags
                                fh.Div(
                                    # Empty container for tags (will be populated dynamically)
                                    id="restrictions-list",
                                    cls="flex flex-wrap"
                                ),
                                cls="w-full"
                            )),
                            cls="space-y-4"
                        ),
                        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6 mb-8"
                    ),
                    # Fitness Goals
                    fh.Card(
                        fh.Header(
                            fh.H3("Fitness Goals", cls="text-xl font-bold text-center mb-2 text-primary-content"),
                            cls="mb-6 bg-base-200"
                        ),
                        fh.Div(
                            # Primary Goal
                            create_form_row("Primary Goal", fh.Select(
                                *[
                                    fh.Option(goal.value.title(), value=goal.value)
                                    for goal in Goals
                                ],
                                name="fitness_goal",
                                cls="select select-bordered w-full bg-base-200 text-primary-content"
                            )),
                            # Weekly Workout Target
                            create_form_row("Weekly Workouts", fh.Input(
                                type="number",
                                name="workout_target",
                                placeholder="5",
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-primary-content"
                            )),
                            cls="space-y-4"
                        ),
                        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6 mb-8"
                    ),
                    # Preferences
                    fh.Card(
                        fh.Header(
                            fh.H3("Preferences", cls="text-xl font-bold text-center mb-2 text-primary-content"),
                            cls="mb-6 bg-base-200"
                        ),
                        fh.Div(
                            # Units
                            create_form_row("Units", fh.Select(
                                fh.Option("Imperial (lbs, inches)", value="imperial", selected=True),
                                fh.Option("Metric (kg, cm)", value="metric"),
                                name="units",
                                cls="select select-bordered w-full bg-base-200 text-primary-content"
                            )),
                            cls="space-y-4"
                        ),
                        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6 mb-8"
                    ),
                    fh.Button(
                        "Save Changes",
                        type="submit",
                        cls="btn btn-primary outline outline-1 outline-primary-content w-full"
                    ),
                    fh.Div(id="profile-result")
                ),
                cls="bg-base-200 shadow-lg rounded-lg p-6 mb-8"
            ),
            # Tracker Management Section
            fh.Card(
                fh.Header(
                    fh.H3("Fitness Trackers", cls="text-2xl font-bold text-center mb-2 text-primary-content"),
                    cls="mb-6 bg-base-200"
                ),
                active_tracker_info(),
                credentials_section(),
                change_tracker_section(),
                cls="bg-base-200 shadow-lg rounded-lg p-6"
            ),
            cls="max-w-2xl mx-auto p-6 space-y-6"
        ),
        cls="bg-base-100"
    )
    return page_outline(6, "Profile", content)


def create_form_row(label: str, input_element):
    """Create a form row with label on the left and input on the right"""
    return fh.Div(
        fh.Label(label, cls="text-primary-content w-1/3 h-12 flex items-center"),
        fh.Div(input_element, cls="w-2/3"),
        cls="flex gap-4"
    )


def active_tracker_info():
    """Return information about the currently active tracker"""
    secrets = load_secrets()
    active_type = get_active_tracker_type()
    
    if not active_type or active_type not in secrets:
        return fh.Card(
            fh.P(
                "No active tracker configured",
                cls="text-primary-content text-center"
            ),
            cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6"
        )
    
    active_info = secrets[active_type]
    return fh.Card(
        fh.Header(
            fh.H3("Active Tracker", cls="text-xl font-bold text-center mb-2 text-primary-content"),
            cls="mb-4 bg-base-200"
        ),
        fh.Div(
            fh.P(
                fh.Span("Type: ", cls="font-semibold"),
                active_type.replace('_', ' ').title(),
                cls="mb-2 text-primary-content"
            ),
            fh.P(
                fh.Span("Username: ", cls="font-semibold"),
                active_info['username'],
                cls="mb-4 text-primary-content"
            ),
            cls="text-primary-content bg-base-200"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6"
    )


def credentials_section():
    """Return the credentials management section"""
    active_type = get_active_tracker_type()
    has_active = active_type is not None
    
    return fh.Card(
        fh.Header(
            fh.H3("Add New Tracker", cls="text-xl font-bold text-center mb-2 text-primary-content"),
            fh.P(
                "Connect a fitness tracker account",
                cls="text-primary-content text-center opacity-70"
            ),
            cls="mb-6 bg-base-200"
        ),
        fh.Form(
            hx_post="/connect_tracker",
            hx_target="#connection-result",
            cls="space-y-4"
        )(
            fh.Div(
                fh.Label("Select Tracker", cls="label text-primary-content"),
                fh.Select(
                    fh.Option("Select a tracker", value="", selected=True, disabled=True),
                    fh.Option("Fitbit", value="fitbit"),
                    fh.Option("Whoop", value="whoop"),
                    fh.Option("Apple Watch", value="apple_watch"),
                    fh.Option("Garmin", value="garmin"),
                    name="tracker_type",
                    cls="select select-bordered w-full bg-base-200 outline outline-1 outline-primary-content text-primary-content",
                    required=True
                ),
                cls="form-control"
            ),
            create_login_input_section("Username/Email", "username", placeholder="Enter username or email"),
            create_login_input_section("Password", "password", "password", placeholder="Enter password"),
            fh.Div(
                fh.Label(
                    fh.Input(
                        type="checkbox",
                        name="set_active",
                        cls="checkbox checkbox-primary mr-2"
                    ),
                    "Set as active tracker",
                    cls="label cursor-pointer justify-start gap-2 text-primary-content"
                ),
                cls="form-control"
            ) if has_active else "",
            fh.Input(
                type="hidden",
                name="first_tracker",
                value="true" if not has_active else "false"
            ),
            fh.Button(
                "Save Credentials",
                type="submit",
                cls="btn btn-primary outline outline-1"
            ),
            fh.Div(id="connection-result")
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6"
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


def change_tracker_section():
    """Return the section for changing active tracker"""
    secrets = load_secrets()
    active_type = get_active_tracker_type()
    
    if len(secrets) == 0 or (len(secrets) == 1 and active_type is not None):
        return ""
    
    return fh.Card(
        fh.Header(
            fh.H3("Change Active Tracker", cls="text-xl font-bold text-center mb-2 text-primary-content"),
            fh.P(
                "Switch to a different tracker",
                cls="text-primary-content text-center opacity-70"
            ),
            cls="mb-6"
        ),
        fh.Form(
            hx_post="/set_active_tracker",
            hx_target="#active-tracker-result",
            cls="space-y-4"
        )(
            fh.Div(
                fh.Label("Select Tracker", cls="label text-primary-content"),
                fh.Select(
                    [
                        fh.Option(
                            f"{tracker_type.replace('_', ' ').title()} ({info['username']})",
                            value=tracker_type,
                            selected=tracker_type == active_type
                        )
                        for tracker_type, info in secrets.items()
                    ],
                    name="active_tracker",
                    cls="select select-bordered w-full bg-base-200 outline outline-1 outline-primary-content text-primary-content",
                    required=True
                ),
                cls="form-control"
            ),
            fh.Button(
                "Set Active",
                type="submit",
                cls="btn btn-primary outline outline-1 outline-primary-content"
            ),
            fh.Div(id="active-tracker-result")
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg p-6"
    )


async def update_profile(request: fh.Request):
    """Handle profile update"""
    try:
        form = await request.form()
        # TODO: Save profile data to database
        return fh.P(
            "Profile updated successfully!",
            cls="text-green-500 font-semibold text-center mt-4"
        )
    except Exception as e:
        return fh.P(
            f"Error updating profile: {str(e)}",
            cls="text-red-500 font-semibold text-center mt-4"
        )


async def connect_tracker(
        tracker_type: str,
        username: str,
        password: str,
        set_active: bool = False,
        first_tracker: str = "false"
):
    """Handle tracker connection"""
    try:
        save_secrets(tracker_type, username, password)
        
        if first_tracker == "true" or set_active:
            set_active_tracker(tracker_type)
            active_msg = " and set as active tracker"
        else:
            active_msg = ""
            
        return fh.Div(
            fh.P(
                f"Successfully saved credentials for {tracker_type.replace('_', ' ').title()}{active_msg}!",
                cls="text-success font-semibold text-center mt-4"
            )
        )
    except Exception as e:
        return fh.Div(
            fh.P(
                "Failed to save tracker credentials.",
                cls="text-error font-semibold text-center mt-4"
            ),
            fh.P(
                str(e),
                cls="text-primary-content opacity-70 text-center text-sm mt-1"
            )
        )


async def set_active_tracker(active_tracker: str):
    """Handle setting the active tracker"""
    try:
        set_active_tracker(active_tracker)
        return fh.Div(
            fh.P(
                f"Successfully set {active_tracker.replace('_', ' ').title()} as active tracker!",
                cls="text-success font-semibold text-center mt-4"
            )
        )
    except Exception as e:
        return fh.Div(
            fh.P(
                "Failed to set active tracker.",
                cls="text-error font-semibold text-center mt-4"
            ),
            fh.P(
                str(e),
                cls="text-primary-content opacity-70 text-center text-sm mt-1"
            )
        )


async def add_restriction(request: fh.Request):
    """Handle adding a dietary restriction"""
    try:
        form = await request.form()
        restriction = form.get("dietary_restriction")
        # TODO: Save restriction to database
        
        # Get existing restrictions from the form
        existing_restrictions = form.getlist("existing_restrictions[]")
        if restriction not in existing_restrictions:
            existing_restrictions.append(restriction)
        
        # Create a div for each restriction
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
            # Hidden inputs to maintain state
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
        
        # Remove the restriction
        if restriction_to_remove in existing_restrictions:
            existing_restrictions.remove(restriction_to_remove)
        
        # Create a div for each remaining restriction
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
            # Hidden inputs to maintain state
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