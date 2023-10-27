import numpy as np
from functools import reduce
import networkx as nx
from general import DAYS, SHIFTS, get_shift_index

class MatchingGraph:

    def __init__(self,df,shift_type_dict,copy_instance=None):

        if copy_instance is not None:
            self.graph = copy_instance.graph.copy()
            self.node_offsets = copy_instance.node_offsets
            self.node_lengths = copy_instance.node_lengths
            self.df = copy_instance.df
            return
        
        assert copy_instance is None

        shift_degree = [df[s].sum() for s in shift_type_dict]
        len([x for x in shift_degree if x < 2])
        for i,key in enumerate(shift_type_dict):
            if shift_degree[i] < 2:
                shift_type_dict[key] = []

        node_lengths = [1,
                        df.shape[0],
                        (df.shape[0] * len(SHIFTS) * len(DAYS)),
                        (len(SHIFTS) * len(DAYS)),
                        (len(SHIFTS) * len(DAYS)),
                        (len(SHIFTS) * len(DAYS)),
                        1]
        node_offsets = [reduce(lambda x,y: x+y, node_lengths[:i]) for i in range(1,len(node_lengths))]
        print(node_offsets)
        n_nodes = reduce(lambda x,y: x+y, node_lengths)
        graph_matrix = np.zeros((n_nodes, n_nodes), dtype="int64")
        graph_matrix[0, node_offsets[0]:node_offsets[1]] = df["n_shifts"].to_numpy()
        #graph_matrix[node_offsets[1]:node_offsets[2], -1] = 3

        shiftlead_vector = np.zeros(df.shape[0]*len(SHIFTS)*len(DAYS))
        stretch_factor = len(SHIFTS)*len(DAYS)

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
            shiftlead_vector[column_index::stretch_factor] = df_sl
            graph_matrix[node_offsets[1]:node_offsets[2],node_offsets[2]+column_index] = shiftlead_vector

        for index, row in df.iterrows():
            avai = row.to_numpy()[3:3+(len(SHIFTS)*len(DAYS))]
            start_col = node_offsets[1]+(index*len(SHIFTS)*len(DAYS))
            end_col = node_offsets[1]+((index+1)*len(SHIFTS)*len(DAYS))
            graph_matrix[node_offsets[0]+index, start_col:end_col] = avai
            #graph_matrix[start_col:end_col, node_offsets[2]:node_offsets[3]] = np.identity(len(SHIFTS)*len(DAYS))
            graph_matrix[start_col:end_col, node_offsets[3]:node_offsets[4]] = np.identity(len(SHIFTS)*len(DAYS))
            graph_matrix[start_col:end_col, node_offsets[4]:node_offsets[5]] = np.identity(len(SHIFTS)*len(DAYS))


        graph_matrix[node_offsets[4]:node_offsets[5], 0] = 1
        graph_matrix[0,node_offsets[5]] = 1000

        edge_costs={}
        for i in range(n_nodes):
            for j in range(n_nodes):
                if j == 0 and node_offsets[4] <= i < node_offsets[5]:
                    edge_costs[i,j] = -1
                else:
                    edge_costs[i,j] = 0

        node_demands=np.zeros((n_nodes),dtype="int16")
        for i in range(n_nodes):
            if i == 0:
                node_demands[i] = -1000
            elif node_offsets[2] <= i < node_offsets[4]:
                node_demands[i] = 1
            elif i == node_offsets[5]:
                node_demands[i] = 1000 - (2*len(SHIFTS)*len(DAYS))
            else:
                node_demands[i] = 0

        # disable shifts
        def __disable_shift(i):
            node_demands[node_offsets[2]+i] = 0
            node_demands[node_offsets[3]+i] = 0
            node_demands[0] += 2
            graph_matrix[:,node_offsets[4]+i] = 0

        for s in shift_type_dict:
            keysplit = s.split('_')
            column_index = DAYS.index(keysplit[0]) * 3 + SHIFTS.index(keysplit[1])
            if len(shift_type_dict[s]) == 0:
                __disable_shift(column_index)
                print("disabled shift",s)

        graph = nx.from_numpy_array(graph_matrix, create_using=nx.DiGraph())

        nx.set_edge_attributes(graph, edge_costs, "cost")

        node_demands_dict = dict(zip(range(len(node_demands)),list(node_demands),))
        nx.set_node_attributes(graph, node_demands_dict, "demand")

        self.graph = graph
        self.node_offsets = node_offsets
        self.node_lengths = node_lengths
        self.df = df

    def get_flow(self):
        try:
            flow = nx.min_cost_flow(self.graph,capacity="weight",weight="cost")
            return flow
        except nx.NetworkXUnfeasible:
            print("no flow found")
            return None

    def get_flow_value(self):
        try:
            flow = nx.min_cost_flow_cost(self.graph,capacity="weight",weight="cost")
            return flow
        except nx.NetworkXUnfeasible:
            print("no flow found")
            return None

    def disable_shift(self,i):
        self.graph.nodes[self.node_offsets[2]+i]["demand"] = 0
        self.graph.nodes[self.node_offsets[3]+i]["demand"] = 0
        self.graph.nodes[0]["demand"] = self.graph.nodes[0]["demand"] + 2
        for j in range(self.node_offsets[1],self.node_offsets[2]):
            try:
                self.graph.remove_edge(j,self.node_offsets[4]+i)
            except:
                pass

    def get_best_flow_by_remove_shift(self,avai_shifts,recursion_level=0):
        best_flow_shift_combi = None
        best_flow_shift_value = 1000
        for d in DAYS:
            for s in SHIFTS:
                column_index = DAYS.index(d) * 3 + SHIFTS.index(s)
                
                if column_index not in avai_shifts:
                    continue

                graph_copy = self.copy()
                graph_copy.disable_shift(column_index)

                if recursion_level == 0:
                    flow_combi = []
                    flow_value = graph_copy.get_flow_value()
                    print("0 try",d,s,"value",flow_value)
                else:
                    print(recursion_level,"try",d,s)
                    avai_shifts_copy = avai_shifts.copy()
                    avai_shifts_copy.remove(column_index)
                    retval = graph_copy.get_best_flow_by_remove_shift(avai_shifts_copy,recursion_level-1)
                    if retval is not None:
                        flow_combi = retval[0]
                        flow_value = retval[1]
                    else:
                        flow_combi = None
                        flow_value = None

                if flow_combi is not None and flow_value is not None and best_flow_shift_value > flow_value:
                    best_flow_shift_value = flow_value
                    best_flow_shift_combi = flow_combi + [d+"_"+s]

        if best_flow_shift_combi is not None:
            return  best_flow_shift_combi,best_flow_shift_value

    def get_matched_person(self,flow,shift,position):
        shift_ind = get_shift_index(shift)
        for i in range(self.df.shape[0]*len(DAYS)*len(SHIFTS)):
            if (self.node_offsets[position]+shift_ind) in flow[i+self.node_offsets[1]] and flow[i+self.node_offsets[1]][self.node_offsets[position]+shift_ind] > 0:
                return (self.df.iloc[i//(len(DAYS)*len(SHIFTS))]["name"])
            
    def get_shift_list(self,flow):
        shift_list = {}
        for day in DAYS:
            for shift in SHIFTS:
                key = day + "_" + shift
                shift_list[key] = {"lead": None, "worker": []}
                lead = self.get_matched_person(flow,key,2)
                w1   = self.get_matched_person(flow,key,3)
                w2   = self.get_matched_person(flow,key,4)
                if lead != None:
                    shift_list[key]["lead"] = lead
                if w1 != None:
                    shift_list[key]["worker"].append(w1)
                if w2 != None:
                    shift_list[key]["worker"].append(w2)
        return shift_list
    
    def __copy__(self):
        return MatchingGraph(None,None,copy_instance=self)
    
    def copy(self):
        return self.__copy__()

def min_cost_matching(df,shift_type_dict):
    graph = MatchingGraph(df,shift_type_dict)
    flow = graph.get_flow()
    retval = None
    if flow is None:
        avai_shifts = [get_shift_index(s) for s in shift_type_dict if len(shift_type_dict[s]) > 0]
        for i in range(3):
            retval = graph.get_best_flow_by_remove_shift(avai_shifts,i)
            if retval is not None:
                break

    graph_copy = graph.copy()

    if retval is not None:
        for shift in retval[0]:
            graph_copy.disable_shift(get_shift_index(shift))
        flow = graph_copy.get_flow()

    if flow is None:
        return None
    
    shift_list = graph_copy.get_shift_list(flow)

    return shift_list
