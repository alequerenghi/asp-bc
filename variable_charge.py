

import os
from gurobipy import GRB
import scipy.sparse as sp
import numpy as np
import gurobipy as gb
from gurobipy import quicksum
from numpy.typing import NDArray
from parser import parse_file
import csv


class ASPBC:
    def __init__(self, agv_number: int, job_durations: NDArray[np.int64],
                 battery_capacity: float, charge_duration: float, energy_requirements: NDArray[np.float64],
                 charging_operations_number=0
                 ) -> None:
        self.M = agv_number
        self.d = job_durations
        self.b = battery_capacity
        self.t = charge_duration
        self.e = energy_requirements
        self.R = energy_requirements.shape[0] if charging_operations_number == 0 else charging_operations_number

    def solve(self, tau: float, env=None):
        J = self.e.shape[0]

        model = gb.Model("ASP-BC-v", env=env)
        x = model.addVars([(j, m) for j in range(J)
                          for m in range(self.M)], vtype=GRB.BINARY, name="x")
        q = model.addVars([(r, m) for r in range(self.R)
                          for m in range(self.M)], vtype=GRB.BINARY, name="q")
        y = model.addVars([(j, r, m) for j in range(J) for r in range(
            self.R) for m in range(self.M)], vtype=GRB.BINARY, name="y")
        cmax = model.addVar()

        # m.addConstr(cmax >= computation_times @ x + tau * ((energy_consumptions @ y)[-1:] * q[1:]).sum(axis=0))

        # r = 0..R-2, j = 0..J-1, m = 0..M-1
        w = model.addVars(self.R-1, J, self.M, vtype=GRB.BINARY, name="w")

        model.setObjective(cmax, GRB.MINIMIZE)

        # w <= y[:R-1]
        model.addConstrs(
            (w[r, j, m] <= y[r, j, m] for r in range(self.R-1)
             for j in range(J) for m in range(self.M))
        )

        # w <= q[1:, None, :]
        model.addConstrs(
            (w[r, j, m] <= q[r+1, m] for r in range(self.R-1)
             for j in range(J) for m in range(self.M))
        )

        # w >= y[:R-1] + q[1:, None, :] -1
        model.addConstrs(
            (w[r, j, m] >= y[r, j, m] + q[r+1, m] - 1
             for r in range(self.R-1) for j in range(J) for m in range(self.M))
        )

        # cmax >= d @ x + tau*(e @ w).sum(axis=0)
        model.addConstrs(cmax >= quicksum(self.d[j] * x[j, m] for j in range(J)) + tau * quicksum(
            self.e[j] * w[r, j, m]for r in range(self.R-1) for j in range(J)) for m in range(self.M))

        model.addConstrs(quicksum(x[j, m] for m in range(self.M)) == 1
                         for j in range(J)
                         )
        model.addConstrs(quicksum(y[r, j, m] for r in range(self.R)) == x[j, m]
                         for j in range(J)
                         for m in range(self.M)
                         )
        model.addConstrs(2 * y[r, j, m] <= x[j, m] + q[r, m]
                         for j in range(J)
                         for r in range(self.R)
                         for m in range(self.M)
                         )
        model.addConstrs(quicksum(self.e[j] * y[r, j, m] for j in range(J)) <= self.b
                         for r in range(self.R)
                         for m in range(self.M)
                         )
        model.addConstrs(q[r, m] <= q[r-1, m]
                         for r in range(1, self.R)
                         for m in range(self.M)
                         )
        model.addConstrs(q[0, m] == 1
                         for m in range(self.M)
                         )
        model.optimize()

        self.aspbc = model

        return self

    @classmethod
    def create_from_file(cls, file_name: str) -> "ASPBC":
        return cls(*parse_file(
            file_name))


if __name__ == "__main__":
    m = ASPBC.create_from_file(
        "dataset/ASP-BC Instances/Ins_V2_J50_T10_R60_B10_W1_S90_N0.txt")
    m.solve(1.0)
    for v in m.aspbc.getVars():
        if "x" in v.VarName:
            print(f"{v.VarName} = {v.X}")
    print(f"Objective: {m.aspbc.ObjVal}")
