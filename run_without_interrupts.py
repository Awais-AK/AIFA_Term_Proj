import numpy as np
import copy 
import pandas as pd
from problem_model import problem
import heapq
import networkx as nx

_EPS = 1e-4

"""
Charge to maximum required - Travel to other node - Repeat method 

Assumption: the path chosen for each vehicle is decided based on physically shortest path (not considering waiting)
Itna charge denge ki woh kisi bhi do node ke beech stuck nhi hoga

"""
class CTR(object):
    def __init__(self,p):
        self.p = p
        self.events_heap = []
        self.paths = []
        self.at = []
        self.time = []
        self.node_free_charging = [-1 for _ in range(p.n)]
        self.ev_events = []
        self.current_battery = []
    
    def get_paths(self):
        for i in range(self.p.k):
            self.paths.append(nx.shortest_path(self.p.Graphs[i],source=self.p.source_node[i],target=self.p.destination_node[i], weight='weight'))
            net_b = self.p.battery_usage_on_path(i,self.paths[-1])
            if abs(net_b - self.p.initial_battery[i]) <= _EPS or  net_b < self.p.initial_battery[i]:
                self.at.append(len(self.paths[-1])-1)
                self.time.append(net_b/self.p.discharging_rate[i])
                self.ev_events.append([(self.time[-1],f"reached without charging at destination on path {self.paths[-1]}")])
                continue

            self.at.append(0)
            b = self.p.max_battery[i] - self.p.initial_battery[i]
            self.current_battery.append(self.p.initial_battery[i])
            charge_complete_time = min(b,net_b-self.p.initial_battery[i])/self.p.charging_rate[i]
            if self.node_free_charging[self.paths[-1][0]] == -1:
                self.time.append(0)
                self.ev_events.append([(0,f"started charging at {self.paths[-1][0]}")])
                self.node_free_charging[self.paths[-1][0]] = charge_complete_time
            else:
                self.time.append(self.node_free_charging[self.paths[-1][0]])
                self.ev_events.append([(self.node_free_charging[self.paths[-1][0]],f"started charging at {self.paths[-1][0]}")])
                self.node_free_charging[self.paths[-1][0]] += charge_complete_time
        return

    def set_paths(self,paths):
        self.paths = paths
        for i in range(self.p.k):
            net_b = self.p.battery_usage_on_path(i,self.paths[i])
            if abs(net_b - self.p.initial_battery[i]) <= _EPS or  net_b < self.p.initial_battery[i]:
                self.at.append(len(self.paths[i])-1)
                self.time.append(net_b/self.p.discharging_rate[i])
                self.ev_events.append([(self.time[-1],f"reached without charging at destination on path {self.paths[i]}")])
                continue

            self.at.append(0)
            b = self.p.max_battery[i] - self.p.initial_battery[i]
            self.current_battery.append(self.p.initial_battery[i])
            charge_complete_time = min(b,net_b-self.p.initial_battery[i])/self.p.charging_rate[i]
            if self.node_free_charging[self.paths[i][0]] == -1:
                self.time.append(0)
                self.ev_events.append([(0,f"started charging at {self.paths[i][0]}")])
                self.node_free_charging[self.paths[i][0]] = charge_complete_time
            else:
                self.time.append(self.node_free_charging[self.paths[i][0]])
                self.ev_events.append([(self.node_free_charging[self.paths[i][0]],f"started charging at {self.paths[i][0]}")])
                self.node_free_charging[self.paths[i][0]] += charge_complete_time
        return

    def init_events(self):
        for i in range(self.p.k):
            if self.at[i]==len(self.paths[i])-1:
                continue
            net_b = self.p.battery_usage_on_path(i,self.paths[i])
            b = self.p.max_battery[i] - self.p.initial_battery[i]
            charge_complete_time = min(b,net_b-self.p.initial_battery[i])/self.p.charging_rate[i]
            self.events_heap.append((self.time[i]+charge_complete_time,i,'charging'))
            self.ev_events[i].append((self.time[i]+charge_complete_time,f"completed charging at {self.paths[i][0]}"))
            # self.time[i]+=charge_complete_time
        heapq.heapify(self.events_heap)

    def run(self):

        self.get_paths()
        self.init_events()

        while len(self.events_heap) > 0:
            event_complete_time,ev_id,etype = self.events_heap[0]
            heapq.heappop(self.events_heap)

            if etype == 'charging':
                if abs(self.node_free_charging[self.paths[ev_id][self.at[ev_id]]]-event_complete_time)<=_EPS:
                    self.node_free_charging[self.paths[ev_id][self.at[ev_id]]]=-1
                self.time[ev_id]=event_complete_time
                u,v = self.paths[ev_id][self.at[ev_id]],self.paths[ev_id][self.at[ev_id]+1]
                edge_travel_time = self.p.time_to_travel(ev_id,(u,v))
                heapq.heappush(self.events_heap,(self.time[ev_id]+edge_travel_time,ev_id,'traveling'))
                self.ev_events[ev_id].append((self.time[ev_id]+edge_travel_time,f"reached {v}"))
            elif etype == 'traveling':
                self.at[ev_id]+=1
                self.time[ev_id]=event_complete_time
                if self.at[ev_id]==len(self.paths[ev_id])-1:
                    continue

                u,v = self.paths[ev_id][self.at[ev_id]-1],self.paths[ev_id][self.at[ev_id]]

                b = self.p.battery_usage_on_path(ev_id,self.paths[ev_id][self.at[ev_id]:])
                curr_b = self.p.max_battery[ev_id] - self.p.battery_to_travel(ev_id,(u,v))
                if abs(b - curr_b) <= _EPS or  b < curr_b:
                    travel_complete_time = b/self.p.discharging_rate[ev_id]
                    self.time[ev_id]+=travel_complete_time
                    self.ev_events[ev_id].append((self.time[ev_id],f"reached destination on path {self.paths[ev_id][self.at[ev_id]:]}"))
                    self.at[ev_id]=len(self.paths[ev_id])-1
                    continue
                
                charge_complete_time = (min(self.p.max_battery[ev_id]-curr_b,b-curr_b))/self.p.charging_rate[ev_id]
                if self.node_free_charging[v] == -1:
                    # print(ev_id,v,len(self.paths),len(self.paths[ev_id]),len(self.time))
                    self.events_heap.append((self.time[ev_id]+charge_complete_time,ev_id,'charging'))
                    self.ev_events[ev_id].append((event_complete_time,f"started charging at {v}"))
                    self.ev_events[ev_id].append((self.time[ev_id]+charge_complete_time,f"completed charging at {v}"))
                    self.node_free_charging[v]=self.time[ev_id]+charge_complete_time
                else:
                    self.events_heap.append((max(self.time[ev_id],self.node_free_charging[v])+charge_complete_time,ev_id,'charging'))
                    self.ev_events[ev_id].append((self.node_free_charging[v],f"started charging at {v}"))
                    self.ev_events[ev_id].append((max(self.time[ev_id],self.node_free_charging[v])+charge_complete_time,f"completed charging at {v}"))
                    self.node_free_charging[v]=max(self.time[ev_id],self.node_free_charging[v])+charge_complete_time
            
            heapq.heapify(self.events_heap)
        
    def print_paths(self):
        for i in range(self.p.k):
            print(f"for EV {i} : {self.ev_events[i]}")
        return

p = problem.problem()

p.input("gen_testcase.txt")

p.make_graphs()

Thr_min = p.theoritical_minima()
print("Lower bound is: ",Thr_min,"\n")

sol = CTR(p)
sol.run()
# print(p.k)
# print(p.Graphs)

# print(sol.time)
print("output of algoritm is: ",np.max(sol.time),"\n")

print("Paths that are followed are:\n")
sol.print_paths()