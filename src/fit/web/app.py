import fasthtml.common as fh

import fit.web.food as food
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
app.post("/generate_overview")(food.generate_overview)
app.post("/save_meal")(food.save_meal)
app.post("/reset_text_form")(food.reset_text_form)
app.post("/regenerate_analysis")(food.regenerate_analysis)

# Progress routes
app.get("/progress")(progress.get)
app.post("/update_weight")(progress.update_weight)
app.post("/update_height")(progress.update_height)
app.post("/update_goal")(progress.update_goal)

# Tracker routes
app.get("/trackers")(trackers.get)
app.post("/connect_tracker")(trackers.connect_tracker)
app.post("/set_active_tracker")(trackers.set_active_tracker)

fh.reg_re_param("imgext", "png")


@app.get(r"/static/{path:path}")
def get(path: str):
    return fh.FileResponse(f"{path}")

fh.serve() 