import os
import csv
from aspbc import ASPBC
from gurobipy import Env

FOLDER = "dataset/ASP-BC Instances"
        
def compute_outcomes(euristic = False):
    env = Env()
    env.setParam("OutputFlag", 0) # disattiva output gurobi
    env.setParam("ConcurrentMIP", 3)

    FILE_NAME = 'MILP.csv' if not euristic else '3S-MHA.csv'
    files = os.listdir(FOLDER)

    if not euristic:
        files = [f for f in files if "J200" not in f]
        env.setParam("TimeLimit", 600)
    else:
        env.setParam("TimeLimit", 240)

    with open(FILE_NAME, 'wt') as file:
        to_write = csv.writer(file)
        to_write.writerow(['File name', 
                        'Fleet size', 
                        'Number of jobs', 
                        'Average job duration', 
                        'Average energy job costs', 
                        'Lower bound', 
                        'Upper bound', 
                        'GAP (%)', 
                        'Runtime'])
        for file in files:
            path = os.path.join(FOLDER, file)
            model = ASPBC.create_from_file(path)
            if euristic: 
                model.solve_matheuristic(env)
            else:
                model.solve(env)
            to_write.writerow([file, 
                                f"{model.M}", 
                                f"{model.e.shape[0]}", 
                                f"{int(model.d.mean())}", 
                                f"{int(model.e.mean())}", 
                                f"{int(model.lb)}", 
                                f"{int(model.ub)}",
                                f"{model.gap * 100:.2f}",
                                f"{model.time:.2f}"])

compute_outcomes(euristic=True)   
compute_outcomes()