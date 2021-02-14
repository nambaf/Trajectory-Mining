import docplex.mp.model as cplex


def setup_n_t_master_problem(list_of_cells, list_of_steps, verbose = 0):
    """
    Setup variables of the Master problem see doc.

    1 step Master Problem (only first iteration)

    :param: list_of_cells: list
        list of aces
    :param: list_of_steps: list
        list of timeslots
    :param: verbose: int
        enable verbose
    :return: list
        set of aces, parameter N
    :return: list
        set of time steps, paramter T
    :return: list
        list of tuple (i_n,t_m)
    """
    N = list(set(list_of_cells))  # set dei nodi
    T = list(set(list_of_steps))  # set dei time step
    N_T = [(i, t) for i in N for t in T]

    if verbose:
        print('Set delle celle:', N)
        print('Set dei time step:', T)
        print('N_T:', N_T)
        print('')
    return N, T, N_T


def generate_self_paths_timed(N, T):
    """
    Generate complete self node for the time-unfolded graph.
    First version of the Master Problem that use for the initialization only the self-nodes.
    An easy way to to have the init distance parameter of all possible (node,time step) for the Pricing Algthm.

    :param N: list
        parameter N Master Problem
    :param T: list
        parameter T Master Problem
    :return: list
        list of complete self-paths.
        Ex [[(n0,t0),(n0,t1)],[(n1,t0),(n1,t1)]]
    """
    paths = []
    for node in N:
        self_path = []
        for step in T:
            self_path.append((node, step))
        paths.append(self_path)
    return paths


def setup_pi_graph_master_problem(N, T, subset_q_true, verbose = 0):
    """
    First version master problem:
    Load complete self-paths and generate q_true parameter for the Master Problem (see doc.)
    Self-paths time-unfolded graph are important because there is an init parameter (node,time step) for the Pricing Problem

    2 step Master Problem (only first iteration)

    :param: N: list
        parameter N Master Problem
    :param: T: list
        parameter T Master Problem
    :param: subset_q_true: Dataframe
        Dataframe that contains
        id -> id cell as str
        H_UNIX -> time step as time unix
        P -> presence var cell as int
    :param: verbose: int
        enable verbose
    :return: list
        list of complete self-paths
    :return: dict
        parameter q_true Master Problem
    """
    pi_graph = generate_self_paths_timed(N, T)

    q_true = {(row['id'], row['H_UNIX']): row['P'] for index, row in
              subset_q_true.iterrows()}  # conteggio dispositivi nodo i a istante t
    if verbose:
        print('q_true:', q_true)

    return pi_graph, q_true


def generate_j_master_problem(pi_graph, verbose = 0):
    """
    Given set of paths, generate a dict useful to retrive path by id (optimizing future searches)
    Return J parameter for the Master Problem

    3 step Master Problem in the first iteration, 1 step in the continuous iteration

    :param pi_graph: list
        list of paths, input pool for the selection process of Master Problem
    :param verbose: int
        enable verbose
    :return: dict
        dict of paths with the index of the position as key (unique identifier of path)
    :return: list
        parameter J Master Problem
    """
    pi_graph_set = {index: traj for index, traj in enumerate(pi_graph)}

    J = list(pi_graph_set.keys())

    if verbose:
        print('PI GRAPH:', pi_graph)
        print('')
        print('Numero traiettorie trovate:', len(J))
        print('')

    return pi_graph_set, J


def build_master_problem_contraints(paths, mld, x, e, q_true):
    """
    Given the Master Problem model and variables, build the constraints
    and return a dict with the index of a path that contains the key (node, time step)

    :param paths: list
        list of paths as input pool of Master Problem
    :param mld: Model
        Master Problem model
    :param x: var
        x parameter Master Problem
    :param e: var
        e parameter Master Problem
    :param q_true: dict
        q_true parameter Master Problem
    :return: dict
        dict of (node,time step) that appear in a specific path (identified by index)
    """
    paths_by_node = {}
    for j, nlist in enumerate(paths):
        for i, t in nlist:
            if (i, t) in paths_by_node:
                paths_by_node[i, t].append(j)
            else:
                paths_by_node[i, t] = [j]

    for i, t in paths_by_node:
        # build constraint

        mld.add_constraint(e[i, t] - mld.sum(x[j] for j in paths_by_node[i, t]) >= -q_true[i, t])
        mld.add_constraint(e[i, t] + mld.sum(x[j] for j in paths_by_node[i, t]) >= q_true[i, t])
    return paths_by_node


