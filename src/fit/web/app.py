import fasthtml.common as fh
import fit.web.food as food
import fit.web.personal as personal
import fit.web.progress as progress
from fit.web.common import page_outline


tlink = (fh.Script(src="https://cdn.tailwindcss.com"),)
dlink = fh.Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.css",
)
modal_css = fh.Link(rel="stylesheet", href="/static/public/modal.css")
app = fh.FastHTML(hdrs=(tlink, dlink, fh.picolink, modal_css))

# Food routes
app.get("/food")(food.get)
app.post("/analyze_text")(food.analyze_text)
app.post("/analyze_image")(food.analyze_image)

# Personal routes
app.get("/personal")(personal.get)
app.post("/update_personal")(personal.update_personal)

# Progress routes
app.get("/progress")(progress.get)

fh.serve() 