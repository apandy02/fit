import fasthtml.common as fh
from fit.web.common import nutritionist
from fit.web.food_plots import create_plot


def metric_card(title: str, y_axis_title: str, plot_id: str, consumed: float, goal: float, burned: float = None, show_analysis: bool = True, allow_hide: bool = True):
    """Create a card containing a metric plot"""
    plot_data, plot_layout = create_plot(title, y_axis_title, consumed, goal, burned)
    
    analysis_text = None
    if show_analysis:
        macro_name = title.lower()
        if macro_name == "carbohydrates":
            macro_name = "carbohydrate"
        analysis_text = nutritionist.macro_analysis(macro_name, consumed, goal)
    
    hide_button = None
    if allow_hide and title.lower() not in ["calories", "water", "creatine"]:
        hide_button = fh.Button(
            "×",
            cls="absolute right-2 top-2 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
            style="outline: none; box-shadow: none;",
            hx_post=f"/hide_metric/{plot_id}",
            hx_target=f"#{plot_id}-container",
            hx_swap="outerHTML"
        )
    
    return fh.Card(
        fh.Div(
            hide_button if hide_button else None,
            fh.Div(id=plot_id, cls="w-full h-full"),
            fh.Script(
                f"""
                Plotly.newPlot(
                    '{plot_id}',
                    {plot_data},
                    {plot_layout},
                    {{responsive: true}}
                );
                """
            ),
            fh.P(analysis_text, cls="text-sm text-primary-content mt-4") if analysis_text else None,
            cls="p-4 relative"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg h-full text-primary-content",
        id=f"{plot_id}-container"
    )

def create_meal_prompt_form(
    title: str,
    textarea_label: str,
    textarea_placeholder: str,
    submit_text: str,
    hx_post_url: str,
    hx_target: str = "#text-input",
    extra_fields: list = None,
    header_buttons: list = None,
    rows: int = 3
):
    """Create a form for meal description or refinement input."""
    header_content = fh.H3(title, cls="text-xl font-bold text-primary-content")
    if header_buttons:
        header_content = fh.Div(
            header_content,
            *header_buttons,
            cls="flex justify-between items-center"
        )
    
    return fh.Card(
        fh.Div(
            fh.Header(
                header_content,
                cls="mb-6"
            ),
            fh.Form(
                hx_post=hx_post_url,
                hx_target=hx_target,
                hx_swap="outerHTML",
                cls="space-y-4"
            )(
                fh.Div(
                    fh.Label(textarea_label, cls="label text-primary-content"),
                    fh.Textarea(
                        name="meal_description" if "analyze" in hx_post_url else "feedback",
                        placeholder=textarea_placeholder,
                        rows=rows,
                        cls="textarea textarea-bordered w-full bg-base-200 outline text-primary-content placeholder-slate-400"
                    ),
                    cls="form-control"
                ),
                *(extra_fields or []),
                fh.Button(
                    submit_text,
                    type="submit",
                    cls="btn bg-primary"
                )
            ),
            cls="p-6"
        ),
        cls="bg-base-200 rounded-lg"
    )

def create_text_input_form(is_feedback: bool = False, original_description: str = None):
    """Create the text input form for meal description"""
    if not is_feedback:
        return create_meal_prompt_form(
            title="Describe Your Meal",
            textarea_label="Meal Description",
            textarea_placeholder="Example: I had a grilled chicken sandwich with lettuce, tomato and mayo",
            submit_text="Analyze Description",
            hx_post_url="/analyze_text",
            rows=3
        )
    else:
        return create_meal_prompt_form(
            title="Refine Analysis",
            textarea_label="Suggest Edits",
            textarea_placeholder="Suggest edits to improve the analysis",
            submit_text="Regenerate",
            hx_post_url="/regenerate_analysis",
            hx_target="#text-input",
            rows=2,
            extra_fields=[
                fh.Input(
                    type="hidden",
                    name="original_description",
                    id="original_description",
                    value=original_description
                )
            ],
            header_buttons=[
                fh.Button(
                    "↺",
                    hx_post="/reset_text_form",
                    hx_target="#text-input",
                    cls="btn btn-ghost text-xl text-primary-content"
                )
            ]
        )

def create_image_upload_form():
    """Create the image upload form"""
    return fh.Card(
        fh.Div(
            fh.Header(
                fh.H3("Upload Food Image", cls="text-xl font-bold text-primary-content"),
                cls="mb-6"
            ),
            fh.Form(
                hx_post="/analyze_image",
                hx_target="#image-result",
                hx_encoding="multipart/form-data",
                cls="space-y-4"
            )(
                fh.Div(
                    fh.Label("Food Image", cls="label"),
                    fh.Input(
                        type="file",
                        name="food_image",
                        accept="image/*",
                        cls="file-input file-input-bordered w-full text-sm"
                    ),
                    cls="form-control"
                ),
                fh.Button(
                    "Upload & Analyze",
                    type="submit",
                    cls="btn btn-primary"
                ),
                fh.Div(id="image-result", cls="mt-4")
            ),
            cls="p-6"
        ),
        cls="bg-base-200 shadow-lg rounded-lg"
    )

def create_modal_content():
    """Create the content for the food tracking modal"""
    return fh.Div(
        # Close button
        fh.Button(
            "×",
            cls="absolute right-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 focus:ring-offset-0 border-none outline-none z-10",
            onclick="closeModal()",
            style="outline: none; box-shadow: none;"
        ),
        # Back button (shown only when a form is visible)
        fh.Button(
            "←",
            cls="absolute left-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 focus:ring-offset-0 border-none outline-none hidden z-10",
            onclick="showInputSelection()",
            style="outline: none; box-shadow: none;",
            id="back-button"
        ),
        # Initial selection view
        fh.Div(
            fh.Div(
                fh.H3("How would you like to log your meal?", cls="text-xl font-bold text-center mb-8 text-primary-content"),
                fh.Div(
                    # Image upload option
                    fh.Button(
                        fh.Div(
                            fh.Img(
                                src="/static/images/camera.png",
                                cls="h-12 w-auto object-contain mb-3"
                            ),
                            fh.P("Upload an image", cls="text-primary-content mb-2"),
                            cls="flex flex-col items-center justify-center h-full"
                        ),
                        cls="p-6 bg-base-200 bg-opacity-70 outline outline-1 outline-primary-content rounded-lg hover:bg-base-200 hover:bg-opacity-90 transition-colors w-full focus:outline-none mb-4 h-32",
                        onclick="showInputForm('image')"
                    ),
                    # Text description option
                    fh.Button(
                        fh.P("Describe it", cls="text-primary-content text-lg"),
                        cls="p-6 bg-base-200 bg-opacity-70 outline outline-1 outline-primary-content rounded-lg hover:bg-base-200 hover:bg-opacity-90 transition-colors w-full flex items-center justify-center focus:outline-none h-32",
                        onclick="showInputForm('text')"
                    ),
                    cls="flex flex-col space-y-4"
                ),
                id="input-selection",
                cls="p-6"
            ),
            # Hidden forms that will be shown when selected
            fh.Div(
                create_image_upload_form(),
                cls="hidden",
                id="image-input"
            ),
            fh.Div(
                create_text_input_form(),
                cls="hidden",
                id="text-input"
            ),
            cls="space-y-6 overflow-y-auto max-h-[80vh] bg-base-200 bg-opacity-70 rounded-lg relative w-full max-w-lg"
        ),
        cls="bg-transparent rounded-lg relative w-full max-w-lg"
    )

def food_tracking_modal():
    """Create the food tracking modal"""
    return fh.Div(
        fh.Div(
            cls="fixed inset-0 bg-slate-100 bg-opacity-25 transition-opacity hidden",
            id="modal-backdrop",
            onclick="closeModal()"
        ),
        fh.Div(
            create_modal_content(),
            cls="fixed inset-0 flex items-center justify-center p-4 hidden",
            id="food-modal"
        ),
        fh.Script("""
            function openFoodModal() {
                document.getElementById('food-modal').classList.remove('hidden');
                document.getElementById('modal-backdrop').classList.remove('hidden');
                document.body.style.overflow = 'hidden';
                document.getElementById('back-button').classList.add('hidden');
                showInputSelection();
            }
            
            function closeModal() {
                document.getElementById('food-modal').classList.add('hidden');
                document.getElementById('modal-backdrop').classList.add('hidden');
                document.body.style.overflow = 'auto';
                
                // Reset forms
                document.getElementById('text-result').innerHTML = '';
                document.querySelector('textarea[name="meal_description"]').value = '';
                document.getElementById('image-result').innerHTML = '';
                document.querySelector('input[type="file"]').value = '';
                
                // Hide back button
                document.getElementById('back-button').classList.add('hidden');
            }
            
            function showInputForm(type) {
                // Hide selection view
                document.getElementById('input-selection').classList.add('hidden');
                
                // Show selected input form
                if (type === 'image') {
                    document.getElementById('image-input').classList.remove('hidden');
                    document.getElementById('text-input').classList.add('hidden');
                } else {
                    document.getElementById('text-input').classList.remove('hidden');
                    document.getElementById('image-input').classList.add('hidden');
                }
                
                // Show back button
                document.getElementById('back-button').classList.remove('hidden');
            }
            
            function showInputSelection() {
                // Show selection view
                document.getElementById('input-selection').classList.remove('hidden');
                
                // Hide input forms
                document.getElementById('image-input').classList.add('hidden');
                document.getElementById('text-input').classList.add('hidden');
                
                // Hide back button
                document.getElementById('back-button').classList.add('hidden');
                
                // Reset forms
                document.getElementById('text-result').innerHTML = '';
                document.querySelector('textarea[name="meal_description"]').value = '';
                document.getElementById('image-result').innerHTML = '';
                document.querySelector('input[type="file"]').value = '';
            }
        """)
    )

def create_page_header():
    """Create the page header with title and time filter"""
    return fh.Div(
        fh.P("Nutritional Overview", cls="text-3xl font-bold text-center mb-6 text-primary-content"),
        fh.Div(
            fh.Select(
                fh.Option("Today", value="today", selected=True),
                fh.Option("This Week", value="week"),
                fh.Option("This Month", value="month"),
                name="time_filter",
                cls="select select-bordered w-full max-w-xs"
            ),
            cls="flex justify-center mb-8"
        ),
        cls="mb-8"
    )

def create_metric_overview_section(title, metrics_data, filtered_metrics, all_metrics=None):
    """Create a metrics overview section with configurable metrics"""    
    # Create dropdown of hidden metrics if all_metrics is provided
    add_button = None
    hidden_metrics = []
    if all_metrics is not None:
        hidden_metrics = [
            metric for metric in all_metrics 
            if metric["column_name"] not in [m["column_name"] for m in filtered_metrics]
        ]
    
    if hidden_metrics:
        dropdown_id = f"dropdown-{title.lower().replace(' ', '-')}"
        add_button = fh.Div(
            fh.Button(
                "+",
                cls="text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
                hx_get=f"/toggle_dropdown/{dropdown_id}",
                hx_target=f"#{dropdown_id}",
                hx_swap="innerHTML",
                onclick=f"document.getElementById('{dropdown_id}').classList.toggle('hidden')"
            ),
            fh.Div(
                cls="hidden absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-base-200 outline  ring-1 ring-black ring-opacity-5 z-10",
                id=dropdown_id
            ),
            cls="relative inline-block text-left ml-2"
        )
    
    return fh.Section(
        fh.Div(
            fh.H3(f"{title}", cls="text-2xl font-bold text-center mb-8 text-primary-content"),
            add_button if add_button else None,
            cls="flex items-center justify-center"
        ),
        fh.Div(
            fh.Div(
                *[fh.Div(
                    metric_card(
                        metric["name"],
                        f"{metric['name']} ({metric['unit']})" if metric["unit"] else metric["name"],
                        metric["plot_id"],
                        metrics_data[metric["column_name"]]["consumed"],
                        metrics_data[metric["column_name"]]["goal"],
                        metrics_data[metric["column_name"]].get("burned"),
                        allow_hide=metric["name"].lower() not in ["calories", "water", "creatine"]
                    ),
                    cls="w-1/2 p-2" if i < len(filtered_metrics) - 1 or len(filtered_metrics) % 2 == 0 
                        else "w-1/2 p-2 mx-auto"
                ) for i, metric in enumerate(filtered_metrics)],
                cls="flex flex-wrap"
            ),
            cls="w-full"
        ),
        cls="w-full"
    )

def create_macro_section(data, visible_metrics):
    """Create the macronutrient metrics section"""
    macro_metrics = [
        {"name": "Calories", "column_name": "calories", "unit": "", "plot_id": "calories"},
        {"name": "Protein", "column_name": "protein", "unit": "g", "plot_id": "protein"},
        {"name": "Carbohydrates", "column_name": "carbs", "unit": "g", "plot_id": "carbs"},
        {"name": "Fat", "column_name": "fat", "unit": "g", "plot_id": "fat"}
    ]

    filtered_metrics = [
        metric for metric in macro_metrics 
        if metric["column_name"].lower() in visible_metrics
    ]

    return create_metric_overview_section("Macronutrients", data, filtered_metrics, macro_metrics)

def create_micro_section(data, visible_metrics):
    """Create the micronutrient metrics section"""
    micro_metrics = [
        {"name": "Vitamin A", "column_name": "vitamin_a", "unit": "IU", "plot_id": "vitamin_a"},
        {"name": "Vitamin C", "column_name": "vitamin_c", "unit": "mg", "plot_id": "vitamin_c"},
        {"name": "Iron", "column_name": "iron", "unit": "mg", "plot_id": "iron"},
        {"name": "Calcium", "column_name": "calcium", "unit": "mg", "plot_id": "calcium"}
    ]
    filtered_metrics = [
        metric for metric in micro_metrics 
        if metric["column_name"].lower() in visible_metrics
    ]
    return create_metric_overview_section("Micronutrients", data, filtered_metrics, micro_metrics)

def create_conditional_section(data, visible_metrics):
    """Create the conditionally essential nutrients section"""
    conditional_metrics = [
        {"name": "Creatine", "column_name": "creatine", "unit": "g", "plot_id": "creatine"}
    ]
    filtered_metrics = [
        metric for metric in conditional_metrics 
        if metric["column_name"].lower() in visible_metrics
    ]
    return create_metric_overview_section("Conditionally Essential Nutrients", data, filtered_metrics, conditional_metrics)

def create_metrics_grid(data, visible_metrics, water_metrics):
    """Create the grid of metric cards"""
    sections = [
        create_overview_card(),
        create_macro_section(data, visible_metrics),
        create_micro_section(data, visible_metrics),
        create_conditional_section(data, visible_metrics),
        create_metric_overview_section("Hydration", data, water_metrics)
    ]
    sections = [section for section in sections if section is not None]
    
    return fh.Div(
        fh.Div(
            *sections,
            cls="w-full space-y-12"
        ),
        cls="w-full"
    )

def create_overview_card():
    """Create the overview card with analysis button"""
    return fh.Card(
        fh.Div(
            fh.Div(
                fh.Button(
                    "Generate Daily Analysis",
                    cls="btn btn-primary outline outline-1 outline-primary-content",
                    hx_post="/generate_overview",
                    hx_target="#analysis-content"
                ),
                cls="flex justify-center mb-4"
            ),
            fh.Div(
                id="analysis-content",
                cls="prose max-w-none prose-invert"
            ),
            cls="p-6"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mb-8 text-primary-content"
    )


def create_nutrition_section(title: str, items: list, cls: str = "mb-4"):
    """Create a section in the nutrition card"""
    return fh.Section(
        fh.H4(title, cls="font-medium mb-2"),
        fh.Ul(
            *[
                fh.Li(
                    fh.Span(f"{name}: ", cls="font-medium"),
                    value,
                    cls="mb-1"
                )
                for name, value in items
            ],
            cls="list-none"
        ),
        cls=cls
    )

def create_form_input(label_text, input_name, input_value, input_type="number", step="0.1"):
    """Helper function to create a form input with label"""
    if input_type == "number":
        value = 0.0 if input_value is None or input_value == "" else float(input_value)
        formatted_value = "{:.1f}".format(value)
    else:
        formatted_value = input_value

    return fh.Div(
        fh.Label(label_text, cls="label text-primary-content"),
        fh.Input(
            type=input_type,
            name=input_name,
            value=formatted_value,
            step=step if input_type == "number" else None,
            cls="input input-bordered w-full bg-base-200 outline  text-primary-content"
        ),
        cls="form-control"
    )

def create_form_section(title, inputs, cls="mb-6"):
    """Helper function to create a form section with a title and inputs"""
    return fh.Section(
        fh.H4(title, cls="font-medium mb-4 text-primary-content"),
        fh.Div(
            *inputs,
            cls="grid grid-cols-2 gap-4"
        ),
        cls=cls
    )

def create_nutrition_card(nutrition_info):
    """Create a card containing ingredients text and editable nutrition form"""
    return fh.Card(
        fh.Div(
            fh.H4("Ingredients", cls="font-medium mb-2 text-primary-content"),
            fh.P(
                nutrition_info.ingredients,
                cls="mb-6 text-primary-content"
            ),
            fh.Form(
                hx_post="/save_meal",
                hx_target="#save-result",
                cls="space-y-6"
            )(
                fh.Input(
                    type="hidden",
                    name="summary",
                    value=nutrition_info.summary
                ),
                fh.Input(
                    type="hidden",
                    name="ingredients",
                    value=nutrition_info.ingredients
                ),
                create_form_section("Nutrition Information", [
                    create_form_input("Meal Title", "summary", nutrition_info.summary, input_type="text"),
                    create_form_input("Calories (kcal)", "calories", nutrition_info.calories),
                    create_form_input("Protein (g)", "protein", nutrition_info.protein),
                    create_form_input("Carbs (g)", "carbs", nutrition_info.carbs),
                    create_form_input("Fat (g)", "fat", nutrition_info.fat),
                    create_form_input("Fiber (g)", "fiber", nutrition_info.fiber),
                    create_form_input("Vitamin A (IU)", "vitamin_a", nutrition_info.vitamin_a),
                    create_form_input("Vitamin C (mg)", "vitamin_c", nutrition_info.vitamin_c),
                    create_form_input("Vitamin D (IU)", "vitamin_d", nutrition_info.vitamin_d),
                    create_form_input("Calcium (mg)", "calcium", nutrition_info.calcium),
                    create_form_input("Iron (mg)", "iron", nutrition_info.iron),
                    create_form_input("Potassium (mg)", "potassium", nutrition_info.potassium),
                    create_form_input("Sodium (mg)", "sodium", nutrition_info.sodium),
                ]),
                fh.Button(
                    "Save Meal",
                    type="submit",
                    cls="btn btn-primary w-full"
                ),
                fh.Div(id="save-result", cls="mt-4")
            ),
            cls="space-y-4"
        ),
        cls="bg-base-200 outline  rounded-lg p-6"
    )


def create_metrics_container(data, visible_metrics):
    """Create the metrics grid with its container"""
    water_metrics = [{"name": "Water", "column_name": "water", "unit": "oz", "plot_id": "water-plot"}]
    sections = [
        create_overview_card(),
        create_macro_section(data, visible_metrics),
        create_micro_section(data, visible_metrics),
        create_conditional_section(data, visible_metrics),
        create_metric_overview_section("Hydration", data, water_metrics)
    ]
    sections = [section for section in sections if section is not None]
    
    return fh.Div(
        fh.Div(
            *sections,
            cls="w-full space-y-12"
        ),
        cls="w-full",
        id="metrics-container"
    )

