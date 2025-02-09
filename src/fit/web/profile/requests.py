import fasthtml.common as fh

from fit.web.common import database_service
import fit.web.profile.ui as ui

def get(session):
    """Return the profile page content"""
    user_data = database_service.get_profile_data(session["user_id"])
    restrictions = user_data.get("dietary_restrictions", "")
    if restrictions == "" or restrictions is None:
        restrictions = []
    else:
        restrictions = restrictions.split(",")

    return ui.create_profile_page(user_data, restrictions)

async def update_profile(session, request: fh.Request):
    try:
        form = await request.form()
        restrictions = form.getlist("existing_restrictions[]")
        form_data = dict(form)
        form_data["dietary_restrictions"] = ",".join(restrictions) if restrictions else ""
        form_data["user_id"] = session["user_id"]
        
        if "existing_restrictions[]" in form_data:
            form_data.pop("existing_restrictions[]")
        
        database_service.update_profile(form_data)
        
        return fh.P(
            "Profile updated successfully!",
            cls="text-success font-semibold text-center mt-4"
        )
    except Exception as e:
        return fh.P(
            f"Error updating profile: {str(e)}",
            cls="text-error font-semibold text-center mt-4"
        )

async def add_restriction(request: fh.Request):
    try:
        form = await request.form()
        restriction = form.get("dietary_restrictions")
        existing_restrictions = form.getlist("existing_restrictions[]")
        if restriction not in existing_restrictions:
            existing_restrictions.append(restriction)
        
        return ui.create_restriction_list(existing_restrictions)
    except Exception as e:
        return fh.P(
            f"Error adding restriction: {str(e)}",
            cls="text-error text-sm mt-1"
        )

async def remove_restriction(request: fh.Request):
    try:
        form = await request.form()
        restriction_to_remove = form.get("restriction")
        existing_restrictions = form.getlist("existing_restrictions[]")
        if restriction_to_remove in existing_restrictions:
            existing_restrictions.remove(restriction_to_remove)
        
        return ui.create_restriction_list(existing_restrictions)
    
    except Exception as e:
        return fh.P(
            f"Error removing restriction: {str(e)}",
            cls="text-error text-sm mt-1"
        ) 