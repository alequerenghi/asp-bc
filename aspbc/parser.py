import os
import re
import numpy as np
from numpy.typing import NDArray


def parse_file(filepath) -> tuple[int, NDArray[np.int64], float, float, NDArray[np.float64]]:
    with open(filepath, "r") as f:
        instance = f.read()

    agv_number = int(re.search(r"N_MACHINES:(\d+)", instance).group(1))
    job_number = int(re.search(r"N_JOBS:(\d+)", instance).group(1))
    charge_duration = int(re.search(r"CHARGING_TIME:(\d+)", instance).group(1))
    battery_capacity = int(
        re.search(r"INITIAL_CHARGE:(\d+)", instance).group(1))

    D_block = re.search(r"D:\[(.*?)\]", instance, re.S).group(1)
    D_lines = [line.strip()
               for line in D_block.strip().splitlines() if line.strip()]
    D = [[int(x) for x in re.split(r"\s+", line)] for line in D_lines]

    W_block = re.search(r"w:\[(.*?)\]", instance, re.S).group(1)
    W_lines = [line.strip()
               for line in W_block.strip().splitlines() if line.strip()]
    W = [[float(x) for x in re.split(r"\s+", line)] for line in W_lines]

    job_durations = np.array(D, dtype=np.int64)[:, 0]
    energy_requirements = np.array(W, dtype=np.float64)[:, 0]

    assert len(
        job_durations) == job_number, f"Mismatch: expected {job_number} jobs, got {len(job_durations)}"
    assert len(
        energy_requirements) == job_number, f"Mismatch: expected {job_number} jobs, got {len(energy_requirements)}"

    return (agv_number, job_durations, battery_capacity, charge_duration, energy_requirements)


if __name__ == "__main__":
    parse_file("dataset/ASP-BC Instances/Ins_V10_J200_T30_R60_B10_W2_S357_N7.txt")
