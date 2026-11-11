"""CHAKRAVAT Plotly Offline Geospatial Map Engine.

Generates dark-theme (#101820) North Indian Ocean (Bay of Bengal & Arabian Sea)
basemaps with zero external dependencies, 100% offline air-gapped execution,
dynamic IMD intensity categorization, and multi-storm tracking.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import plotly.graph_objects as go

from src.geo.styling import (
    GEO_BOUNDS,
    IMD_CATEGORIES,
    STORM_COLOR_PALETTE,
    get_category_color,
    get_category_style,
    get_storm_color,
)
from src.geo.tracks import CycloneTrack, CycloneWaypoint



def topojson_url() -> str:
    """URL prefix of the bundled basemap geometry (``static/topojson``).

    Plotly normally downloads ``asia_50m.json`` from cdn.plot.ly at render time, which silently
    breaks the app's offline / air-gapped promise (blank map, no coastlines). The files are
    shipped in ``static/`` and served by Streamlit (``server.enableStaticServing``).
    """
    base = ""
    try:
        import streamlit as st

        base = str(st.get_option("server.baseUrlPath") or "").strip("/")
    except Exception:
        pass
    return (f"/{base}" if base else "") + "/app/static/topojson/"


def geo_chart_config(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Plotly ``config`` for any chart containing a geo subplot (offline basemap + sane toolbar)."""
    cfg: Dict[str, Any] = {
        "topojsonURL": topojson_url(),
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    }
    cfg.update(extra or {})
    return cfg


# ---------------------------------------------------------------------------
# Viewport fitting
# ---------------------------------------------------------------------------

def fit_bounds(
    points: Iterable[Tuple[float, float]],
    pad_frac: float = 0.35,
    min_lat_span: float = 7.0,
    min_lon_span: float = 10.0,
) -> Tuple[List[float], List[float], Dict[str, float]]:
    """Return (lataxis_range, lonaxis_range, center) that frames every (lat, lon) point.

    The window is padded, given a minimum span so a single fix is not zoomed to a pixel,
    and clamped to the North Indian Ocean extent. The center is always the exact midpoint
    of the two ranges, so Plotly never has to reconcile a range with a different center.
    """
    pts = [(float(la), float(lo)) for la, lo in points]
    if not pts:
        return (list(GEO_BOUNDS["lataxis_range"]), list(GEO_BOUNDS["lonaxis_range"]),
                dict(GEO_BOUNDS["center"]))

    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    lat_lo, lat_hi = min(lats), max(lats)
    lon_lo, lon_hi = min(lons), max(lons)

    lat_span = max(min_lat_span, (lat_hi - lat_lo) * (1 + 2 * pad_frac))
    lon_span = max(min_lon_span, (lon_hi - lon_lo) * (1 + 2 * pad_frac))
    lat_mid = (lat_hi + lat_lo) / 2.0
    lon_mid = (lon_hi + lon_lo) / 2.0

    b_lat = GEO_BOUNDS["lataxis_range"]
    b_lon = GEO_BOUNDS["lonaxis_range"]
    lat_span = min(lat_span, b_lat[1] - b_lat[0])
    lon_span = min(lon_span, b_lon[1] - b_lon[0])

    # Slide (not shrink) the window so it stays inside the basin extent.
    lat_lo_w = min(max(lat_mid - lat_span / 2, b_lat[0]), b_lat[1] - lat_span)
    lon_lo_w = min(max(lon_mid - lon_span / 2, b_lon[0]), b_lon[1] - lon_span)
    lataxis = [round(lat_lo_w, 3), round(lat_lo_w + lat_span, 3)]
    lonaxis = [round(lon_lo_w, 3), round(lon_lo_w + lon_span, 3)]
    center = {"lat": (lataxis[0] + lataxis[1]) / 2.0, "lon": (lonaxis[0] + lonaxis[1]) / 2.0}
    return lataxis, lonaxis, center

