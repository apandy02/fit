import fasthtml.common as fh

from fit.web.common import page_outline
from fit.web.user_profile.ui import (create_basic_info_card,
                                     create_dietary_restrictions_card)


def create_profile_page(user_data):
    """Create the profile page"""
    form = fh.Form(
            hx_post="/onboarding/complete_profile",
            cls="space-y-6"
            )(
            create_basic_info_card(user_data),
            fh.Button(
                "Next →",
                type="submit",
                cls="btn btn-base outline outline-1 outline-primary-content w-full mt-8 font-light"
            ),
        cls="p-6"
    )
    return onboarding_page(form, "Profile", "Profile")

def create_dietary_page(session):
    """Create the dietary page"""
    form = fh.Form(
        hx_post="/onboarding/complete_dietary",
        cls="space-y-6"
    )(
        create_dietary_restrictions_card([], hx_target="onboarding-restrictions-list"),  # Pass empty list for initial state
        fh.Button(
            "Next →",
            type="submit",
            cls="btn btn-base outline outline-1 outline-primary-content w-full mt-8 font-light"
        ),
        cls="p-6"
    )
    return onboarding_page(form, "Dietary Restrictions", "Dietary Restrictions")

def onboarding_page(form: fh.Form, page_title: str, header: str):
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Div(
                    fh.Header(
                        fh.H3(header, cls="text-2xl text-center mb-6 text-base-content font-light"),
                        cls="mb-6 bg-base-200"
                    ),
                    form,
                    cls="bg-base-200 rounded-lg p-6"
                ),
                cls="bg-base-200 shadow-lg rounded-lg"
            ),
            cls="max-w-2xl mx-auto p-6"
        ),
        cls="bg-base-100 min-h-screen flex items-center outline outline-1 outline-base-content"
    )
    return page_outline(None, page_title, False, False, content)

def create_activity_page(session):
    """Create the activity page"""
    header = "How Active Are You?"
    activity_options = [
        ("Not at all", "0 workouts per week", "sedentary"),
        ("Lightly active", "1-2 workouts per week", "lightly_active"),
        ("Active", "3-5 workouts per week", "active"), 
        ("Very active", "6+ workouts per week", "very_active")
    ]
    form = fh.Form(
        hx_post="/onboarding/handle_activity_selection",
        cls="space-y-6"
    )(
        fh.Div(
            *[onboarding_form_option(title, desc, val, i == len(activity_options)-1) 
              for i, (title, desc, val) in enumerate(activity_options)],
            cls="space-y-4"
        ),
        cls="p-6"
    )
    return onboarding_page(form, "Activity Level", header)

def onboarding_form_option(title, description, form_name, value, is_last=False):
    return fh.Button(
        fh.Div(
            fh.H4(title, cls="text-lg mb-2 text-base-content font-light"),
            fh.P(description, cls="text-sm text-slate font-light"),
            cls="text-center"
        ),
        type="submit",
        name=form_name, 
        value=value,
        cls=f"btn btn-ghost outline outline-1 outline-base-content w-full h-24 font-light{' mb-4' if not is_last else ''}"
    )

def create_goals_page(session):
    """Create the goals page"""
    header = "What are your weight goals?"
    form_name = "weight_goal"
    button_options = [
        ("Lose", "I want to reduce my body weight", form_name, "lose"),
        ("Maintain", "I want to maintain my current weight", form_name, "maintain"),
        ("Gain", "I want to increase my body weight", form_name, "gain")
    ]
    form = fh.Form(
        hx_post="/onboarding/handle_goals_selection",
        cls="space-y-6"
    )(
        fh.Div(
            fh.Div(
                *[onboarding_form_option(title, desc, form_name, val, i == len(button_options)-1) 
                    for i, (title, desc, form_name, val) in enumerate(button_options)],
                cls="space-y-4"
            ),
            cls="mb-8"
        ),
    cls="p-6"
    )
    return onboarding_page(form, "Goals", header)

def create_measurements_page(session):
    """Create the measurements page"""
    form = fh.Form(
        hx_post="/onboarding/complete_measurements",
        cls="space-y-6"
    )(
        fh.Card(
            fh.Header(
                fh.H3("Body Measurements", cls="text-xl text-center mb-2 text-base-content font-light"),
                cls="mb-6 bg-base-200"
            ),
            fh.Div(
                fh.Div(
                    fh.Label("Weight (lbs)", cls="label text-base-content font-light"),
                    fh.Input(
                        type="number",
                        name="weight",
                        step="0.1",
                        min="0",
                        required=True,
                        placeholder="Enter your weight",
                        cls="input input-bordered w-full bg-base-200 text-base-content font-light"
                    ),
                    cls="form-control mb-4"
                ),
                fh.Div(
                    fh.Label("Height", cls="label text-base-content font-light"),
                    fh.Div(
                        fh.Div(
                            fh.Label("Feet", cls="label text-base-content font-light"),
                            fh.Input(
                                type="number",
                                name="height_feet",
                                step="1",
                                min="0",
                                max="9",
                                placeholder="ft",
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-base-content font-light"
                            ),
                            cls="form-control"
                        ),
                        fh.Div(
                            fh.Label("Inches", cls="label text-base-content font-light"),
                            fh.Input(
                                type="number",
                                name="height_inches",
                                min="0",
                                max="11",
                                placeholder="in",
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-base-content font-light"
                            ),
                            cls="form-control"
                        ),
                        cls="grid grid-cols-2 gap-4"
                    ),
                    cls="form-control"
                ),
                cls="space-y-4"
            ),
            cls="bg-base-200 outline outline-1 outline-base-content rounded-lg p-6 mb-8 shadow-none"
        ),
        fh.Button(
            "Next →",
            type="submit",
            cls="btn btn-base outline outline-1 outline-primary-content w-full mt-8 font-light"
        ),
        cls="p-6"
    )
    return onboarding_page(form, "Measurements", "Body Measurements")
