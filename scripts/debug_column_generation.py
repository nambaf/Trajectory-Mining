from scripts.folium_lib.utils_folium import util_lat_long_geopandas_point
from scripts.lib_column_generation import *
import folium
import pandas
import geopandas
import branca
import numpy

if __name__ == "__main__":
    FILE_LAYER = '../data/layers_geojson.geojson'
    FILE_TELEPHONY_DAY = '../data/P15_uni_20190929.csv'
    STR_CONCAT_ONLYFORSINGLEFILE_CAUSE_TUNIX = '2019-09-29T'
    #OUTPUT = "PRIVATE DATA.html"
    #DEBUG_MASTER = "../PRIVATE DATA/output/example_application_debug_master.html"

    # read temporal data
    b_center = [
        '08|037|006|003|003',
        '08|037|006|007|007',
        '08|037|006|006|006',
        '08|037|006|008|081',
        '08|037|006|003|031',
        '08|037|006|008|008',
        '08|037|006|006|062',
        '08|037|006|007|072',
        '08|037|006|005|005',
        '08|037|006|002|022'
    ]

    pi_graph_no_time = {
        b_center[0]: [b_center[1], b_center[2], b_center[3], b_center[4], b_center[5], b_center[9]],
        b_center[1]: [b_center[0], b_center[2], b_center[3], b_center[7], b_center[8], b_center[9]],
        b_center[2]: [b_center[0], b_center[1], b_center[3], b_center[6], b_center[7]],
        b_center[3]: [b_center[0], b_center[1], b_center[2], b_center[4], b_center[5], b_center[6]],
        b_center[4]: [b_center[0], b_center[3], b_center[5], b_center[9]],
        b_center[5]: [b_center[0], b_center[3], b_center[4], b_center[6]],
        b_center[6]: [b_center[2], b_center[3], b_center[5], b_center[7]],
        b_center[7]: [b_center[1], b_center[2], b_center[6], b_center[8]],
        b_center[8]: [b_center[1], b_center[7], b_center[9]],
        b_center[9]: [b_center[0], b_center[1], b_center[4], b_center[8]]
    }

    geojson = geopandas.read_file(FILE_LAYER)
    # retrieve centroids
    centroids = geojson.centroid
    lat_long_centroids = list(map(util_lat_long_geopandas_point, centroids))
    geojson['centroid'] = lat_long_centroids
    mapper_centroid = {}
    for _, row in geojson.iterrows():
        mapper_centroid.update({row['id']: row['centroid']})

    data_cell = pandas.read_csv(FILE_TELEPHONY_DAY, sep=';')
    data_cell.rename(columns={'ID': 'id'}, inplace=True)
    # data_cell = data_cell.loc[data_cell['id'].isin(b_center)]
    data_cell = data_cell[(data_cell['H'].str.contains(u'18:')) | (data_cell['H'].str.contains(u'19:00'))]
    data_cell.loc[:, 'H'] = STR_CONCAT_ONLYFORSINGLEFILE_CAUSE_TUNIX + data_cell['H'].astype(str)

    # map cell to an index
    id_dict = {}
    for index, value in enumerate(geojson['id']):
        id_dict.update({value: index})

    data_cell.loc[:, 'cell_id'] = data_cell['id'].map(id_dict)

    # create sliced datatrame to create data dict for slider
    simpler_df = data_cell[['H', 'cell_id']]
    simpler_df.loc[:, 'H'] = pandas.to_datetime(simpler_df['H'])

    # data slider
    simpler_df.loc[:, 'H_UNIX'] = simpler_df['H'].apply(lambda x: x.replace().timestamp())
    simpler_df.loc[:, 'H_UNIX'] = numpy.array(simpler_df['H_UNIX']).astype('U10')
    data_cell.loc[:, 'H_UNIX'] = simpler_df['H_UNIX'].astype(int)

    N, T, N_T = setup_n_t_master_problem(b_center, data_cell['H_UNIX'])
    pi_graph, q_true = setup_pi_graph_master_problem(N, T, data_cell[['id', 'H_UNIX', 'P']])

    # run column generation
    while 1:
        pi_graph_set, J = generate_j_master_problem(pi_graph)
        mld, paths_by_node, x, e = create_master_problem(J, N_T, N, T, q_true, pi_graph, weight_reg_long_path=2)
        solution, df_sol_x, df_sol_e = solve_master_problem(mld, x, e)
        print(solution)
        # print('Best traj found:\n ')
        # print(pi_graph_set[df_sol_x.idxmax()[1]])
        constraints = []
        distances = {}
        for i in range(0, len(paths_by_node.keys()) * 2):
            c = mld.get_constraint_by_index(i)
            constraints.append(c)
        duals = mld.dual_values(constraints)
        for index_key, key in enumerate(paths_by_node):
            lambda11 = duals[index_key * 2]
            lambda12 = duals[index_key * 2 + 1]
            distances.update({key: lambda11 - lambda12})  # +lambda11 - lambda12 per ogni nodo i, tempo t

        # ottengo pool di traiettorie da aggiungere a master, lunghezza massima fissata, peso assocciato in base a distances
        dsts, spts = pricing_problem(paths_by_node, pi_graph_no_time, distances, limit_time=1569783600, max_len=5)
        print('Duplicates?', any(spts.count(x) > 1 for x in spts))
        path_generated = [list(path) for path in spts]  # si può evitare??
        if len(path_generated) == 0:
            print('Done')
            print(solution)
            break
        # aggiungo trovate a pi_graph e avvio iterazione
        pi_graph = pi_graph + path_generated
        print('Numero traiettorie totale da analizzare:', len(pi_graph))