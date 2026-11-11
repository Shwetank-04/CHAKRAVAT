"""Regression tests for map viewport/integration bugs."""
import pytest

from src.geo.map_engine import (
    build_multi_storm_figure,
    build_single_storm_figure,
    create_north_indian_ocean_map,
    fit_bounds,
)
from src.geo.styling import GEO_BOUNDS
from src.geo.tracks import load_cyclone_tracks_from_csv


def _mid(r):
    return (r[0] + r[1]) / 2.0


def test_default_center_is_midpoint_of_ranges():
    fig = create_north_indian_ocean_map()
    geo = fig.layout.geo
    assert geo.center.lat == pytest.approx(_mid(geo.lataxis.range))
    assert geo.center.lon == pytest.approx(_mid(geo.lonaxis.range))
    assert GEO_BOUNDS["center"]["lon"] == pytest.approx(_mid(GEO_BOUNDS["lonaxis_range"]))


@pytest.mark.parametrize("name", list(load_cyclone_tracks_from_csv().keys()))
def test_every_storm_is_fully_inside_its_viewport(name):
    track = load_cyclone_tracks_from_csv()[name]
    fig = build_single_storm_figure(track, height=500)
    lat_r, lon_r = fig.layout.geo.lataxis.range, fig.layout.geo.lonaxis.range
    for wp in track.waypoints:
        assert lat_r[0] <= wp.lat <= lat_r[1], (name, wp.lat, lat_r)
        assert lon_r[0] <= wp.lon <= lon_r[1], (name, wp.lon, lon_r)
    assert fig.layout.geo.center.lon == pytest.approx(_mid(lon_r))


def test_overview_covers_whole_basin():
    fig = build_multi_storm_figure(load_cyclone_tracks_from_csv())
    for track in load_cyclone_tracks_from_csv().values():
        for wp in track.waypoints:
            assert fig.layout.geo.lataxis.range[0] <= wp.lat <= fig.layout.geo.lataxis.range[1]
            assert fig.layout.geo.lonaxis.range[0] <= wp.lon <= fig.layout.geo.lonaxis.range[1]


def test_fit_bounds_pads_clamps_and_handles_edge_cases():
    # single fix -> still a usable window, not a pinpoint
    lat, lon, c = fit_bounds([(20.0, 86.0)])
    assert lat[1] - lat[0] >= 7 and lon[1] - lon[0] >= 10
    # point at the basin edge slides the window inside the extent instead of leaving it
    lat, lon, _ = fit_bounds([(27.5, 97.5)])
    assert lat[1] <= GEO_BOUNDS["lataxis_range"][1] and lon[1] <= GEO_BOUNDS["lonaxis_range"][1]
    # empty input falls back to the basin default
    assert fit_bounds([])[1] == list(GEO_BOUNDS["lonaxis_range"])


def test_prediction_map_frames_all_layers_and_legend_has_its_own_band():
    from src.views.section_prediction import _build_track_map_figure
    track = load_cyclone_tracks_from_csv()["FANI"]
    wps = track.waypoints[:6]
    cone = [(14.0, 85.0), (14.0, 89.0), (19.0, 89.5), (19.5, 84.5)]
    fig = _build_track_map_figure(
        historical_waypoints=wps, pred_lat=17.0, pred_lon=86.0, lin_lat=16.2, lin_lon=85.4,
        clip_lat=16.8, clip_lon=85.0, uncertainty_polygon=cone, actual_lat=17.4, actual_lon=86.2,
        horizon_hours=12,
    )
    lat_r, lon_r = fig.layout.geo.lataxis.range, fig.layout.geo.lonaxis.range
    pts = [(w.lat, w.lon) for w in wps] + cone + [(17.0, 86.0), (16.2, 85.4), (16.8, 85.0), (17.4, 86.2)]
    assert all(lat_r[0] <= la <= lat_r[1] and lon_r[0] <= lo <= lon_r[1] for la, lo in pts)
    assert fig.layout.margin.b >= 80 and fig.layout.legend.y < 0     # legend below, not over the map
