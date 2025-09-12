from aspbc import ASPBC
import gurobipy as gb
import os

folder = "dataset/ASP-BC Instances"
env = gb.Env()

env.setParam("OutputFlag", 0) # disattiva output gurobi
env.setParam("ConcurrentMIP", 3)

# test su istanze con 50 jobs a peso medio 1
files = [f for f in os.listdir(folder) if "J50" in f and "W1" in f]
# solo le prime 20 istanze
for file in files[0:20]:
      path = os.path.join(folder, file)
      model = ASPBC.create_from_file(path)

      print(f"\n\nInstance {file} with {model.M} AGVs and {model.e.shape[0]} jobs")
      
      model.solve(env)
      print(f"\n\nExact approach:\nBest solution: {model.aspbc.ObjVal}",
            f"\nOptimal solution reached" if model.aspbc.MIPGap == 0.0 else f"GAP from optimal solution: {model.aspbc.MIPGap}",
            f"\nRuntime: {model.aspbc.Runtime:.2f} seconds")
 
      model.solve_matheuristic(env)
      print(f"\n\nMatheuristic:\nLower bound: {model.lb}, "
            f"Time step 1: {model.time_1:.2f}, "
            f"Initial Upper bound: {model.initial_ub}, "
            f"Initial GAP: {round((model.initial_ub-model.lb)/model.lb * 100, 2)}, "
            f"Time step 2: {model.time_2:.2f}, Upper Bound: {model.ub}, "
            f"GAP: {round((model.ub-model.lb)/model.lb*100, 2)}, "
            f"Time step 3: {model.time_3:.2f}, "
            f"Total time: {model.time_1 + model.time_2 + model.time_3:.2f}")

      print("\n\n=====================================")
