import fasthtml.common as fh
import fit.web.food as food
from fit.web.common import page_outline


tlink = (fh.Script(src="https://cdn.tailwindcss.com"),)
dlink = fh.Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.css",
)
modal_css = fh.Link(rel="stylesheet", href="/static/public/modal.css")
app = fh.FastHTML(hdrs=(tlink, dlink, fh.picolink, modal_css))

app.get("/food")(food.get)
app.post("/analyze_text")(food.analyze_text)
app.post("/analyze_image")(food.analyze_image)

fh.serve() 