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
      print(f"\n\nExact approach:\nFound solution: {model.lb} s",
            f"\nOptimal solution reached" if model.gap == 0.0 else f"\nGAP from optimal solution: {model.gap} %",
            f"\nRuntime: {model.time:.2f} s")
 
      model.solve_matheuristic(env)
      print(f"\n\nMatheuristic:\nFound solution: {model.ub} s",
            f"\nOptimal solution reached" if model.ub-model.lb == 0.0 else f"\nGAP from optimal solution: {round((model.ub-model.lb)/model.lb*100, 2)} %",
            f"\nRuntime: {model.time:.2f} s")

      print("\n\n=====================================")
