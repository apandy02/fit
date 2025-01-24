from datetime import datetime

import fasthtml.common as fh
from fasthtml.common import RedirectResponse
from fasthtml.oauth import redir_url

import fit.web.kitchen.requests as kitchen
import fit.web.nutrition.requests as nutrition
import fit.web.performance as performance
import fit.web.progress as progress
import fit.web.rest as rest
import fit.web.user_profile as user_profile
from fit.web.auth.clients import fitbit_client_oauth as fitbit_client
from fit.web.auth.clients import whoop_client_oauth as whoop_client
from fit.web.auth.login_page import get_login_page

# Add htmx-indicator style before other CSS
htmx_indicator_style = fh.Style("""
.htmx-indicator {
    opacity: 0;
    transition: opacity 200ms ease-in;
}
""")

tlink = (fh.Script(src="https://cdn.tailwindcss.com"),)
amcharts = [
    fh.Script(src="https://cdn.amcharts.com/lib/5/index.js"),
    fh.Script(src="https://cdn.amcharts.com/lib/5/percent.js"),
    fh.Script(src="https://cdn.amcharts.com/lib/5/themes/Dark.js")
]
plotly = fh.Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js")

dlink = fh.Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.css",
)
modal_css = fh.Link(rel="stylesheet", href="/static/public/modal.css")

def before(req, session):
    access_token_expiry = session.get('access_token_expiry', None)
    req.scope['auth'] = access_token_expiry
    
    # Check if token is missing or expired
    if not access_token_expiry or datetime.now().timestamp() > access_token_expiry:
        return RedirectResponse('/login', status_code=303)
        
    # fh.counts.xtra(name=access_token_expiry)

auth_callback_path = "/auth_redirect"

fitbit_auth_callback_path = auth_callback_path + '/fitbit'
whoop_auth_callback_path = auth_callback_path + '/whoop'

fitbit_scope = ["activity", "heartrate", "profile"]
whoop_scope = ["offline", "read:recovery", "read:cycles", "read:workout", "read:sleep", "read:profile"]

bware = fh.Beforeware(before, skip=['/login', auth_callback_path, fitbit_auth_callback_path, whoop_auth_callback_path])
app = fh.FastHTML(before=bware, hdrs=(htmx_indicator_style, tlink, *amcharts, plotly, dlink, fh.picolink, modal_css))

# Food routes
app.get("/nutrition/weekly")(nutrition.get_weekly_overview)
app.get("/nutrition/{date}")(nutrition.get_daily_overview)
app.get("/nutrition")(nutrition.get_daily_overview)
app.post("/analyze_text")(nutrition.analyze_text)
app.post("/analyze_text/{date:str}")(nutrition.analyze_text)
app.post("/analyze_image")(nutrition.analyze_image)
app.post("/analyze_image/{date:str}")(nutrition.analyze_image)
app.post("/generate_daily_nutrition_overview/{date:str}")(nutrition.generate_daily_overview)
app.post("/generate_daily_nutrition_overview")(nutrition.generate_daily_overview)
app.post("/generate_weekly_nutrition_overview")(nutrition.generate_weekly_overview)
app.post("/save_meal")(nutrition.save_meal)
app.post("/save_meal/{date:str}")(nutrition.save_meal)
app.post("/delete_meal/{meal_id:int}")(nutrition.delete_meal)
app.post("/reset_text_form")(nutrition.reset_text_form)
app.post("/regenerate_analysis")(nutrition.regenerate_analysis)
app.post("/hide_metric/{plot_id}")(nutrition.hide_metric)
app.post("/show_metric/{plot_id}")(nutrition.show_metric)
app.get("/toggle_dropdown/{dropdown_id}")(nutrition.toggle_dropdown)
app.post("/nutrition_redirect")(nutrition.nutrition_redirect)
app.post("/save_supplement")(nutrition.save_supplement)
app.get("/get_supplements")(nutrition.get_supplements)
app.post("/get_nutrient_suggestions/{nutrient}")(nutrition.get_nutrient_suggestions)
app.post("/log_supplement_consumption")(nutrition.log_supplement_consumption)
app.post("/log_supplement_consumption/{date:str}")(nutrition.log_supplement_consumption)
app.post("/log_water")(nutrition.log_water)
app.post("/log_water/{date:str}")(nutrition.log_water)

# Kitchen routes
app.get("/kitchen")(kitchen.get)
app.post("/add_item")(kitchen.add_item)
app.post("/decipher_text_inventory_addition")(kitchen.add_inventory_from_text)
app.post("/save_inventory")(kitchen.save_inventory)
app.get("/get_inventory")(kitchen.get_inventory)
app.route("/delete_inventory_item/{rowid:int}", methods=["POST"])(kitchen.delete_inventory_item)
app.post("/generate_inventory_additions")(kitchen.generate_inventory_additions)
# Progress routes
app.get("/progress")(progress.get)
app.post("/update_measurements")(progress.update_measurements)

# Profile routes
app.get("/profile")(user_profile.get)
app.post("/update_profile")(user_profile.update_profile)
app.post("/add_restriction")(user_profile.add_restriction)
app.post("/remove_restriction")(user_profile.remove_restriction)

# rest routes
app.get("/rest")(rest.get)

# performance routes
app.get("/performance")(performance.get)


fh.reg_re_param("imgext", "png")


@app.get(r"/static/{path:path}")
def get(path: str):
    return fh.FileResponse(f"{path}")

@app.get('/')
def home(auth): return fh.P('Logged in!'), fh.A('Log out', href='/logout')

@app.get('/login')
def login(req):
    fitbit_redir = redir_url(req, f"{auth_callback_path}/fitbit")
    whoop_redir = redir_url(req, f"{auth_callback_path}/whoop")
    fitbit_login_link = fitbit_client.login_link(fitbit_redir, scope=fitbit_scope)
    whoop_login_link = whoop_client.login_link(whoop_redir, scope=whoop_scope)
    return get_login_page(req, fitbit_login_link=fitbit_login_link, whoop_login_link=whoop_login_link)

@app.get(fitbit_auth_callback_path)
def fitbit_auth_redirect(code:str, request, session):
    redir = redir_url(request, f"{auth_callback_path}/fitbit")
    access_token_dict = fitbit_client.fetch_access_token(code, redir)
    session['access_token'] = access_token_dict['access_token']
    session['access_token_expiry'] = access_token_dict['expires_at']
    session['refresh_token'] = access_token_dict['refresh_token']
    session["tracker"] = "fitbit"
    return RedirectResponse('/nutrition', status_code=303)

@app.get(whoop_auth_callback_path)
def whoop_auth_redirect(code:str, request, session):
    redir = redir_url(request, whoop_auth_callback_path)
    access_token_dict = whoop_client.fetch_access_token(code, redir)
    session['access_token'] = access_token_dict['access_token']
    session['access_token_expiry'] = access_token_dict['expires_at']
    session['refresh_token'] = access_token_dict['refresh_token']
    session["tracker"] = "whoop"
    return RedirectResponse('/nutrition', status_code=303)


fh.serve() 


