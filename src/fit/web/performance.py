import fasthtml.common as fh
from fit.web.common import create_fab_menu, page_outline


def get():
    """Return the performance tracking page content"""
    fab_buttons = [
        ("Activity", "🏃", None),  # Add handler later
        ("Workout", "💪", None),   # Add handler later
        ("Stats", "📊", None)      # Add handler later
    ]
    
    content = fh.Article(
        fh.Div(
            # Header section
            fh.Card(
                fh.Header(
                    fh.H3("Performance Overview", cls="text-2xl font-bold text-center mb-2 text-primary-content"),
                    fh.P(
                        "Track your athletic performance and training",
                        cls="text-slate-400 text-center"
                    ),
                    cls="mb-6 bg-base-200"
                ),
                # Placeholder for main content
                fh.Div(
                    fh.P(
                        "Performance tracking features coming soon...",
                        cls="text-primary-content text-center text-lg"
                    ),
                    cls="p-8"
                ),
                cls="bg-base-200 shadow-lg rounded-lg p-6"
            ),
            # Add FAB menu
            create_fab_menu(fab_buttons),
            cls="max-w-4xl mx-auto p-6 bg-base-100"
        ),
        cls="bg-base-100"
    )
    return page_outline(3, "Performance Tracking", content) 