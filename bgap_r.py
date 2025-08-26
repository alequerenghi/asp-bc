import gurobipy as gp
from gurobipy import GRB
import numpy as np
from bpp import BinPackingProblem
from numpy.typing import NDArray


class BGAPChargeOperations:
    def __init__(self, M: int, energy_requirements: np.ndarray, processing_times: np.ndarray, battery_capacity: float, gamma: NDArray[np.bool], chi: NDArray[np.bool], charge_duration: float, J: int = 0) -> None:
        self.M = M
        self.e = energy_requirements
        self.d = processing_times
        self.b = battery_capacity
        self.gamma = gamma
        self.chi = chi
        self.t = charge_duration
        self.J = energy_requirements.shape[0] if J == 0 else J
        self.R = self.J

    @classmethod
    def from_bpp(cls, bpp: BinPackingProblem, M: int, processing_times: np.ndarray, charge_duration: float) -> 'BGAPChargeOperations':
        gamma = _array_from_var(bpp.gamma)
        chi = _array_from_var(bpp.chi)
        bgap_r = cls(M, bpp.e, processing_times, bpp.b,
                     gamma, chi, charge_duration, bpp.J)
        return bgap_r

    def solve(self) -> 'BGAPChargeOperations':
        m = gp.Model("bgap_r")

        R_bar = np.where(self.gamma == 1)[0]
        D = (self.chi @ self.d)[R_bar]

        # VARIABLES!!!!
        theta = m.addMVar(shape=(R_bar.shape[0], self.M), vtype=GRB.BINARY)
        cmax = m.addVar()

        # OBJECTIVE!!!
        m.setObjective(cmax, GRB.MINIMIZE)

        # CONSTRAINTS!!!
        m.addConstr(cmax >= (theta @ D)-self.t)
        # uguale a m.addConstr(theta.sum(axis=1) == 1)
        m.addConstr(theta @ np.ones(self.M) == 1)

        m.setParam('OutputFlag', 0)
        m.optimize()

        self.theta = np.zeros((self.R, self.M), dtype=np.bool)
        self.theta[R_bar] = _array_from_var(theta)
        # np.add.at(self.theta, R_bar, _array_from_var(theta))
        self.z = m.ObjVal

        return self


def _array_from_var(var: gp.MVar) -> NDArray[np.bool]:
    return np.array(var.X, dtype=np.bool)
