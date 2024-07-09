import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow
import networkx as nx
import matplotlib.pyplot as plt
from .general import DAYS,SHIFTS

def shiftplan_to_adj_mat(df):
    n_nodes = 1 + df.shape[0] + (len(SHIFTS) * len(DAYS)) + 1
    graph_matrix = np.zeros((n_nodes, n_nodes), dtype="int64")
    graph_matrix[0, 1:(1 + df.shape[0])] = df["n_shifts"].to_numpy()
    graph_matrix[(1 + df.shape[0]):-1, -1] = 3
    for i, d in enumerate(DAYS):
        for j, s in enumerate(SHIFTS):
            key = d + "_" + s
            graph_matrix[1:(1 + df.shape[0]), (1 + df.shape[0] + (i * len(SHIFTS)) + j)] = df[key].to_numpy()
    return graph_matrix

def make_sl_adj_mat(df, graph_matrix_sl, shift_type_dict):
    graph_matrix_sl = graph_matrix_sl.copy()

    for s in shift_type_dict:
        df_sl = None
        for st in shift_type_dict[s]:
            if df_sl is None:
                df_sl = df["sl_" + st].to_numpy().copy()
            else:
                df_sl |= df["sl_" + st].to_numpy()
        if df_sl is None:
            df_sl = np.array(df.shape[0] * [False])
        keysplit = s.split('_')
        column_index = DAYS.index(keysplit[0]) * 3 + SHIFTS.index(keysplit[1])
        graph_matrix_sl[1:(1 + df.shape[0]), 1 + df.shape[0] + column_index][df_sl.transpose() == False] = 0

    graph_matrix_sl[(1 + df.shape[0]):-1, -1] = 1

    return graph_matrix_sl

def make_worker_adj_mat(df, graph_matrix, flow_sl, max_people_at_shift=3):
    graph_matrix = graph_matrix.copy()
    flow_shift_counts = flow_sl.flow.toarray()[(1 + df.shape[0]):-1, -1]
    flow_shift_counts[flow_shift_counts > 0] = max_people_at_shift
    graph_matrix[(1 + df.shape[0]):-1, -1] = flow_shift_counts
    sl_flow_only_pos = flow_sl.flow.toarray().copy()
    sl_flow_only_pos[sl_flow_only_pos < 0] = 0
    graph_matrix = graph_matrix - sl_flow_only_pos

    return graph_matrix

def get_flow_from_adj_mat(adj_mat):
    graph_mat = csr_matrix(adj_mat)
    flow = maximum_flow(graph_mat, 0, adj_mat.shape[0] - 1)
    return flow

def get_shift_list(df, flow_sl, flow, add_flow=None):
    np_flow = flow.flow.toarray()
    np_sl_flow = flow_sl.flow.toarray()
    shift_list = {}
    for i, day in enumerate(DAYS):
        for j, shift in enumerate(SHIFTS):
            key = day + "_" + shift
            ind_people = np.where(np_flow[1:(1 + df.shape[0]), (1 + df.shape[0] + (i * len(SHIFTS)) + j)] == 1)
            ind_sl = np.where(np_sl_flow[1:(1 + df.shape[0]), (1 + df.shape[0] + (i * len(SHIFTS)) + j)] == 1)
            shift_list[key] = {"lead": None, "worker": []}
            if len(ind_sl[0]):
                shift_list[key]["lead"] = df["name"][ind_sl[0][0]]
            for k in list(ind_people[0]):
                shift_list[key]["worker"].append(df['name'][k])
            if add_flow is not None:
                ind_people_2 = np.where(
                    add_flow.flow.toarray()[1:(1 + df.shape[0]), (1 + df.shape[0] + (i * len(SHIFTS)) + j)] == 1)
                for k in list(ind_people_2[0]):
                    shift_list[key]["worker"].append(df['name'][k])
    return shift_list

def max_flow_matching(df,shift_type_dict, max_shift_size):
    
    base_mat = shiftplan_to_adj_mat(df)

    shift_degree = [df[s].sum() for s in shift_type_dict]
    len([x for x in shift_degree if x < 2])
    for i,key in enumerate(shift_type_dict):
        if shift_degree[i] < 2:
            shift_type_dict[key] = []

    # Find the best flow, that results in the most shifts possible.

    best_sl_flow = None
    best_w_mat = None
    best_flow = None
    best_flow_sum_value = 0
    best_df = None

    for _ in range(50):
        df = df.sample(frac=1).reset_index(drop=True)
        base_mat = shiftplan_to_adj_mat(df)
        shift_type_dict_copy = shift_type_dict.copy()
        for _ in range(10):
            sl_mat = make_sl_adj_mat(df, base_mat, shift_type_dict_copy)
            flow_sl = get_flow_from_adj_mat(sl_mat)
            w_mat = make_worker_adj_mat(df, base_mat, flow_sl, 2)
            flow = get_flow_from_adj_mat(w_mat)

            shift_list = get_shift_list(df, flow_sl, flow)

            print(flow_sl.flow_value + flow.flow_value)

            for k in shift_list:
                if (shift_list[k]["lead"] is not None) and (
                        shift_list[k] is None or len(shift_list[k]["worker"]) == 0):
                    shift_type_dict_copy[k] = []
                    shift_list = None
                    break

            if shift_list is not None:
                break

        if (flow_sl.flow_value + flow.flow_value) > best_flow_sum_value:
            best_sl_flow = flow_sl
            best_w_mat = w_mat
            best_flow = flow
            best_flow_sum_value = (flow_sl.flow_value + flow.flow_value)
            best_df = df.copy()

    w_mat_2 = make_worker_adj_mat(best_df, best_w_mat, best_flow, max_shift_size - 1)
    flow_2 = get_flow_from_adj_mat(w_mat_2)
    shift_list = get_shift_list(best_df, best_sl_flow, best_flow, flow_2)
    print(best_sl_flow.flow_value + best_flow.flow_value + flow_2.flow_value)

    return shift_list

def draw_matching(df, adj_mat, out_file=None):
    G = nx.from_numpy_array(adj_mat)

    node_labels = ["start"]
    node_labels += list(df['name'])
    node_labels += [d + '_' + s for d in DAYS for s in SHIFTS]
    node_labels += ["end"]

    node_labels_obj = {}

    for i, v in enumerate(node_labels):
        node_labels_obj[i] = v

    G = nx.relabel_nodes(G, node_labels_obj)

    pos = []

    pos.append((0, 40))

    for i in range(1, 1 + df.shape[0]):
        pos.append((2, i - 1))

    for i in range(1 + df.shape[0], 1 + df.shape[0] + (len(SHIFTS) * len(DAYS))):
        pos.append((4, (i - 1 - df.shape[0]) * 4))

    pos.append((6, 40))

    pos_obj = {}

    for i, v in enumerate(pos):
        pos_obj[node_labels[i]] = v

    plt.figure(figsize=(15, 40))
    # labels = nx.get_edge_attributes(G,'weight')
    # nx.draw_networkx_edge_labels(G,pos,edge_labels=labels)
    nx.draw_networkx(G, arrows=True, pos=pos_obj)
    if out_file is None:
        plt.show()
    else:
        plt.savefig(out_file)
