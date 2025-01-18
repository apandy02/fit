import fasthtml.common as fh

import fit.web.nutrition.requests as nutrition
import fit.web.performance as performance
import fit.web.progress as progress
import fit.web.rest as rest
from fit.web.auth.login_page import get_login_page
import fit.web.user_profile as user_profile
import fit.web.kitchen.requests as kitchen
from fasthtml.oauth import OAuth, redir_url
from fasthtml.common import RedirectResponse
from fit.web.auth.clients import fitbit_client_oauth as fitbit_client
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
app = fh.FastHTML(hdrs=(tlink, *amcharts, plotly, dlink, fh.picolink, modal_css))

# Food routes
app.get("/nutrition/weekly")(nutrition.get_weekly_overview)
app.get("/nutrition/{date}")(nutrition.get_daily_overview)
app.get("/nutrition")(nutrition.get_daily_overview)
app.post("/analyze_text")(nutrition.analyze_text)
app.post("/analyze_text/{date:str}")(nutrition.analyze_text)
app.post("/analyze_image")(nutrition.analyze_image)
app.post("/analyze_image/{date:str}")(nutrition.analyze_image)
app.post("/generate_daily_overview/{date:str}")(nutrition.generate_daily_overview)
app.post("/generate_daily_overview")(nutrition.generate_daily_overview)
app.post("/generate_weekly_overview")(nutrition.generate_weekly_overview)
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

# Progress routes
app.get("/progress")(progress.get)
app.post("/update_measurements")(progress.update_measurements)

# Profile routes
app.get("/profile")(user_profile.get)
app.post("/update_profile")(user_profile.update_profile)
app.post("/connect_tracker")(user_profile.connect_tracker)
app.post("/set_active_tracker")(user_profile.set_active_tracker)
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

auth_callback_path = "/auth_redirect"
def before(req, session):
    auth = req.scope['auth' ] = session.get('user_id', None)
    if not auth: return RedirectResponse('/login', status_code=303)
    fh.counts.xtra(name=auth)
bware = fh.Beforeware(before, skip=['/login', auth_callback_path])

@app.get('/login')
def login(req):
    redir = redir_url(req, auth_callback_path)
    login_link = fitbit_client.login_link(redir, scope=scope)
    print(login_link)
    return get_login_page(req, fitbit_login_link=login_link)



@app.get(auth_callback_path)
def auth_redirect(code:str, request):
    redir = redir_url(request, auth_callback_path)
    print(fitbit_client.__dir__())
    print(f"fitbit_client.token: {fitbit_client.token}")
    user_info = fitbit_client.fetch_access_token(code, redir)
    print(f"user_info: {user_info}")
    #print(user_info)


scope = ["activity", "heartrate", "profile"]


fh.serve() 


