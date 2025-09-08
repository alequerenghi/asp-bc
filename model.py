import numpy as np
import os
from numpy.typing import NDArray
import gurobipy as gb
from gurobipy import GRB, quicksum
from parser import parse_file
from csv import writer


class ASPBC:
    def __init__(self, job_number: int, agv_number: int, job_durations: NDArray[np.int64],
                 battery_capacity: float, charge_duration: float, energy_requirements: NDArray[np.float64],
                 charging_operations_number: int = 0
                 ) -> None:
        self.J = job_number
        self.M = agv_number
        self.d = job_durations
        self.b = battery_capacity
        self.t = charge_duration
        self.e = energy_requirements
        self.R = self.J if charging_operations_number == 0 else charging_operations_number

    def solve(self, env=None) -> "ASPBC":
        aspbc = gb.Model("ASP-BC", env=env)

        x = aspbc.addVars([(j, m) for j in range(self.J)
                          for m in range(self.M)], vtype=GRB.BINARY)
        q = aspbc.addVars([(r, m) for r in range(self.R)
                          for m in range(self.M)], vtype=GRB.BINARY)
        y = aspbc.addVars([(j, r, m) for j in range(self.J) for r in range(
            self.R) for m in range(self.M)], vtype=GRB.BINARY)

        cmax = aspbc.addVar(vtype=GRB.CONTINUOUS, lb=0.0)

        aspbc.setObjective(cmax, GRB.MINIMIZE)

        aspbc.addConstrs(cmax >= quicksum(self.d[j] * x[j, m] for j in range(self.J)) + quicksum(self.t * q[r, m] for r in range(1, self.R))
                         for m in range(self.M)
                         )
        aspbc.addConstrs(quicksum(x[j, m] for m in range(self.M)) == 1
                         for j in range(self.J)
                         )
        aspbc.addConstrs(quicksum(y[j, r, m] for r in range(self.R)) == x[j, m]
                         for j in range(self.J)
                         for m in range(self.M)
                         )
        aspbc.addConstrs(2 * y[j, r, m] <= x[j, m] + q[r, m]
                         for j in range(self.J)
                         for r in range(self.R)
                         for m in range(self.M)
                         )
        aspbc.addConstrs(quicksum(self.e[j] * y[j, r, m] for j in range(self.J)) <= self.b
                         for r in range(self.R)
                         for m in range(self.M)
                         )
        aspbc.addConstrs(q[r, m] <= q[r-1, m]
                         for r in range(1, self.R)
                         for m in range(self.M)
                         )
        aspbc.addConstrs(q[0, m] == 1
                         for m in range(self.M)
                         )
        aspbc.optimize()

        self.aspbc = aspbc

        return self

    @classmethod
    def create_from_file(cls, file_name: str) -> "ASPBC":
        return cls(*parse_file(
            file_name))


def read_and_solve(folder) -> None:
    with open("output.csv", "wt") as output_file:
        csv_writer = writer(output_file)
        csv_writer.writerow(["Name", "Machines", "Jobs",
                            "Lower bound", "Upper bound", "Gap", "Time"])
        with gb.Env() as env:
            env.setParam("OutputFlag", 0)
            env.setParam("ConcurrentMIP", 3)
            env.setParam("TimeLimit", 1800)
            for fname in os.listdir(folder):
                if fname.endswith(".txt"):
                    path = os.path.join(folder, fname)
                    model = ASPBC.create_from_file(path)
                    model.solve(env)
                    csv_writer.writerow(
                        [fname, model.M, model.J, model.aspbc.ObjVal, model.aspbc.ObjBound, model.aspbc.MIPGap, model.aspbc.Runtime])


if __name__ == "__main__":
    read_and_solve("dataset/ASP-BC Instances")
