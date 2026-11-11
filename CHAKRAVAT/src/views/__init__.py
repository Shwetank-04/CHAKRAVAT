"""CHAKRAVAT Section Views."""

from src.views.section_overview import render as render_overview
from src.views.section_map import render as render_map
from src.views.section_prediction import render as render_prediction
from src.views.section_data_sources import render as render_data_sources
from src.views.section_alerts import render as render_alerts
from src.views.section_community import render as render_community
from src.views.section_shelters import render as render_shelters
from src.views.section_response import render as render_response
from src.views.section_about import render as render_about

__all__ = [
    "render_overview",
    "render_map",
    "render_prediction",
    "render_data_sources",
    "render_alerts",
    "render_community",
    "render_shelters",
    "render_response",
    "render_about",
]