# ---------------------------------------------------------------------------
# Basemap Construction
# ---------------------------------------------------------------------------

def create_north_indian_ocean_map(
    title: Optional[str] = None,
    height: int = 620,
    custom_lataxis: Optional[List[float]] = None,
    custom_lonaxis: Optional[List[float]] = None,
    custom_center: Optional[Dict[str, float]] = None,
) -> go.Figure:
    """Build a baseline Plotly Scattergeo figure for the North Indian Ocean basin.
    
    100% offline, zero network requests, deep navy/charcoal styling (#101820).
    """
    palette = GEO_BOUNDS["theme_palette"]
    lataxis_range = custom_lataxis or GEO_BOUNDS["lataxis_range"]
    lonaxis_range = custom_lonaxis or GEO_BOUNDS["lonaxis_range"]
    center = custom_center or {
        "lat": (lataxis_range[0] + lataxis_range[1]) / 2.0,
        "lon": (lonaxis_range[0] + lonaxis_range[1]) / 2.0,
    }

    fig = go.Figure()

    # Configure geographic projection and offline vector styling
    fig.update_geos(
        scope="asia",
        resolution=50,  # 1:50M offline vector coastline resolution
        showland=True,
        landcolor=palette["land_color"],
        showocean=True,
        oceancolor=palette["ocean_color"],
        showlakes=True,
        lakecolor=palette["lake_color"],
        showrivers=False,
        showcoastlines=True,
        coastlinecolor=palette["coastline_color"],
        coastlinewidth=1.2,
        showcountries=True,
        countrycolor=palette["country_color"],
        countrywidth=1.0,
        showsubunits=True,
        subunitcolor=palette["country_color"],
        subunitwidth=0.6,
        bgcolor=palette["bg_color"],
        projection_type=GEO_BOUNDS["projection_type"],
        center=center,
        lataxis=dict(
            range=lataxis_range,
            showgrid=True,
            gridcolor=palette["grid_color"],
            gridwidth=0.5,
            dtick=5,
        ),
        lonaxis=dict(
            range=lonaxis_range,
            showgrid=True,
            gridcolor=palette["grid_color"],
            gridwidth=0.5,
            dtick=5,
        ),
        fitbounds=False,
    )

    # Ambient basin geographical labels (subtle atmospheric typography)
    fig.add_trace(
        go.Scattergeo(
            lat=[14.5, 14.5],
            lon=[65.0, 89.0],
            text=["ARABIAN SEA", "BAY OF BENGAL"],
            mode="text",
            textfont=dict(
                family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
                size=12,
                color="rgba(148, 163, 184, 0.40)",
            ),
            hoverinfo="skip",
            showlegend=False,
            name="Basin Labels",
        )
    )

    # Coastal zone landmark labels
    fig.add_trace(
        go.Scattergeo(
            lat=[20.2, 21.8, 17.5, 22.5, 7.8],
            lon=[86.2, 88.5, 83.0, 69.5, 78.5],
            text=["Odisha Coast", "Sundarbans / WB", "Andhra Coast", "Gujarat / Kutch", "Kanyakumari"],
            mode="text",
            textfont=dict(
                family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
                size=10,
                color="rgba(56, 189, 248, 0.45)",
            ),
            hoverinfo="skip",
            showlegend=False,
            name="Coastal Landmarks",
        )
    )

    # Global layout styling
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=palette["bg_color"],
        plot_bgcolor=palette["bg_color"],
        height=height,
        margin=dict(l=0, r=0, t=30 if title else 0, b=0),
        title=dict(
            text=f"<b style='color: #F1F5F9; font-size: 15px;'>{title}</b>" if title else "",
            x=0.02,
            y=0.96,
            xanchor="left",
            yanchor="top",
        ) if title else None,
        legend=dict(
            bgcolor="rgba(23, 34, 45, 0.90)",
            bordercolor=palette["border_color"],
            borderwidth=1,
            font=dict(
                family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
                size=11,
                color=palette["text_color"],
            ),
            orientation="v",
            x=0.01,
            y=0.02,
            xanchor="left",
            yanchor="bottom",
        ),
        dragmode="pan",
    )

    return fig


