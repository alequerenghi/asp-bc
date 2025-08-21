# ASP-BC
Problem of scheduling transfer jobs on the **Automated Guided Vehicles (AGVs)**.  
**AGV Scheduling Problem with Battery Constraints ASP-BC**: transfer jobs and charge operations of a fleet of homogeneous AGVs to **minimze the makespan of hte handling problem**.  

## Introduction
Used for horizontal movement of materials. AGVs are part of the **AGV system**. 
Transfer the material to the right place at the right time.  
Minimize time to supply a set of packages to a set of workstations. Each package contains all the materials of a single workstation; **packages are located at the central warehouse**; **one package on each AGV per trip**; one trip **begins and ends at the central warehouse**.  
Battery consumption depends on **travel time and weight carried**.  
Recharged fully before the battery is completely depleted with **fixed charging time**.  
Charging stations are at the central warehouse.

**Can be adapted to account for residual charge.**

In the paper:  
1. Original MILP model for ASP-BC (variant of Bottleneck Generalized Assignment Problem BGAP where a job is a round trip with two possible decision: assignment of a job and charging).
2. Three step matheuristic to solve large instances:
    * **Bin-Packing Problem BPP** to determine minimum number of battery charges required -> lower bound for ASP-BC
    * **BCAP is solved** 
    * **Local search** to improve the solution
3. Solve real instances from real data. Evidence shows that complexity stems from battery management.

The formulation allows to solve instances with up to 150 jobs and 10 AGVs outperforming previous research solutions and the matheuristic is able to solve instances with up to 200 jobs and 10 AGVs with a limited computation burden and an average optimality gap lower than 1%.

## Lieterature review

Consider standard ASPs with maintenance activities where the latter refers to charging operations.  
In **fixed problems** jobs have to be scheduled wrt planned maintenance activities (start and completion times known in advance).  
In **coordinated problems** both jobs and maintenance have to be scheduled. **Only consider coordinated problems**.  
Classified in two groups:
* Single mainenance activity must be performed regardless
* Machines cannot continuously operate longer than a pre-defined working time: **consider this case**

Notice that in ASP-BC:
* **parallel machine scheduling problem**
* **minimize the makespan** instead of the completion time.
* Battery charge activities depend not only on time but also on actual battery depletion.
* exact methods cannot be used with ASP-BC due to dimensional drawbacks. Heuristics are designed for very specific variants and cannot be adapted.
* in ASP-BC a subset of problems is assigned to a charging operation -> sequence of jobs **does not affect the amount of energy consumed or the objective function**

## AGV Scheduling Problem with Battery Constraints

### Problem description

Supply materials to workstations with AGVs.  
Minimize the time required to dispatch all materials and avoid delays.  
A single dedicated package for each workstation. **One-to-one matching between packages and workstations**.  
Packages in central warehouse.  
Homogeneous AGVs located at the central warehouse. AGVs travel at constant speed and carry one package per time (perform round-trips).  Trips are called **transfer jobs**.
Transfer jobs consider:
* **duration**: round trip travel time, loading and unloading of package
* **weight**: weight of the package carried

AGVs have limited capacity batteries. Battery level depelete in function of job duration and weight carried.  
Before total depletion perform **charging operation** at the central warehouse **fully recharging** the battery.  
**Charge time is fixed**.  
Minimze the number of charges by performing full charges. Chargin represents overhead. Charging time is fixed if the battery is almost depleted each time.  
Charge jobs are **special jobs with duration equal to charge time and null weight**.  
Determine the scheduling of transfer and charing jobs to **minimize makespan** (**maximum completion time of the last transfer job over all AGVs**).

Less charging jobs could lead to better solutions.