import pandas as pd
from tufast_matching_tool.mincost import MatchingGraph
from tufast_matching_tool.general import DAYS,SHIFTS,SHIFT_TYPES

from general import generate_base_data_dict

def test_simple_matching():
    data, shift_type_dict = generate_base_data_dict(2)
    data["sl_cut"][0] = True
    data["wed_9"][0] = 1
    data["wed_9"][1] = 1
    shift_type_dict["wed_9"] = ["cut"]
    graph = MatchingGraph(pd.DataFrame(data),shift_type_dict)
    flow = graph.get_flow()
    assert flow is not None
    shift_list = graph.get_shift_list(flow)
    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            if key != "wed_9":
                assert shift_list[key]["lead"] == None
                assert shift_list[key]["worker"] == []
            else:
                assert shift_list[key]["lead"] == "person0"
                assert shift_list[key]["worker"] == ["person1"]

def test_shift_lead_only_matched_when_avail():
    data, shift_type_dict = generate_base_data_dict(6)
    data["sl_cut"][3] = True
    data["wed_9"][3] = 0
    data["wed_9"][4] = 1
    shift_type_dict["wed_9"] = ["cut"]
    graph = MatchingGraph(pd.DataFrame(data),shift_type_dict)
    flow = graph.get_flow()
    assert flow is not None
    shift_list = graph.get_shift_list(flow)
    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            if key != "wed_9":
                assert shift_list[key]["lead"] == None
                assert shift_list[key]["worker"] == []

def test_worker_one_only_matched_when_avail():
    data, shift_type_dict = generate_base_data_dict(6)
    data["n_shifts"][3] = 21
    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            data[key][3] = 1
    data["sl_cut"][3] = True
    data["wed_9"][4] = 0
    shift_type_dict["wed_9"] = ["cut"]
    graph = MatchingGraph(pd.DataFrame(data),shift_type_dict)
    flow = graph.get_flow()
    assert flow is not None
    shift_list = graph.get_shift_list(flow)
    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            if key != "wed_9":
                assert shift_list[key]["lead"] == None
                assert shift_list[key]["worker"] == []

def test_only_assigne_proper_lead():
    data, shift_type_dict = generate_base_data_dict(6)
    for t in SHIFT_TYPES:
        if t != "cut":
            data["sl_"+t][0] = True
    data["wed_9"][2] = 1
    data["wed_9"][3] = 1
    shift_type_dict["wed_9"] = ["cut"]
    graph = MatchingGraph(pd.DataFrame(data),shift_type_dict)
    flow = graph.get_flow()
    assert flow is None

def test_correctly_assign_shiftleads():
    data, shift_type_dict = generate_base_data_dict(6)
    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            shift_type_dict[key] = ["cut"]
    data["sl_cut"][0] = True
    data["sl_cut"][1] = True
    data["n_shifts"][0] = 21
    data["n_shifts"][1] = 21
    for i,d in enumerate(DAYS):
        for s in SHIFTS:
            key = d + "_" + s
            if i % 2 == 1:
                data[key][0] = 1
            else:
                data[key][1] = 1
    for i in range(2,6):
        data["n_shifts"][i] = 21
        for d in DAYS:
            for s in SHIFTS:
                key = d + "_" + s
                data[key][i] = 1
    graph = MatchingGraph(pd.DataFrame(data),shift_type_dict)
    flow = graph.get_flow()
    assert flow is not None
    shift_list = graph.get_shift_list(flow)
    for i,d in enumerate(DAYS):
        for s in SHIFTS:
            key = d + "_" + s
            if i % 2 == 1:
                assert shift_list[key]["lead"] == "person0"
            else:
                assert shift_list[key]["lead"] == "person1"

            