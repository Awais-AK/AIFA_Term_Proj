class city:
    def __init__(self, num: int, dist_arr: list):
        self.num = num
        
        self.dist = dist_arr #dist_mat[num] #distance from other cities (list)
        

class car:
    def __init__(self, source: city, dest: city, Bat_in: float, discrg_rate: float, max_cap: float, avg_speed: float, crg_rate: float):
        #given
        self.src = source 
        self.dest = dest #destination city
        self.init_chrg = Bat_in #initial charge in the battery
        self.discrg_rate = discrg_rate #discharge rate
        self.max_cap = max_cap #maximum charge in battery
        self.crg_rate = crg_rate #charging rate
        self.avg_speed = avg_speed

        #found
        self.tot_time = None
        self.path = list()
    



def path_plot(car_s: car, city_list):
    class node:
        def __init__(self, cty: city, pred = None, h_cost = None, t_cost = None):
            self.cty = cty
            self.pred = pred
            self.h_cost = h_cost
            self.t_cost = t_cost
            self.f_cost = None
    node_list = list()
    for i in city_list:
        x = node(i)
        node_list.append(x)


    # supply heuristic value #
    op = list()
    op.append(car_s.dest.num)
    node_list[car_s.dest.num].h_cost = 0
    while(len(op) != 0):
        i = op.pop(0)
        for j in range(len(city_list[i].dist)):
            if city_list[i].dist[j] is not None:
                if node_list[j].h_cost is None:
                    node_list[j].h_cost = city_list[i].dist[j] + node_list[i].h_cost
                    op.append(j)
                elif node_list[j].h_cost > (city_list[i].dist[j] + node_list[i].h_cost):
                    node_list[j].h_cost = city_list[i].dist[j] + node_list[i].h_cost
                    op.append(j)
    #heuristic calculation done... #


    # A* algorithm search #
    closed = list()
    opent = list()
    opent.append(car_s.src.num)
    node_list[car_s.src.num].t_cost = 0
    node_list[car_s.src.num].f_cost = node_list[car_s.src.num].h_cost
    while(len(opent) != 0):
        i = opent.pop(0)
        if i == car_s.dest.num:
            #terminate
            break
        for j in range(len(city_list[i].dist)):
            if city_list[i].dist[j] is not None and city_list[i].dist[j] != 0 and city_list[i].dist[j] <= ((car_s.max_cap * car_s.avg_speed)/car_s.discrg_rate):
                cost = (city_list[i].dist[j]/car_s.avg_speed)*(1 + (car_s.discrg_rate/car_s.crg_rate))
                g = cost + (node_list[j].h_cost/car_s.avg_speed)
                if j not in opent and j not in closed:
                    node_list[j].t_cost = cost + node_list[i].t_cost
                    node_list[j].f_cost = node_list[i].t_cost + g
                    node_list[j].pred = i
                    opent.append(j)
                elif j in opent:
                    if node_list[j].t_cost > cost + node_list[i].t_cost:
                        node_list[j].t_cost = cost + node_list[i].t_cost
                        node_list[j].f_cost = node_list[i].t_cost + g
                        node_list[j].pred = i

    # A* search completed... optimal path found #

    # path finding
    path = list()
    i = car_s.dest.num
    while i == car_s.src.num:
        path.insert(0,i)
        i = node_list[i].pred
    path.insert(0,i)
    car_s.path = path
    #....path found

    #travel and charging time calulated
    travel_time = 0
    crg_time = 0
    for i in range(len(path)-1):
        di = city_list[path[i]].dist[path[i+1]]
        cost_crg = (di/car_s.avg_speed)*car_s.discrg_rate
        crg_time += cost_crg/car_s.crg_rate
        travel_time += (di/car_s.avg_speed)
    if crg_time*car_s.crg_rate < car_s.init_chrg:
        crg_time = 0
    else:
        crg_time = crg_time - (car_s.init_chrg/car_s.crg_rate)
    
    car_s.tot_time = travel_time + crg_time

    return car_s

    



if __name__ == '__main__':
    n = int(input('Enter number of cars'))
    m = int(input('Enter number of cities'))
    city_list = list()
    car_list = list()
    dist_matrix = [[None]*(m)]*m

    for i in range(m):
        for j in range(i,m):
            if i == j:
                dist_matrix[i][j] = 0
                dist_matrix[j][i] = 0
            else:
                dist_matrix[i][j] = float(input('enter distance between city '+str(i)+' and '+str(j)+' : '))
                dist_matrix[j][i] = dist_matrix[i][j]
    for i in range(m):
        v = city(i,dist_matrix[i])
        city_list.append(v)
    for i in range(n):
        sr = int(input('enter the source city of car number '+str(i)))
        de = int(input('enter the destination city of car number '+ str(i)))
        b = float(input('enter the initial charge'))
        d = float(input('enter the discharge rate'))
        max_b = float(input('enter the maximum charge capacity'))
        crg_r = float(input('enter the charge rate of the car'))
        avg_s = float(input('enter the average speed of the car'))
        car_s = car(city_list[sr],city_list[de],b,d,max_b,avg_s,crg_r)
        car_list.append(car_s)
    for i in range(len(car_list)):
        car_list[i] = path_plot(car_list[i],city_list)

    print('The following are the paths of each car')
    for i in range(len(car_list)):
        print(i,':',car_list[i].path)
        







    
    
    


    
    


