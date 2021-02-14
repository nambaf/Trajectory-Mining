Simulators
===================

Simple GeoJson folium map
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code:: ipython3

    import folium
    import pandas
    import geopandas
    import branca
    
    
    def util_lat_long_geopandas_point(pt):
        return (pt.y, pt.x)
    
    
    """
    Create a viewer with a GeoJson folium map + Mouse event
    """
    if __name__ == "__main__":
        FILE_LAYER = '../polis-eye/data/layers_geojson.geojson'
        FILE_TELEPHONY_DAY = '../polis-eye/data/dati_telefonia.csv'
        OUTPUT = "../polis-eye/output/polis-layer.html"
    
        geojson = geopandas.read_file(FILE_LAYER)
    
        # UserWarning: Geometry is in a geographic CRS. Results from 'centroid' are likely incorrect.
        # Use 'GeoSeries.to_crs()' to re-project geometries to a projected CRS before this operation.
        centroids = geojson.centroid
        lat_long_centroids = list(map(util_lat_long_geopandas_point, centroids))
    
        # read temporal data
        df_today = pandas.read_csv(FILE_TELEPHONY_DAY, sep=';')
        df_today.rename(columns={'ID': 'id'}, inplace=True)
        df_today = df_today.groupby(['id']).sum()
    
        result = pandas.merge(
            geojson,
            df_today,
            how='outer',
            on='id'
        )
        #print(result.columns)
        #print(result['geometry'])
    
        # create map Folium, Bologna(lat,long)
        map_folium = folium.Map(location=[44.4992192, 11.2616459], zoom_start=10)
        #fg = folium.FeatureGroup(name='cells')
        #map_folium.add_child(fg)
    
        variable_legend = 'P'
        # create colormap based on the parameter P
        colorscale = branca.colormap.linear.YlOrRd_09.scale(0, result[variable_legend].max())
    
        # need a discrete colormap
        df_colormap_disc = result[['id', variable_legend]].sort_values(by=variable_legend, ascending=False)
        df_colormap_disc.reset_index(inplace=True)
        # splitting example: 6 colors based on percentile
        slice_th = list(df_colormap_disc[df_colormap_disc.index.isin([0, 4, 9, 19, 29, 49])][variable_legend])
        slice_th.sort()
    
        # conversion to discrete
        colorscale = colorscale.to_step(n=6, quantiles=slice_th)
        colorscale.caption = 'Emilia-Romagna map'
    
        # create GeoJson map
        columns_tooltip = df_today.columns.difference(['H'])
        folium.GeoJson(
            result,
            name='Map',
            # add colormap
            style_function=lambda x: {
                'weight': 1,
                'color': '#545453',
                # if 0 light grey
                # else colorscale based on variable
                'fillColor': '#9B9B9B' if x['properties'][variable_legend] == 0
                else colorscale(x['properties'][variable_legend]),
                # similarly opacity
                'fillOpacity': 0.2 if x['properties'][variable_legend] == 0
                else 0.5
            },
            # style geo regions hover
            highlight_function=lambda x: {'weight': 3, 'color': 'black', 'fillOpacity': 1},
            # tooltip to include information from any column in the Geopandas Dataframe
            tooltip=folium.features.GeoJsonTooltip(
                fields=[column_name for column_name in result[columns_tooltip].columns],
                aliases=[column_name+':' for column_name in result[columns_tooltip].columns]
            )
        ).add_to(map_folium)
    
        # add colormap
        colorscale.add_to(map_folium)
    
        for tuple_coord in lat_long_centroids:
            folium.CircleMarker(
                location=tuple_coord,
                radius=2
            ).add_to(map_folium)
            #folium.Marker(location=[tuple_coord[0], tuple_coord[1]]).add_to(map_folium)
    
        # add control
        folium.LayerControl().add_to(map_folium)
    
        # save result
        map_folium.save(OUTPUT)
    