def create_master_problem(J, N_T, N, T, q_true, pi_graph, weight_reg_long_path = 0):
    """
    Create Master Problem model

    4 step Master Problem in the first iteration, 2 step in the continuous iteration

    :param J: list
        J parameter Master Problem
    :param N_T: list
        list of tuple (i_n,t_m), parameter Master Problem
    :param N: list
        N parameter Master Problem
    :param T: list
        T parameter Master Problem
    :param q_true: dict
        q_true parameter Master Problem
    :param pi_graph: list
        list of paths as input pool of Master Problem
    :param weight_reg_long_path: int
        const weight if want to add regularizer that increase search long_path(with great contribution).
        I scenario see doc.
    :return: Model
        Master Problem model
    :return: dict
        dict of (node,time step) that appear in a specific path (identified by index)
    :return: var
        x parameter Master Problem
    :return: var
        e parameter Master Problem
    """
    mld = cplex.Model('Master problem')
    x = mld.continuous_var_dict(J, lb=0, name='x')
    e = mld.continuous_var_dict(N_T, lb=0, name='e')

    paths_by_node = build_master_problem_contraints(pi_graph, mld, x, e, q_true)
    if weight_reg_long_path != 0:
        cotruire espressione e sistemare concatenazione
        #mld.minimize(mld.sum(e[i, t]) + weight_reg_long_path*x[j] for i in N for t in T for j in paths_by_node[i, t]))
    else:
        mld.minimize(mld.sum(e[i, t] for i in N for t in T))

    return mld, paths_by_node, x, e


def solve_master_problem(mld, x, e, verbose = 0, log = False, path_lp = 'C:\\Users\\marco\\Documents\\POLIS-EYE\\Trajectory-Project\\Simulator\\polis-eye\\output\\Master.lp'):
    """
    Given Master Problem model, solve it and return the solution

    Last step Master Problem
    5 step Master Problem in the first iteration, 3 step in the continuous iteration

    :param mld: Model
        Master Problem model
    :param x: var
        x var Master Problem
    :param e: var
        e var Master Problem
    :param verbose: int
        enable verbose
    :param log: bool
        enable log cplex
    :param path_lp: str
        path str + .lp extension, where lp file must be saved
    :return: Solution
        cplex solution
    :return: Dataframe
        x solution Dataframe
    :return: Dataframe
        e solution Dataframe
    """
    solution = mld.solve(log_output=log)

    mld.export_as_lp(path=path_lp)
    df_sol_x = solution.get_value_df(x)
    df_sol_e = solution.get_value_df(e)

    if verbose:
        print(solution)
        print('Shape SOL X:', df_sol_x[df_sol_x['value'] != 0].shape)
        print('')
        print('SOL E:\n', df_sol_e[df_sol_e['value'] != 0])
        print('')
        print('Best traj DF x:\n ', df_sol_x.idxmax())
        print('')

    return solution, df_sol_x, df_sol_e


def pricing_problem(paths_by_node, pi_graph_no_time, distances, limit_time, max_len = 3,):
    """
    TODO
    """
    dsts, spts = [], []
    for start_node in paths_by_node: # loop over possible roots
        # Collect shortest paths from this root
        #print('Start node (node n, time t):',start_node)
        dst, spt = shortest_paths_from_root(start_node, pi_graph_no_time, distances, limit_time, max_len)
        for node_time in dst:
            if dst[node_time] < 0:
                spts.append(spt[node_time])
            #if dst[node_time] == 0:
            #    print("dst:",dst[node_time])
            #    print("percorso nullo",spt[node_time])
        #dsts += list(dst.values())
        #spts += list(spt.values())
    return dsts, spts


def shortest_paths_from_root(start_node, pi_graph_no_time, distances, limit_time, max_len):
    """

    """
    root = start_node  # (node i, time step t)
    spt = {root: {root}}
    dst = {root: distances[root]}  # shortest path distances
    # print('INIT spt e dst:',spt, dst)
    # constant for the calc of the next time step with an interval of 15 minutes.
    # datetime.timestamp() gives seconds, not milliseconds
    k_next_timeunix = 900
    for step in range(0, max_len - 1):  # loop over the possible cycle lengths -> aggiungo componente tempo dopo
        ndst, nspt = {}, {}
        # print('>>>Step',step)
        for node_time_visited in dst:  # process all visited nodes -> (node i, time t)
            time_next = node_time_visited[1] + k_next_timeunix
            if (time_next > limit_time):  # out of limit
                break
            for next_node in pi_graph_no_time[node_time_visited[0]]:  # loop over outgoing arcs
                # print('Analisi node_visited:',node_time_visited[0],node_time_visited[1])
                tuple_next = (next_node, time_next)
                # print('Analisi next:',next_node, time_next)

                # Dijkstra update
                if tuple_next not in ndst or dst[node_time_visited] + distances[tuple_next] < ndst[tuple_next]:
                    # print('Update distance next_node:', tuple_next)
                    ndst[tuple_next] = dst[node_time_visited] + distances[tuple_next]
                    nspt[tuple_next] = spt[node_time_visited] | {tuple_next}
                elif dst[node_time_visited] + distances[tuple_next] == ndst[tuple_next]:
                    # penalty cicles ?
                    print('Add blackbox func')

        dst, spt = ndst, nspt
    # print('>>>Done')
    return dst, spt