# ---------------------------------------------------------------------------
# Multi-Storm Comparative Overview Figure
# ---------------------------------------------------------------------------

def build_multi_storm_figure(
    tracks: Dict[str, CycloneTrack],
    show_lines: bool = True,
    show_markers: bool = True,
    show_landfalls: bool = True,
    height: int = 640,
) -> go.Figure:
    """Build a multi-storm comparative track overview map.
    
    Renders multiple historical cyclone tracks across Bay of Bengal and Arabian Sea.
    """
    fig = create_north_indian_ocean_map(height=height)

    for storm_name, track in tracks.items():
        if not track.waypoints:
            continue

        lats = [wp.lat for wp in track.waypoints]
        lons = [wp.lon for wp in track.waypoints]
        hover_texts = [wp.hover_text for wp in track.waypoints]
        color = track.signature_color
        basin_tag = "AS" if "Arabian" in track.basin_full_name else "BOB"

        # 1. Solid geodesic connecting line
        if show_lines:
            fig.add_trace(
                go.Scattergeo(
                    lat=lats,
                    lon=lons,
                    mode="lines",
                    line=dict(
                        width=2.5,
                        color=color,
                    ),
                    name=f"{storm_name} ({basin_tag} • {track.max_category_code})",
                    hoverinfo="skip",
                    showlegend=True,
                )
            )

        # 2. Waypoint markers colored by intensity or signature
        if show_markers:
            marker_colors = [wp.category_color for wp in track.waypoints]
            marker_sizes = [
                IMD_CATEGORIES.get(wp.category_code, {}).get("size", 8)
                for wp in track.waypoints
            ]
            fig.add_trace(
                go.Scattergeo(
                    lat=lats,
                    lon=lons,
                    mode="markers",
                    marker=dict(
                        size=marker_sizes,
                        color=marker_colors,
                        line=dict(width=1.0, color="#101820"),
                        opacity=0.95,
                    ),
                    hovertext=hover_texts,
                    hoverinfo="text",
                    showlegend=False,
                    name=f"{storm_name} Fixes",
                )
            )

        # 3. High-visibility Landfall Marker
        if show_landfalls:
            lf = track.landfall_waypoint
            if lf:
                fig.add_trace(
                    go.Scattergeo(
                        lat=[lf.lat],
                        lon=[lf.lon],
                        mode="markers+text",
                        marker=dict(
                            size=14,
                            symbol="star",
                            color="#F87171",
                            line=dict(width=1.5, color="#FFFFFF"),
                        ),
                        text=[f"  {storm_name} Landfall"],
                        textposition="top right",
                        textfont=dict(
                            family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
                            size=10,
                            color="#FCA5A5",
                        ),
                        hovertext=[lf.hover_text],
                        hoverinfo="text",
                        showlegend=False,
                        name=f"{storm_name} Landfall",
                    )
                )

    return fig


# ---------------------------------------------------------------------------
# Single Storm Focus Figure
# ---------------------------------------------------------------------------