TimeSliderChoropleth + GeoJson folium map [CURRENT SIMULATOR]
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code:: ipython3

    import folium
    from folium import plugins
    import pandas
    import geopandas
    import numpy
    import branca
    
    """
    Create a viewer with a TimeSliderChoropleth and a GeoJson folium map
    """
    if __name__ == "__main__":
        FILE_LAYER = '../polis-eye/data/layers_geojson.geojson'
        FILE_TELEPHONY = '../polis-eye/data/dati_telefonia.csv'
        OUTPUT = "../polis-eye/output/slider_geo_polis-datacell.html"
    
        geojson = geopandas.read_file(FILE_LAYER)
        # to fix crs
        #geojson = geojson.to_crs("EPSG:3395")
    
        # read temporal data
        data_cell = pandas.read_csv(FILE_TELEPHONY)
    
        # create map Folium, Bologna(lat,long)
        map_folium = folium.Map(location=[44.4992192, 11.2616459], zoom_start=10)
    
        # map cell to an index
        id_dict = {}
        for index, value in enumerate(geojson['id']):
            id_dict.update({value: index})
    
        # print(data_cell.head())
        data_cell['cell_id'] = data_cell['id'].map(id_dict)
    
        # create colormap to retrieve a discrete color for percentile
        variable_legend = 'P'
        colorscale = branca.colormap.linear.YlOrRd_09.scale(0, data_cell[variable_legend].max())
        df_colormap_disc = data_cell[['id', variable_legend]].sort_values(by=variable_legend, ascending=False)
        df_colormap_disc.reset_index(inplace=True)
        slice_th = list(df_colormap_disc[df_colormap_disc.index.isin([0, 4, 9, 19, 29, 49])][variable_legend])
        slice_th.sort()
        colorscale = colorscale.to_step(n=6, quantiles=slice_th)
        colorscale.caption = 'Emilia-Romagna map'
    
        data_cell['color'] = data_cell[variable_legend].apply(lambda x: colorscale(x)[:7])
    
        # create sliced datatrame to create data dict for slider
        simpler_df = data_cell[['H', 'cell_id', 'color']]
        simpler_df['H'] = pandas.to_datetime(simpler_df['H'])
    
        # data slider
        simpler_df['H_UNIX'] = simpler_df['H'].apply(lambda x: x.replace().timestamp())
        simpler_df['H_UNIX'] = numpy.array(simpler_df['H_UNIX']).astype('U10')
        style_data = {}
        for i in simpler_df['cell_id'].unique():
            style_data[int(i)] = {}
            for j in simpler_df[simpler_df['cell_id'] == i].set_index(['cell_id']).values:
                style_data[i][j[2]] = {'color': j[1], 'opacity': 1}
    
        geojson['cell_id'] = geojson['id'].map(id_dict)
        geojson['cell_id'] = geojson['cell_id'].astype(int)
    
        # create TimeSlider map
        plugins.TimeSliderChoropleth(
            geojson.set_index('cell_id').to_json(),
            styledict=style_data, overlay=False
        ).add_to(map_folium)
    
        # create geojson data
        style_function = lambda x: {
            'color': 'black',
            'weight': 1,
        }
    
        folium.GeoJson(
            geojson,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['id', 'cell_id'],
                aliases=['id','cell_id'],
                localize=True
            )
        ).add_to(map_folium)
    
        colorscale.add_to(map_folium)
    
        # save result
        map_folium.save(OUTPUT)
    


