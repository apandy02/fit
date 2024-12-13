import fasthtml.common as fh
from fit.web.common import page_outline
from fit.trackers.manager import load_secrets, get_active_tracker_type, get_active_tracker

def active_tracker_info():
    """Return information about the currently active tracker"""
    secrets = load_secrets()
    active_type = get_active_tracker_type()
    
    if not active_type or active_type not in secrets:
        return fh.Card(
            fh.P(
                "No active tracker configured",
                cls="text-gray-600 text-center"
            ),
            cls="bg-white shadow-lg rounded-lg p-6"
        )
    
    active_info = secrets[active_type]
    return fh.Card(
        fh.Header(
            fh.H3("Active Tracker", cls="text-xl font-bold text-center mb-2"),
            cls="mb-4"
        ),
        fh.Div(
            fh.P(
                fh.Span("Type: ", cls="font-semibold"),
                active_type.replace('_', ' ').title(),
                cls="mb-2"
            ),
            fh.P(
                fh.Span("Username: ", cls="font-semibold"),
                active_info['username'],
                cls="mb-4"
            ),
            cls="text-gray-600"
        ),
        cls="bg-white shadow-lg rounded-lg p-6"
    )

def credentials_section():
    """Return the credentials management section"""
    active_type = get_active_tracker_type()
    has_active = active_type is not None
    
    return fh.Card(
        fh.Header(
            fh.H3("Add New Tracker", cls="text-xl font-bold text-center mb-2"),
            fh.P(
                "Connect a fitness tracker account",
                cls="text-gray-600 text-center"
            ),
            cls="mb-6"
        ),
        fh.Form(
            hx_post="/connect_tracker",
            hx_target="#connection-result",
            cls="space-y-4"
        )(
            fh.Div(
                fh.Label("Select Tracker", cls="label"),
                fh.Select(
                    fh.Option("Select a tracker", value="", selected=True, disabled=True),
                    fh.Option("Fitbit", value="fitbit"),
                    fh.Option("Whoop", value="whoop"),
                    fh.Option("Apple Watch", value="apple_watch"),
                    fh.Option("Garmin", value="garmin"),
                    name="tracker_type",
                    cls="select select-bordered w-full",
                    required=True
                ),
                cls="form-control"
            ),
            fh.Div(
                fh.Label("Username/Email", cls="label"),
                fh.Input(
                    type="text",
                    name="username",
                    placeholder="Enter your tracker account username or email",
                    cls="input input-bordered w-full",
                    required=True
                ),
                cls="form-control"
            ),
            fh.Div(
                fh.Label("Password", cls="label"),
                fh.Input(
                    type="password",
                    name="password",
                    placeholder="Enter your tracker account password",
                    cls="input input-bordered w-full",
                    required=True
                ),
                cls="form-control"
            ),
            # Only show "Set as active" checkbox if there's already an active tracker
            fh.Div(
                fh.Label(
                    fh.Input(
                        type="checkbox",
                        name="set_active",
                        cls="checkbox checkbox-primary mr-2"
                    ),
                    "Set as active tracker",
                    cls="label cursor-pointer justify-start gap-2"
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
                cls="btn btn-primary w-full mt-2"
            ),
            fh.Div(id="connection-result")
        ),
        cls="bg-white shadow-lg rounded-lg p-6"
    )

def change_tracker_section():
    """Return the section for changing active tracker"""
    secrets = load_secrets()
    active_type = get_active_tracker_type()
    
    # Only show if there are multiple trackers or if there are trackers but none active
    if len(secrets) == 0 or (len(secrets) == 1 and active_type is not None):
        return ""
    
    return fh.Card(
        fh.Header(
            fh.H3("Change Active Tracker", cls="text-xl font-bold text-center mb-2"),
            fh.P(
                "Switch to a different tracker",
                cls="text-gray-600 text-center"
            ),
            cls="mb-6"
        ),
        fh.Form(
            hx_post="/set_active_tracker",
            hx_target="#active-tracker-result",
            cls="space-y-4"
        )(
            fh.Div(
                fh.Label("Select Tracker", cls="label"),
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
                    cls="select select-bordered w-full",
                    required=True
                ),
                cls="form-control"
            ),
            fh.Button(
                "Set Active",
                type="submit",
                cls="btn btn-primary w-full mt-2"
            ),
            fh.Div(id="active-tracker-result")
        ),
        cls="bg-white shadow-lg rounded-lg p-6"
    )

def get():
    """Return the tracker integration page content"""
    content = fh.Article(
        fh.Div(
            active_tracker_info(),
            credentials_section(),
            change_tracker_section(),
            cls="max-w-lg mx-auto p-6 space-y-6"
        )
    )
    return page_outline(4, "Tracker Management", content)

async def connect_tracker(tracker_type: str, username: str, password: str, set_active: bool = False, first_tracker: str = "false"):
    """Handle tracker connection"""
    try:
        save_credentials(tracker_type, username, password)
        
        # Set as active if it's the first tracker or if requested
        if first_tracker == "true" or set_active:
            set_active_tracker(tracker_type)
            active_msg = " and set as active tracker"
        else:
            active_msg = ""
            
        return fh.Div(
            fh.P(
                f"Successfully saved credentials for {tracker_type.replace('_', ' ').title()}{active_msg}!",
                cls="text-green-600 font-semibold text-center mt-4"
            )
        )
    except Exception as e:
        return fh.Div(
            fh.P(
                "Failed to save tracker credentials.",
                cls="text-red-600 font-semibold text-center mt-4"
            ),
            fh.P(
                str(e),
                cls="text-gray-600 text-center text-sm mt-1"
            )
        )

async def set_active_tracker(active_tracker: str):
    """Handle setting the active tracker"""
    try:
        set_active_tracker(active_tracker)
        return fh.Div(
            fh.P(
                f"Successfully set {active_tracker.replace('_', ' ').title()} as active tracker!",
                cls="text-green-600 font-semibold text-center mt-4"
            )
        )
    except Exception as e:
        return fh.Div(
            fh.P(
                "Failed to set active tracker.",
                cls="text-red-600 font-semibold text-center mt-4"
            ),
            fh.P(
                str(e),
                cls="text-gray-600 text-center text-sm mt-1"
            )
        ) 