# TODO Folium library utils

import folium
from folium import plugins
import random

# TimeSliderChoropleth provides a slider on the top of the choropleth map
# which you can slide to visualize the change in a quantity over a period of time.
# The GeoJSON must be string serialized in the following format:
#
# data_dict = {
#   '0': {
#       '1586563200' : { 'color' : 'ffffff', 'opacity': 1 },
#       '1586649600' : { 'color' : 'ffffff', 'opacity': 1 }
#   },
#   'n': {
#       '1586563200' : { 'color' : 'ffffff', 'opacity': 1 },
#       '1586649600' : { 'color' : 'ffffff', 'opacity': 1 }
#   }
# }


def util_lat_long_geopandas_point(pt):
    return pt.y, pt.x


def create_map_trajectories(list_trajectories, mapper_centroid,
                            path_html='../PRIVATE DATA/output/example_application_debug_master.html'):
    lines = []
    for traj in list_trajectories:
        dict_line = {}
        for id_cell, timestep in traj:
            coord_centroid = mapper_centroid[id_cell]
            if 'coordinates' not in dict_line:
                dict_line['coordinates'] = [[coord_centroid[1], coord_centroid[0]]]
                dict_line['dates'] = [timestep]
                dict_line['color'] = 'red'
            else:
                dict_line['coordinates'].append([coord_centroid[1], coord_centroid[0]])
                dict_line['dates'].append(timestep)
        lines.append(dict_line)

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": line["coordinates"],
            },
            "properties": {
                "times": line["dates"],
                "style": {
                    "color": '#%06x' % random.randint(0, 0xFFFFFF),
                    "weight": 5,
                    "opacity": 0.7
                },
            },
        }
        for line in lines
    ]

    # create map Folium, Bologna(lat,long)
    map_time_traj = folium.Map(location=[44.4992192, 11.2616459], zoom_start=10)

    plugins.TimestampedGeoJson(
        {'type': 'FeatureCollection',
         'features': features},
        period='PT1M',
        add_last_point=True,
        auto_play=False,
        loop=True,
        max_speed=1,
        transition_time=2000,
        loop_button=True,
        time_slider_drag_update=True
    ).add_to(map_time_traj)

    map_time_traj.save(path_html)

    return map_time_traj
