Trajectory data mining
==============================================

Trajectory data mining means to discover interesting knowledge (e.g., movement patterns, travel behavior, traffic abnormality) from trajectory datasets.
Typically each point consists of a geospatial coordinate set and a time stamp such as p = (x, y, t) and a trajectory is defined as a set of p.

Geospatial data is considered extremely sensitive and it's not easy to obtain spatial data without a series of direct permissions of the user. In addition, there are several techniques to associate with trajectory data mining to respect the user's privacy.

To avoid all privacy-related processes, geospatial data is replaced by device counts within each census cell in each time slot.
The goal of this project is to extract trajectories from dynamic entity count data and identify trajectories that contain a certain pattern associated with a group of trajectories with similar patterns.

Through the techniques and models it will be possible:
    - locate the basin of attraction of a location: once the census cell to be analyzed has been defined, the algorithm will identify all relevant trajectories from the selected cell so as to extract all the most visited paths. This information is very useful to set up advertising campaigns aimed at reaching as many customers as possible or to study the routes used to reach the selected location.
    - identifying overnight stays: the methodology will be very similar to the previous one with the addition of the analysis of the temporal information of the night periods, i.e. a period of at least seven consecutive hours including the interval between midnight and 5 a.m. Possible applications are in territorial marketing and the promotion of tourist destinations.
    - locate cyclic paths: trajectories with repeating cells or trajectories from the same cell reversed at different time intervals can define cyclic paths. A cyclic path can indicate a tourist destination or a working routine.This information can be used to study territorial mobility.
    - locate a Stay Point: In Trajectory Data Mining, a Stay Point is a much more significant point of trajectory than the others. Often a Stay Point is a point where the user remains stationed or a point where multiple groups of trajectories need to cross (bottleneck). The identification of Stay Points is necessary in all fields of tourism and mobility.

Telephony Data
=========================

The data, provided by Telecom Italia S.p.A., describe the information of the census cells that will hence to be referred to as ACE. A census cell is a portion of provincial territory.
Emilia-Romagna has been partitioned into 507 census cells. There is typically an ACE for each municipality and at most one cell per city, e.g. the centre of Bologna is divided by 4 census cells.

Telecom provided a file that describes all ACEs classified with a unique identifier. 
Each ACE defines an area described by an irregular polygon according to the open GeoJSON format that is widely used for defining spatial geometries.
Telecom also provided a file for each specific day of data extraction: the period ranges from 01/08/2019 to 30/09/2019. Each line in the file contains a set of parameters for an ACE in a specific time slot.

For each census cell there are a series of information:
    - ID: ACE identifier
    - H: time slot. Data sampling is every 15 minutes
    - F1: people under 18
    - F2: people between 18 and 30
    - F3: people between 31 and 40
    - F4: people between 41 and 50
    - F5: people between 51 and 60
    - F6: people over 60
    - Gf: female people
    - Gm: male people
    - Ns: people of foreign nationality
    - Ni: people of Italian nationality
    - P: people connected to the ACE
    - Tb: (business?)
    - Tc: (consumer?)
    - Ve: number of non-regional visitors
    - Vi: number of intra-regional visitors
    - Vp: number of commuters
    - Vr: number of residents
    - Vs: number of foreigners

For a better visualization of the telephony data, we have created an application that, using the data provided, shows in a web page the ACEs, the area of interest of each ACE and the information of the ACes at every time slot.
Each area of the ACE is colored according to the P parameter, which is the number of devices within an ACE. As parameter P increases, the polygon area is colored following a scale from a light yellow to a dark red.
In this first phase it was decided to use the only parameter P because the other information of the ACE was found to be unreliable and in some cases the data are missing.

The application is written in Python and uses the Pandas and Folium libraries for the realization of the map and the visualization of ACE data.

Geopandas
===============================================

`Geopandas <https://geopandas.org/index.html/>`__ is an open source project to make working with geospatial data in python easier. GeoPandas extends the datatypes used by `Pandas <https://pandas.pydata.org/>`__ to allow spatial operations on geometric types.

Geopandas works with GeoJSON file format: GeoJSON is an open standard format designed for representing simple geographical features, along with their non-spatial attributes. It is based on the JSON format.

The features include points (therefore addresses and locations), line strings (therefore streets, highways and boundaries), polygons (countries, provinces, tracts of land), and multi-part collections of these types. GeoJSON features need not represent entities of the physical world only; mobile routing and navigation apps, for example, might describe their service coverage using GeoJSON.

Example GeoJSON format:

.. code:: ipython3

   example = {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [102.0, 0.5]
          },
          "properties": {
            "prop0": "value0"
          }
        },
        {
          "type": "Feature",
          "geometry": {
            "type": "LineString",
            "coordinates": [
              [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]
            ]
          },
          "properties": {
            "prop0": "value0",
            "prop1": 0.0
          }
        },
        {
          "type": "Feature",
          "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [100.0, 0.0], [101.0, 0.0], [101.0, 1.0],
                [100.0, 1.0], [100.0, 0.0]
              ]
            ]
          },
          "properties": {
            "prop0": "value0",
            "prop1": { "this": "that" }
          }
        }
      ]
    }   

How to generate the GeoJSON file: 

.. code:: ipython3

   import folium
   import pandas
   import numpy
   import json
   import random


    if __name__ == "__main__":
        df_layer = pandas.read_csv(LAYER_FILE_CSV, sep=';', dtype={'ID': str})

        map_geojson = {}
        list_features = []
        # struct {"type": "FeatureCollection", "features": []}
        map_geojson['type'] = 'FeatureCollection'

        for row_marker in df_layer.itertuples():
            partial_geojson = json.loads(row_marker.GEOJSON)
            # change ID to create a correct Geojson
            partial_geojson['id'] = row_marker.ID
            list_features.append(partial_geojson)

        map_geojson['features'] = list_features

        with open('layers_geojson.json', 'w') as fp:
            json.dump(map_geojson, fp)





How to read a GeoJSON file:

.. code:: ipython3
   
   geojson = geopandas.read_file(FILE_GEOJSON)

  