def build_single_storm_figure(
    track: CycloneTrack,
    up_to_step: Optional[int] = None,
    show_lines: bool = True,
    show_markers: bool = True,
    show_landfall: bool = True,
    auto_center: bool = True,
    height: int = 640,
) -> go.Figure:
    """Build a detailed single-storm inspection map with IMD intensity tiers.
    
    Supports step-by-step chronological animation/scrubbing and rich hovercards.
    """
    all_wps = track.waypoints
    if not all_wps:
        return create_north_indian_ocean_map(height=height)

    # Determine subset of waypoints if chronological scrubber is engaged
    if up_to_step is not None and up_to_step >= 0:
        active_wps = all_wps[: up_to_step + 1]
    else:
        active_wps = all_wps

    if not active_wps:
        active_wps = [all_wps[0]]

    # Dynamic basin centering if requested
    custom_center = None
    custom_lataxis = None
    custom_lonaxis = None

    if auto_center and len(all_wps) > 0:
        custom_lataxis, custom_lonaxis, custom_center = fit_bounds(
            [(w.lat, w.lon) for w in all_wps], pad_frac=0.4, min_lat_span=8.0, min_lon_span=11.0
        )

    fig = create_north_indian_ocean_map(
        height=height,
        custom_lataxis=custom_lataxis,
        custom_lonaxis=custom_lonaxis,
        custom_center=custom_center,
    )

    lats = [wp.lat for wp in active_wps]
    lons = [wp.lon for wp in active_wps]
    hover_texts = [wp.hover_text for wp in active_wps]

    # 1. Trajectory Track Line
    if show_lines:
        fig.add_trace(
            go.Scattergeo(
                lat=lats,
                lon=lons,
                mode="lines",
                line=dict(
                    width=3.0,
                    color="rgba(148, 163, 184, 0.75)",
                    dash="solid",
                ),
                hoverinfo="skip",
                showlegend=False,
                name="Trajectory",
            )
        )

    # 2. Waypoint markers grouped by IMD Category for clean interactive legend
    if show_markers:
        categories_present = set(wp.category_code for wp in active_wps)
        # Order by IMD intensity
        ordered_codes = ["D", "DD", "CS", "SCS", "VSCS", "ESCS", "SuCS"]

        for code in ordered_codes:
            if code not in categories_present:
                continue

            sub_wps = [wp for wp in active_wps if wp.category_code == code]
            cat_info = IMD_CATEGORIES[code]

            fig.add_trace(
                go.Scattergeo(
                    lat=[wp.lat for wp in sub_wps],
                    lon=[wp.lon for wp in sub_wps],
                    mode="markers",
                    marker=dict(
                        size=cat_info["size"] + 2,
                        symbol=cat_info["symbol"],
                        color=cat_info["color"],
                        line=dict(width=1.5, color="#101820"),
                    ),
                    hovertext=[wp.hover_text for wp in sub_wps],
                    hoverinfo="text",
                    name=f"{cat_info['name']} ({cat_info['min_kts']}-{cat_info['max_kts']} kt)",
                    showlegend=True,
                )
            )

    # 3. Current Position Beacon (Last fix in active scrubber)
    current_wp = active_wps[-1]
    fig.add_trace(
        go.Scattergeo(
            lat=[current_wp.lat],
            lon=[current_wp.lon],
            mode="markers+text",
            marker=dict(
                size=18,
                symbol="circle-open",
                color="#38BDF8",
                line=dict(width=3, color="#38BDF8"),
            ),
            text=[f"  <b>{track.storm_name}</b> ({current_wp.timestamp_utc[5:16]})"],
            textposition="top right",
            textfont=dict(
                family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
                size=12,
                color="#38BDF8",
            ),
            hovertext=[current_wp.hover_text],
            hoverinfo="text",
            showlegend=False,
            name="Current Position",
        )
    )

    # 4. Landfall Highlight
    if show_landfall:
        lf = track.landfall_waypoint
        if lf and lf in active_wps:
            fig.add_trace(
                go.Scattergeo(
                    lat=[lf.lat],
                    lon=[lf.lon],
                    mode="markers+text",
                    marker=dict(
                        size=18,
                        symbol="star",
                        color="#F87171",
                        line=dict(width=2.0, color="#FFFFFF"),
                    ),
                    text=["  <b>LANDFALL POINT</b>"],
                    textposition="bottom right",
                    textfont=dict(
                        family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
                        size=11,
                        color="#FCA5A5",
                    ),
                    hovertext=[lf.hover_text],
                    hoverinfo="text",
                    showlegend=True,
                    name="Official Landfall Point",
                )
            )

    return fig
