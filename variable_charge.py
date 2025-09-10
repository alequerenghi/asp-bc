

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
        x = model.addMVar((J, self.M), vtype=GRB.BINARY)
        q = model.addMVar((self.R, self.M), vtype=GRB.BINARY)
        y = model.addMVar((J, self.R, self.M), vtype=GRB.BINARY)
        w = model.addMVar((J, self.R-1, self.M), vtype=GRB.BINARY)
        cmax = model.addVar()

        model.setObjective(cmax, GRB.MINIMIZE)

        model.addConstr(w <= y[:, :-1])
        model.addConstr(w <= q[None, 1:, :])
        model.addConstr(w >= y[:, :-1] + q[None, 1:, :]-1)
        model.addConstr(cmax >= self.d @ x + tau * (self.e @ w.sum(axis=1)))
        model.addConstr(x @ np.ones(self.M) == 1)
        model.addConstr(y.sum(axis=1) == x)
        model.addConstr(2 * y <= x[:, None, :] + q[None, :, :])
        model.addConstr((self.e[None, :, None] * y).sum(axis=0) <= self.b)
        model.addConstr(q[1:] <= q[:-1])
        model.addConstr(q[0] == 1)
        model.optimize()

        self.aspbc = model

        return self

    @classmethod
    def create_from_file(cls, file_name: str) -> "ASPBC":
        return cls(*parse_file(
            file_name))


if __name__ == "__main__":
    with gb.Env() as env:
        env.setParam("ConcurrentMIP", 3)
        m = ASPBC.create_from_file(
            "dataset/ASP-BC Instances/Ins_V2_J50_T10_R60_B10_W1_S90_N0.txt")
        m.solve(1.0, env)
