import fasthtml.common as fh
import fit.web.food as food
import fit.web.personal as personal
import fit.web.progress as progress
import fit.web.trackers as trackers


tlink = (fh.Script(src="https://cdn.tailwindcss.com"),)
plotly = fh.Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js")
dlink = fh.Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.css",
)
modal_css = fh.Link(rel="stylesheet", href="/static/public/modal.css")
app = fh.FastHTML(hdrs=(tlink, plotly, dlink, fh.picolink, modal_css))

# Food routes
app.get("/food")(food.get)
app.post("/analyze_text")(food.analyze_text)
app.post("/analyze_image")(food.analyze_image)

# Personal routes
app.get("/personal")(personal.get)
app.post("/update_personal")(personal.update_personal)

# Progress routes
app.get("/progress")(progress.get)

# Tracker routes
app.get("/trackers")(trackers.get)
app.post("/connect_tracker")(trackers.connect_tracker)
app.post("/set_active_tracker")(trackers.set_active_tracker)

fh.serve() 