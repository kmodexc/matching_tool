import pandas as pd
import openpyxl
from package.general import DAYS, SHIFTS, SHIFT_TYPES
from package.maxflow import max_flow_matching
from package.mincost import min_cost_matching

START_COL_NAMES = 3
START_ROW_AVAIL = 13
START_ROW_SHIFT_TYPES = 5
START_ROW_MECA = 23
LAST_ROW_MECA = 59


def read_sheet(file="Shiftsplan_lux025.xlsx", sheet="ShiftList_KW16"):
    dataframe = openpyxl.load_workbook(file)
    dataframe1 = dataframe[sheet]
    name = None
    n_shifts = None

    data = {'name': [], 'n_shifts': [], 'beer': []}

    for d in DAYS:
        for s in SHIFTS:
            key = d + "_" + s
            data[key] = []

    for st in SHIFT_TYPES:
        data["sl_" + st] = []

    START_COL_AVAIL_REL = 2
    START_COL_AVAIL = START_COL_NAMES+START_COL_AVAIL_REL
    START_COL_SHIFTLEADS_REL = START_COL_AVAIL_REL+(len(SHIFTS)*len(DAYS))
    START_COL_SHIFTLEADS = START_COL_NAMES+START_COL_SHIFTLEADS_REL
    LAST_COL = START_COL_SHIFTLEADS+len(SHIFT_TYPES) - 1
    LAST_ROW_SHIFT_TYPES = START_ROW_SHIFT_TYPES + len(SHIFT_TYPES) - 1

    shift_type_dict = {}

    for row in range(START_ROW_SHIFT_TYPES, dataframe1.max_row):
        for i, col in enumerate(dataframe1.iter_cols(START_COL_NAMES, LAST_COL)):
            if i == 0 and row >= START_ROW_AVAIL:
                name = col[row].value
                if name != None:
                    data['name'].append(name)
                    if START_ROW_MECA <= row <= LAST_ROW_MECA:
                        data['team'].append('meca')
                    else:
                        data['team'].append('other')
            elif i == 1 and row >= START_ROW_AVAIL:
                if name != None:
                    n_shifts = col[row].value
                    data['beer'].append(1 if n_shifts is None else 0)
                    if n_shifts is None:
                        n_shifts = 0
                    data['n_shifts'].append(int(n_shifts))
            elif name != None and i < START_COL_SHIFTLEADS_REL and row >= START_ROW_AVAIL:
                key = DAYS[(i - START_COL_AVAIL_REL) // len(SHIFTS)] + "_" + SHIFTS[(i - START_COL_AVAIL_REL) % len(SHIFTS)]
                if col[row].value != None:
                    data[key].append(1)
                else:
                    data[key].append(0)
            elif name != None and row >= START_ROW_AVAIL:
                key = "sl_" + SHIFT_TYPES[i - START_COL_SHIFTLEADS_REL]
                if col[row].value != None and len(str(col[row].value)) > 0:
                    data[key].append(True)
                else:
                    data[key].append(False)
            elif row < START_ROW_AVAIL and row < LAST_ROW_SHIFT_TYPES and i >= START_COL_AVAIL_REL and i < START_COL_SHIFTLEADS_REL:
                key = DAYS[(i - START_COL_AVAIL_REL) // len(SHIFTS)] + "_" + SHIFTS[(i - START_COL_AVAIL_REL) % len(SHIFTS)]
                shift_type_id = SHIFT_TYPES[row - START_ROW_SHIFT_TYPES]
                if key not in shift_type_dict:
                    shift_type_dict[key] = []
                if col[row].value is not None:
                    shift_type_dict[key].append(shift_type_id)

    df = pd.DataFrame(data)

    # for row in range(1, dataframe["ShiftLeads"].max_row):
    #     for i, col in enumerate(dataframe["ShiftLeads"].iter_cols(1, 8)):
    #         if i == 0:
    #             name = col[row].value
    #         elif name != None and name != "" and col[row].value != None and len(str(col[row].value)) > 0:
    #             df.loc[df["name"] == name, "sl_" + SHIFT_TYPES[i - 1]] = True

    return df, shift_type_dict

def get_beer_list(df):
    obj = {}
    beers = df[df["beer"] > 0]
    obj = {}
    for n in list(beers['name']):
        obj[n] = df[df["name"] == n]["beer"]
    return obj

def extract_names_from_shift_list(shift_list):
    names = set()
    for key in shift_list:
        if shift_list[key]['lead']:
            names.add(shift_list[key]['lead'])
        for worker in shift_list[key]['worker']:
            names.add(worker)
    return list(names)
 
def get_not_assigned_names(df, assigned_names):
    not_assigned = df[(df['n_shifts'] >= 1) & (~df['name'].isin(assigned_names))]
    assigned_meca = df[(df['team'] == 'meca') & (df['name'].isin(assigned_names))]

    not_assigned = pd.concat([not_assigned, assigned_meca])
    
    meca_not_assigned = not_assigned[not_assigned['team'] == 'meca']
    other_not_assigned = not_assigned[not_assigned['team'] != 'meca']
    
    return meca_not_assigned['name'].tolist() + other_not_assigned['name'].tolist()



def switch_names(df, assigned_names, not_assigned_names):
    num_pairs_to_swap = min(len(assigned_names), len(not_assigned_names))

    name_to_index = {name: idx for idx, name in enumerate(df['name'])}

    assigned_indices = [name_to_index[name] for name in assigned_names]
    not_assigned_indices = [name_to_index[name] for name in not_assigned_names]

    temp = df.loc[assigned_indices].copy()
    df.loc[assigned_indices] = df.loc[not_assigned_indices].values
    df.loc[not_assigned_indices] = temp.values

    return df


def main():
    import PySimpleGUI as sg
    from datetime import date
    import os
    import sys

    day_texts = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thr": "Thursday", "fri": "Friday",
                 "sat": "Saturday", "sun": "Sunday"}
    time_texts = {"9": "9:00 - 13:00", "14": "14:00 - 18:00", "18": "18:00 - 22:00"}

    layout = [[sg.Column([[sg.Text("Excel file:")], [sg.Text("Sheet name:")]]),
                sg.Column([[sg.InputText(key="-CURRENT-FILE-"), sg.FileBrowse()], [sg.InputText("ShiftList_KW16", key="-CURRENT-SHEET-")]])],
              [sg.Column([[sg.Text("Previous Excel file:")], [sg.Text("Sheet name:")]]),
                sg.Column([[sg.InputText(key="-PREVIOUS-FILE-"), sg.FileBrowse()], [sg.InputText("ShiftList_KW15", key="-PREVIOUS-SHEET-")]])],
              [sg.Text("Maximum shift size:"), sg.InputText("3", key="-MAX-SHIFT-SIZE-", size=3), 
               sg.Checkbox("Higher accuracy but slower new algorithm", default=True, key="-USE-NEW-ALGO-")],
              [sg.Button('Generate Shiftplan'), sg.Button('Generate Beerlist'), sg.Text("Comment:"),
               sg.InputText(key="-COMMENT-", size=25)],
              [sg.Multiline("Hi ツ", size=(70, 15), key="-OUTBOX-")]]

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    icon_fqp = os.path.join(base_path, "tufast_img.ico")

    window = sg.Window('TUfast Matching Tool', layout, icon=icon_fqp)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break

        if event == "Generate Beerlist":
            fname = values[0]
            sname = values[1]
            comment = values["-COMMENT-"]
            df, shift_type_dict = read_sheet(fname, sname)
            beerlist = get_beer_list(df)
            bstr = ""
            for b in beerlist:
                bstr += "|| " + b + """ || Did not fill out shift plan || {X} || """ + date.today().strftime(
                    "%d.%m.%Y") + ' || ' + comment + ' ||\n'
            window["-OUTBOX-"].update(bstr)


        if event == 'Generate Shiftplan':
            previous_fname = values[2]
            previous_sname = values[3]
            current_fname = values[0]
            current_sname = values[1]
            if len(current_sname) == 0 or not os.path.isfile(current_fname):
                sg.popup("Fill in valid current shift plan file")
                continue

            if len(previous_sname) == 0 or not os.path.isfile(previous_fname):
                sg.popup("Fill in valid previous shift plan file")
                continue

            if len(current_sname) == 0:
                sg.popup("Fill in current sheet name")
                continue

            if len(previous_sname) == 0:
                sg.popup("Fill in previous sheet name")
                continue
            if len(values["-MAX-SHIFT-SIZE-"]) < 0 or not values["-MAX-SHIFT-SIZE-"].isnumeric():
                sg.popup("fill in maximum shift size")
                continue
            max_shift_size = int(values["-MAX-SHIFT-SIZE-"])
            print("Generate Matching for File:", current_fname, " Worksheet: ", current_sname)
            
            prev_df, prev_shift_type_dict = read_sheet(previous_fname, previous_sname)
            prev_shift_list = max_flow_matching(prev_df, prev_shift_type_dict, max_shift_size)  
            assigned_names_prev = extract_names_from_shift_list(prev_shift_list)
            not_assigned_names_prev = get_not_assigned_names(prev_df, assigned_names_prev)

            curr_df, curr_shift_type_dict = read_sheet(current_fname, current_sname)

            curr_df = switch_names(curr_df, assigned_names_prev, not_assigned_names_prev)

            if values["-USE-NEW-ALGO-"]:
                if max_shift_size != 3:
                    sg.popup("the new algorithm is only implemented for max shiftsize of 3. use the old algo or set shiftsize to 3.")
                    shift_list = []
                else:
                    #no use because it takes time
                    #window["-OUTBOX-"].update("Please wait. The new Algorithm is slower :)")
                    shift_list = min_cost_matching(curr_df, curr_shift_type_dict)
            else:
                shift_list = max_flow_matching(curr_df, curr_shift_type_dict,max_shift_size)

            if shift_list is None:
                window["-OUTBOX-"].update("Algorithm didnt find a shift plan ¯\\_(ツ)_/¯")
                continue

                
        
            sl_str = ""
            shift_count = 0
            worker_count = 0
            for k in shift_list:
                day, time = k.split("_")
                sl_str += day_texts[day] + " " + time_texts[time] + "\n"
                if shift_list[k]["lead"] is None:
                    sl_str += "None\n"
                else:
                    shift_count += 1
                    worker_count += len(shift_list[k]["worker"])
                    sl_str += "@" + shift_list[k]["lead"] + " (lead)\n"
                    for m in shift_list[k]["worker"]:
                        sl_str += "@" + m + "\n"
                sl_str += "\n"
            print("Number of Shifts:", shift_count)
            print("Number of Workers:", worker_count)
            window["-OUTBOX-"].update(sl_str)

    window.close()


if __name__ == "__main__":
    main()
