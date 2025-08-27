import numpy as np
from bpp import BinPackingProblem
from bgap_c import BGAPConstrained
from bgap_r import BGAPChargeOperations
from local_search import LocalSearch


class MathEuristic:
    def __init__(self, M: int, energy_requirements: np.ndarray, computation_times: np.ndarray, battery_capacity: float, charge_time: float) -> None:
        self.M = M
        self.e = energy_requirements
        self.d = computation_times
        self.b = battery_capacity
        self.t = charge_time

    def solve(self):
        bpp = BinPackingProblem(self.e, self.b)
        bpp.solve()
        self._bpp_lb = bpp.get_lower_bound(self.M, self.t, self.d)
        ls = None
        if bpp.zeta <= self.M:
            bgap = BGAPConstrained(self.M, self.e, self.d, self.b)
            bgap.solve()
            ls = LocalSearch.from_constrained(bgap, self.t)
        else:
            bgap = BGAPChargeOperations.from_bpp(bpp, self.M, self.d, self.t)
            bgap.solve()
            ls = LocalSearch.from_charge(bgap)
        ls.solve()
        self.ls = ls
        return self


processing_times = np.array([1, 2, 3, 4])
energy_requirements = np.array([6, 3, 1, 6])
charge_time = 2
battery_capacity = 11

me = MathEuristic(2, energy_requirements, processing_times,
                  battery_capacity, charge_time)
me.solve()
print(me.ls.x)
print(me.ls.y)
print(me.ls.cmax)
