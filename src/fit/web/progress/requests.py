
from datetime import datetime

import fasthtml.common as fh

import fit.web.progress.ui as ui
from fit.web.common import database_service


def get(session):
    """Return the progress tracking page content"""
    measurements = database_service.get_user_measurements(session["user_id"])
    print("measurements: ", measurements)
    return ui.create_progress_page(session, measurements)

def get_latest_measurements(user_id: int):
    """Get the latest measurements from the database"""
    latest = database_service.get_latest_user_measurements(user_id)
    
    if latest:
        weight = latest["weight"] if latest["weight"] is not None else 0
        height = latest["height"] if latest["height"] is not None else 0
        feet = height // 12 if height > 0 else 0
        inches = height % 12 if height > 0 else 0
    else:
        weight, feet, inches = 0, 0, 0
    
    return weight, feet, inches

async def update_measurements(session, request: fh.Request):
    """Handle measurements update"""
    form = await request.form()
    weight = float(form["weight"])
    height_feet = float(form["height_feet"])
    height_inches = float(form["height_inches"])
    total_height = (height_feet * 12) + height_inches
    database_service.insert_user_measurements(
        total_height, weight, datetime.now(), session["user_id"]
    )

    return fh.Div(
        fh.P(
            "Measurements updated successfully!",
            cls="text-green-600 font-semibold text-center mt-4"
        ),
        fh.Script("""
            setTimeout(() => {
                closeMeasurementsModal();
                window.location.reload();
            }, 1000);
        """)
    ) 