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

### Problem formulation

Based on BGAP and named **A-BGAP**.
+ n items (jobs)
+ m units (AGV charging opeartions)
+ $p_{ij}$ penalty (sum of the duration of the transfer and charge jobs)
+ $q_{ij}$ resource requirement (energy consumption of a transfer job)

(assignment of item j to unit i). BGAP assigns each item to one unit to minimize penalty and avoid exceeding resource requirement thresholds.

ASP-BC requires a double level of assignment:
1. **transfer jobs are assigned to charging operations**
2. charging operations and transfer jobs are **assigned to AGVs**

Let:
+ $J$ be the transfer job with $j\in J$ with $e_j$ the **energy cost** and **processing time** $d_j$.
+ $M$ the AGVs and $m\in M$ with battery capacity $b$.
+ $n$ the number of charge operations and $R=\{1,\dots,n\}$ the **charging operations**. Worst case: charge after each job ($n=|J|$).
+ $t$ charge operation duration (all AGVs start with full battery)

Decision variables:
- $x_j^m\in\{0,1\}$: 1 if transfer job $j$ is preformed by AGV $m$ and 0 otherwise
- $q_r^m\in\{0,1\}$: 1 if charging job $r$ is preformed by AGV $m$ and 0 otherwise
- $y_{jr}^m\in\{0,1\}$: 1 if transfer job $j$ is preformed by AGV $m$ after charging job $r$ and before the next one
- $C_\text{max}\in\mathbb{Z}^+$ completion time of the transfer process.

Formulation:
$$z=\min C_\text{max}$$
$C_\text{max}\geq\sum_{j\in J}d_jx_j^m+\sum_{r\in R\backslash\{1\}}tq_r^m \qquad\forall m\in M$  
Ensure consistency between the duration of the transfer job and makespan

$\sum_{m\in M}x_j^m=1\qquad \forall j\in J$  
Each transfer job must be assigned toa single AGV

$\sum_{r\in R}y_{jr}^m=x_j^m\qquad \forall j\in J, m\in M$  
Require to have at least a charge job r before job j

$2y_{jr}^m\leq x_j^m+q_r^m\qquad \forall j\in J, m\in M, r\in R$  
Upper bounds on y

$\sum_{j\in J}e_jy_{jr}^m\leq b\qquad \forall m\in M, r\in R$  
Battery capacity constraints for each charging job

$q_r^m\leq q_{r-1}^m\qquad \forall m\in M,r\in R\backslash\{1\}$  
Symmetry breaking constraints

$q_1^m=1\qquad \forall m\in M$
Charge job on each AGV at start

$$x_j^m\in\{0,1\}\qquad\forall m\in M,j\in J$$
$$q_r^m\in\{0,1\}\qquad\forall m\in M,r\in R\backslash\{1\}$$
$$y_{jr}^m\in\{0,1\}\qquad\forall m\in M,j\in J,r\in R$$
$$C_\text{max}\in\mathbb{R}^+$$

Consider residual energy in charging time wrt $\tau$ the charging time per energy unit:
$C_\text{max}\geq \sum_{j\in J}d_jx_j^m+\tau\sum_{j\in J}\sum_{r\in R\backslash\{n\}}e_jy_{jr}^mq_{r+1}^m\qquad \forall m\in M$  
The first term is transfer time and the second represent the time of charging operations depending on residual energy.  
This changes the first constraint

**DA LINEARIZZARE**

## Matheuristic for the ASP-BC

### Transfer job-charging operation assignment

Assignment of the transfer jobs to the charging operations from the solution of **Bin Packing Problem BPP**:
- bins are charging operations: $\gamma_r$ are binary variables equal to 1 if the $r$-th charging operations is performed
- items are transfer jobs: $\chi_{rj}$ binary variables equal to 1 if the transfer job $j$ is assigned to the $r$-th charging operation:

$\zeta=\min\sum_{r\in R}\gamma_r$  
Minimize the number of charging operations

$\sum_{r\in R}\chi_{rj}=1\qquad \forall j\in J$  
Each job assigned to a charging operation

$\sum_{j\in J}e_j\chi_{rj}\leq b\gamma_r\qquad \forall r\in R$  
If a charge operation is used, then the sum of the energy consumption of the jobs assigned is lower than the battery capacity

$\gamma_r\leq\gamma_{r-1}\qquad\forall r\in R$  
Symmetry breaking constraints

$\chi_{rj}\in\{0,1\}\qquad\forall r\in R$  
$\gamma_r\in\{0,1\}\qquad\forall r\in R$

Let $\bar \zeta$ be the optimum, then the solution is $\max(0,\bar \zeta-|M|)$ is the minimal number of required charges (all AGVs are charged at the beginning).  
A **valid lower bound** is:
$$LB=\max\left\{\left\lceil\frac{(\max(0,\bar\zeta-|M|))*t+\sum_{j\in J}d_j}{|M|}\right\rceil,\left\lceil\frac{(\max(0,\bar\zeta-|M|))}{|M|}\right\rceil*t\right\}$$
The numerator of the first term is the **minimum total time required by all AGVs to perform all the charging and transfer operations**. The second term takes into accuont the indivisibility of the charging operations.  

**The solution does not necessarily use the lowest number of charges**.

### 4.2. Charging operation-AGV assignment

Find a feasible solution for the ASP-BC.  
If $\bar\zeta\leq|M|$ then a **feasible solution without charging operations exists**.  
Otherwise if $\bar\zeta>|M|$ intermediate charging operations are required.

#### 4.2.1. Solution without charging operations

Solve a BGAP with resource Constraints (BGAP-C)

$$z=\min C_\text{max}$$
$C_\text{max}\geq\sum_{j\in J}d_jx_j^m\qquad\forall m\in M$  

$\sum_{m\in M}x_j^m=1\qquad \forall j\in J$  

$\sum_{j\in J}e_jx_{j}^m\leq b\qquad \forall m\in M$  

$x_j^m\in\{0,1\}\qquad\forall m\in M,j\in J$
$C_\text{max}\in\mathbb{R}^+$

This situation arises when the **number of jobs is relatively small** compared to the number of AGVs or the **job energy consumption are low** wrt battery capacity.

#### ASP-BC solution with charging operations

Use the BPP solution to solve a BGAP-R where:
- items are charging operations containing transfer jobs
- AGVs are bings

Let $\bar R$ be the smallest subset of charging jobs in a feasible solution ($\bar R=\{r\in R:\bar\gamma_r=1\}$). Each charging job $\bar r$ has duration $D_{\bar r}$ given by the total processing time of all the jobs assigned to that charging opeartion and the charging time $D_{\bar r}=(\sum_{j\in J}d_j\bar\chi_{\bar rj})+t$.  Solve the BGAP-R to determine a feasible solution of ASP-BC:

$$z=\min C_\text{max}$$
$C_\text{max}\geq\left(\sum_{\bar r\in\bar R}D_{\bar r}\theta_{\bar rm}\right)-t\qquad\forall m\in M$  
Subtraction due to initial battery charge

$\sum_{m\in M}\theta_{\bar rm}=1\qquad \forall \bar r\in\bar R$  
All bins are assigned to an AGV

$\theta_{\bar rm}\in\{0,1\}\qquad\forall \bar r, m\in M$  
Equal to 1 if the charging operation is asssigned to m
$C_\text{max}\in\mathbb{R}^+$

