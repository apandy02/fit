import fasthtml.common as fh
from datetime import datetime
from fit.nutrition.data import Goals
from fit.web.common import MEASUREMENTS_TABLE, page_outline

def get():
    """Return the personal information page content"""
    content = fh.Article(
        fh.Form(
            hx_post="/update_personal",
            hx_target="#update-result",
            cls="space-y-6 max-w-lg mx-auto p-6"
        )(
            # Weight section
            fh.Div(
                fh.Label("Weight (lbs)", cls="label"),
                fh.Input(
                    type="number",
                    name="weight",
                    min="0",
                    step="0.1",
                    placeholder="Enter your weight",
                    cls="input input-bordered w-full"
                ),
                cls="form-control"
            ),
            # Height section
            fh.Div(
                fh.Label("Height", cls="label"),
                fh.Div(
                    fh.Div(
                        fh.Label("Feet", cls="label"),
                        fh.Input(
                            type="number",
                            name="height_feet",
                            min="0",
                            max="9",
                            placeholder="ft",
                            cls="input input-bordered w-24"
                        ),
                        cls="form-control"
                    ),
                    fh.Div(
                        fh.Label("Inches", cls="label"),
                        fh.Input(
                            type="number",
                            name="height_inches",
                            min="0",
                            max="11",
                            placeholder="in",
                            cls="input input-bordered w-24"
                        ),
                        cls="form-control"
                    ),
                    cls="flex space-x-4"
                )
            ),
            # Fitness goal section
            fh.Div(
                fh.Label("Fitness Goal", cls="label"),
                fh.Select(
                    *[
                        fh.Option(goal.value.title(), value=goal.value)
                        for goal in Goals
                    ],
                    name="fitness_goal",
                    cls="select select-bordered w-full"
                ),
                cls="form-control"
            ),
            # Submit button
            fh.Button(
                "Update Information",
                type="submit",
                cls="btn btn-primary w-full mt-6"
            ),
            fh.Div(id="update-result")
        )
    )
    return page_outline(2, "Personal Information", content)

async def update_personal(weight: float, height_feet: int, height_inches: int, fitness_goal: str):
    """Handle personal information update"""
    # Convert height to total inches for storage
    total_height = (height_feet * 12) + height_inches
    
    # Store in database
    MEASUREMENTS_TABLE.insert(
        datetime=datetime.now().isoformat(),
        height=total_height,
        weight=weight
    )
    
    # Return success message
    return fh.Div(
        fh.P(
            "Information updated successfully!",
            cls="text-green-600 font-semibold text-center mt-4"
        )
    ) 