import pandas as pd
from tufast_matching_tool.maxflow import *
from tufast_matching_tool.general import DAYS,SHIFTS,SHIFT_TYPES

from general import generate_base_data_dict

def test_correctly_assign_shiftleads():
    data, shift_type_dict = generate_base_data_dict(6)
    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            shift_type_dict[key] = ["cut"]
    data["sl_cut"][0] = True
    for i in range(0,6):
        data["n_shifts"][i] = 21
        for d in DAYS:
            for s in SHIFTS:
                key = d + "_" + s
                data[key][i] = 1

    df = pd.DataFrame(data)

    base_mat = shiftplan_to_adj_mat(df)

    sl_mat = make_sl_adj_mat(df, base_mat, shift_type_dict)
    flow_sl = get_flow_from_adj_mat(sl_mat)
    w_mat = make_worker_adj_mat(df, base_mat, flow_sl, 2)
    flow = get_flow_from_adj_mat(w_mat)

    shift_list = get_shift_list(df, flow_sl, flow)

    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            assert shift_list[key]["lead"] == "person0"