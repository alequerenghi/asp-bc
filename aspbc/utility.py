import gurobipy as gp
import numpy as np
from numpy.typing import NDArray

# crea un array Numpy da una variabile MVar di Gurobi
def _array_from_var(var: gp.MVar) -> NDArray[np.bool_]:
    return np.array(var.X, dtype=bool)