Example TimeSliderChoropleth folium map
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code:: ipython3

    import folium
    from folium import plugins
    import pandas
    import geopandas
    import numpy
    import branca
    
    """
    Create a viewer with a TimeSliderChoropleth folium map
    """
    if __name__ == "__main__":
        FILE_LAYER = '../polis-eye/data/layers_geojson.geojson'
        FILE_TELEPHONY = '../polis-eye/data/dati_telefonia.csv'
        OUTPUT = "../polis-eye/output/slider_polis-datacell.html"
    
        geojson = geopandas.read_file(FILE_LAYER)
        # to fix crs
        #geojson = geojson.to_crs("EPSG:3395")
    
        # read temporal data
        data_cell = pandas.read_csv(FILE_TELEPHONY)
    
        # create map Folium, Bologna(lat,long)
        map_folium = folium.Map(location=[44.4992192, 11.2616459], zoom_start=10)
    
        # map cell to an index
        id_dict = {}
        for index, value in enumerate(geojson['id']):
            id_dict.update({value: index})
    
        # print(data_cell.head())
        data_cell['cell_id'] = data_cell['id'].map(id_dict)
    
        # create colormap to retrieve a discrete color for percentile
        variable_legend = 'P'
        colorscale = branca.colormap.linear.YlOrRd_09.scale(0, data_cell[variable_legend].max())
        df_colormap_disc = data_cell[['id', variable_legend]].sort_values(by=variable_legend, ascending=False)
        df_colormap_disc.reset_index(inplace=True)
        slice_th = list(df_colormap_disc[df_colormap_disc.index.isin([0, 4, 9, 19, 29, 49])][variable_legend])
        slice_th.sort()
        colorscale = colorscale.to_step(n=6, quantiles=slice_th)
        colorscale.caption = 'Emilia-Romagna map'
    
        data_cell['color'] = data_cell[variable_legend].apply(lambda x: colorscale(x)[:7])
    
        # create sliced datatrame to create data dict for slider
        simpler_df = data_cell[['H', 'cell_id', 'color']]
        simpler_df['H'] = pandas.to_datetime(simpler_df['H'])
    
        # data slider
        simpler_df['H_UNIX'] = simpler_df['H'].apply(lambda x: x.replace().timestamp())
        simpler_df['H_UNIX'] = numpy.array(simpler_df['H_UNIX']).astype('U10')
        style_data = {}
        for i in simpler_df['cell_id'].unique():
            style_data[int(i)] = {}
            for j in simpler_df[simpler_df['cell_id'] == i].set_index(['cell_id']).values:
                style_data[i][j[2]] = {'color': j[1], 'opacity': 1}
    
        geojson['cell_id'] = geojson['id'].map(id_dict)
        geojson['cell_id'] = geojson['cell_id'].astype(int)
    
        # create TimeSlider map
    
        plugins.TimeSliderChoropleth(
            geojson.set_index('cell_id').to_json(),
            styledict=style_data, overlay=False
        ).add_to(map_folium)
    
        # save result
        map_folium.save(OUTPUT)
    


Example HeatMapWithTime folium map
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code:: ipython3

    import folium
    from folium import plugins
    import pandas
    import geopandas
    
    
    def util_lat_long_geopandas_point(pt):
        return (pt.y, pt.x)
    
    """
    Create a viewer with a HeatMapWithTime folium map. NOT USED
    """
    if __name__ == "__main__":
        FILE_LAYER = '../polis-eye/data/layers_geojson.geojson'
        FILE_TELEPHONY_DAY = '../polis-eye/data/P15_uni_20190801.csv'
        OUTPUT = "../polis-eye/output/heatmap_polis-layer.html"
    
        geojson = geopandas.read_file(FILE_LAYER)
        # to fix crs
        #geojson = geojson.to_crs("EPSG:3395")
    
        # retrieve centroids
        centroids = geojson.centroid
        lat_long_centroids = list(map(util_lat_long_geopandas_point, centroids))
        geojson['centroid'] = lat_long_centroids
        mapper_centroid = {}
        for _, row in geojson.iterrows():
            mapper_centroid.update({row['id']: row['centroid']})
    
        # read temporal data
        df_today = pandas.read_csv(FILE_TELEPHONY_DAY, sep=';')
        df_today.rename(columns={'ID': 'id'}, inplace=True)
    
        # to fix date
        df_today['H'] = '2019-08-01T' + df_today['H'].astype(str)
        df_today['Date'] = pandas.to_datetime(df_today['H'])
        # map id to centroid
        df_today['centroid'] = df_today['id'].map(mapper_centroid)
    
        # create map Folium, Bologna(lat,long)
        map_folium = folium.Map(location=[44.4992192, 11.2616459], zoom_start=10)
    
        # create data for heatmap
        dates = pandas.unique(df_today['Date'])
        df_today[['latitude', 'longitude']] = pandas.DataFrame(df_today['centroid'].tolist(), index=df_today.index)
        min_variable_weight = df_today['P'].min()
        max_variable_weight = df_today['P'].max()
        df_today['weight'] = (df_today['P'] - min_variable_weight) / (max_variable_weight - min_variable_weight)
    
        data_heat = [df_today.loc[df_today['Date'] == date, ['latitude', 'longitude', 'weight']].values.tolist() for date in dates]
        date_index = [pandas.to_datetime(str(date)).strftime('%Y-%m-%d %H:%M') for date in dates]
        print(date_index)
        # create Heatmap map
        folium.plugins.HeatMapWithTime(
            data_heat,
            index=date_index,
            #name='today',
            #overlay=False,
            radius=30
        ).add_to(map_folium)
    
        # add control
        folium.LayerControl().add_to(map_folium)
    
        # save result
        map_folium.save(OUTPUT)
    
