

from gurobipy import GRB
import scipy.sparse as sp
import numpy as np
import gurobipy as gb


def solve(R: int, J: int, M: int, computation_times: np.ndarray, e: np.ndarray, tau: float):
    model = gb.Model("ASP-BC-v")

    x = model.addMVar((J, M), vtype=GRB.BINARY)
    y = model.addMVar((R, J, M), vtype=GRB.BINARY)
    q = model.addMVar((R, M), vtype=GRB.BINARY)
    cmax = model.addVar()

    # m.addConstr(cmax >= computation_times @ x + tau * ((energy_consumptions @ y)[-1:] * q[1:]).sum(axis=0))

    # r = 0..R-2, j = 0..J-1, m = 0..M-1
    w = model.addVars(R-1, J, M, vtype=GRB.BINARY)

    model.addConstrs(
        (w[r, j, m] <= y[r, j, m] for r in range(R-1)
         for j in range(J) for m in range(M))
    )

    model.addConstrs(
        (w[r, j, m] <= q[r+1, m] for r in range(R-1)
         for j in range(J) for m in range(M))
    )

    model.addConstrs(
        (w[r, j, m] >= y[r, j, m] + q[r+1, m] - 1
         for r in range(R-1) for j in range(J) for m in range(M))
    )

    energy_term = model.addVars(M, lb=0)

    model.addConstrs(
        (energy_term[m] == sum(e[j] * w[r, j, m]
                               for r in range(R-1) for j in range(J)) for m in range(M))
    )

    jobs_term = model.addVars(M, lb=0)

    model.addConstrs(
        (jobs_term[m] == sum(computation_times[j] * x[j, m] for j in range(J))
         for m in range(M))
    )

    model.addConstrs((cmax >= jobs_term[m] + tau *
                      energy_term[m] for m in range(M)))
