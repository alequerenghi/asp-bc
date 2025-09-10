from aspbc import ASPBC
import gurobipy as gb
import os

# model = ASPBC.create_from_file(
#     "dataset/ASP-BC Instances/Ins_V5_J50_T10_R60_B10_W1_S129_N9.txt")
# model.solve_matheuristic()
# print(f"\nMatheuristic:\nLower bound: {model.lb}, Time step 1: {model.time_1}, Initial Upper bound: {model.initial_ub}, Initial GAP: {round((model.initial_ub-model.lb)/model.lb * 100, 2)}, Time step 2: {model.time_2}, Upper Bound: {model.ub}, GAP: {round((model.ub-model.lb)/model.lb*100, 2)}, Time step 3: {model.time_3}, Total time: {model.time_1 + model.time_2 + model.time_3}")
folder = "dataset/ASP-BC Instances"


with gb.Env() as env_model:
    env_model.setParam("OutputFlag", 0)
    env_model.setParam("ConcurrentMIP", 3)
    env_model.setParam("TimeLimit", 1800)
    with gb.Env() as env_ma:
        env_ma.setParam("OutputFlag", 0)
        env_ma.setParam("ConcurrentMIP", 3)
        env_ma.setParam("TimeLimit", 720)
        files = [f for f in os.listdir(folder) if "J50" in f and "W1" in f]
        for file in files[0:20]:
            path = os.path.join(folder, file)
            model = ASPBC.create_from_file(path)
            print(
                f"Instance {file} with {model.M} AGVs and {model.e.shape[0]} jobs")
            model.solve(env_model)
            print(
                f"\n\nModel:\nLower bound: {model.aspbc.ObjVal}, Upper bound: {model.aspbc.ObjBound}, GAP: {model.aspbc.MIPGap}, Runtime: {model.aspbc.Runtime:.2f}")
            model.solve_matheuristic(env_ma)
            print(
                f"\nMatheuristic:\nLower bound: {model.lb}, Time step 1: {model.time_1:.2f}, Initial Upper bound: {model.initial_ub}, Initial GAP: {round((model.initial_ub-model.lb)/model.lb * 100, 2)}, Time step 2: {model.time_2:.2f}, Upper Bound: {model.ub}, GAP: {round((model.ub-model.lb)/model.lb*100, 2)}, Time step 3: {model.time_3:.2f}, Total time: {model.time_1 + model.time_2 + model.time_3:.2f}")
            print(
                "\n\n=====================================\n\n")
