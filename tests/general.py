from tufast_matching_tool.general import DAYS,SHIFTS,SHIFT_TYPES

def generate_base_data_dict(n_people):
    data = {'name': [], 'n_shifts': [], 'beer': []}
    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            data[key] = []
    for st in SHIFT_TYPES:
        data["sl_" + st] = []

    for i in range(n_people):
        data["name"].append("person"+str(i))
        data["n_shifts"].append(1)
        data["beer"].append(0)
        for d in DAYS:
            for s in SHIFTS:
                key = d + "_" + s
                data[key].append(0)
        for st in SHIFT_TYPES:
            data["sl_" + st].append(False)

    shift_type_dict = {}
    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            shift_type_dict[key] = []
    return data, shift_type_dict