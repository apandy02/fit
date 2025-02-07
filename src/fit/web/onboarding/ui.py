import fasthtml.common as fh
from fit.web.common import page_outline
from fit.web.user_profile import (create_basic_info_card,
                                  create_dietary_restrictions_card)


def create_profile_page(user_data):
    """Create the profile page"""
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Form(
                    hx_post="/onboarding/complete_profile",
                    cls="space-y-6"
                )(
                    create_basic_info_card(user_data),
                    fh.Button(
                        "Next →",
                        type="submit",
                        cls="btn btn-primary outline outline-1 outline-primary-content w-full mt-8"
                    ),
                    cls="p-6"
                ),
                cls="bg-base-200 shadow-lg rounded-lg"
            ),
            cls="max-w-2xl mx-auto p-6"
        ),
        cls="bg-base-100 min-h-screen flex items-center"
    )
    
    return page_outline(None, "Complete Profile", False, False, content)

def create_dietary_page(session):
    """Create the dietary page"""
    
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Div(
                    fh.Form(
                        hx_post="/onboarding/complete_dietary",
                        cls="space-y-6"
                    )(
                        create_dietary_restrictions_card([], hx_target="onboarding-restrictions-list"),  # Pass empty list for initial state
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

    return page_outline(None, "Dietary Restrictions", False, False, content)

def create_activity_page(session):
    """Create the activity page"""
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Div(
                    fh.Header(
                        fh.H3("How Active Are You?", cls="text-2xl font-bold text-center mb-6 text-primary-content"),
                        cls="mb-6 bg-base-200"
                    ),
                    fh.Form(
                        hx_post="/onboarding/handle_activity_selection",
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

def create_goals_page(session):
    """Create the goals page"""
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Div(
                    fh.Header(
                        fh.H3("What are your weight goals?", cls="text-2xl font-bold text-center mb-6 text-primary-content"),
                        cls="mb-6 bg-base-200"
                    ),
                    fh.Form(
                        hx_post="/onboarding/handle_goals_selection",
                        cls="space-y-6"
                    )(
                        fh.Div(
                            fh.Div(
                                fh.Button(
                                    fh.Div(
                                        fh.H4("Lose", cls="text-lg font-bold mb-2 text-primary-content"),
                                        fh.P("I want to reduce my body weight", cls="text-sm"),
                                        cls="text-center"
                                    ),
                                    type="submit",
                                    name="weight_goal",
                                    value="lose",
                                    cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                                ),
                                fh.Button(
                                    fh.Div(
                                        fh.H4("Maintain", cls="text-lg font-bold mb-2 text-primary-content"),
                                        fh.P("I want to maintain my current weight", cls="text-sm"),
                                        cls="text-center"
                                    ),
                                    type="submit",
                                    name="weight_goal",
                                    value="maintain",
                                    cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                                ),
                                fh.Button(
                                    fh.Div(
                                        fh.H4("Gain", cls="text-lg font-bold mb-2 text-primary-content"),
                                        fh.P("I want to increase my body weight", cls="text-sm"),
                                        cls="text-center"
                                    ),
                                    type="submit",
                                    name="weight_goal",
                                    value="gain",
                                    cls="btn btn-ghost outline outline-1 outline-primary-content w-full h-24 mb-4"
                                ),
                                cls="space-y-4"
                            ),
                            cls="mb-8"
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

    return page_outline(None, "Goals", False, False, content)
