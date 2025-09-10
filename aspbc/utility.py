import gurobipy as gp
import numpy as np
from numpy.typing import NDArray


def _array_from_var(var: gp.MVar) -> NDArray[np.bool_]:
    return np.array(var.X, dtype=bool)
