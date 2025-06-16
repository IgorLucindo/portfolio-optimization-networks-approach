import gurobipy as gp
from gurobipy import GRB
from datetime import datetime
import math
import time
import os


def solve_max_return(G, cliques, instance, config, flags, delta=0.65, callback=0):
    """
    Solve for maximum mean return, different methods depending on config
    """
    if config['iterative_warmstart']:
        return _solve_iterative(G, cliques, instance, config, flags, delta, callback)
    else:
        return _solve(G, cliques, instance, config, flags, delta, callback)


def _solve(G, cliques, instance, config, flags, delta, callback, numOfselectedAssets=0, solution=None):
    """
    Solve for maximum mean return
    """
    # Unpack instance data
    (assets, daily_returns, min_daily_return, mean_return,
     correlation_matrix, sigma, asset_pairs, total_days) = instance
    
    R_var = config['R_var']
    gamma = config['gamma']
    V = G.nodes
    T_range = range(total_days)

    # Precompute which assets meet return threshold on each day
    S = {t: [i for i in V if daily_returns[t, i] >= R_var] for t in T_range}


    # Create model
    model = gp.Model("Max_Return")
    model.setParam('TimeLimit', config['time_limit'])
    model.setParam(GRB.Param.LazyConstraints, callback >= 1)
    _save_log(model, flags['save_log'])


    # Add decision variables
    x = model.addVars(V, vtype=GRB.CONTINUOUS, name="x")
    y = model.addVars(V, vtype=GRB.BINARY, name="y")
    z = model.addVars(T_range, vtype=GRB.BINARY, name="z")

    # Set starting values
    if solution:
        _weights, _selected_indices, _objVal, _ = solution
        for i in _selected_indices:
            x[i].Start = _weights[i]
            y[i].Start = 1


    # Set objective function
    obj_fn = gp.quicksum(mean_return[i] * x[i] for i in V)
    model.setObjective(obj_fn, GRB.MAXIMIZE)


    # Fixing
    # Fix dates that weighted return cannot surpass R_var
    for t in T_range:
        if max(daily_returns[t]) < R_var:
            z[t].lb = 1


    # Add constraints
    if not callback:
        model.addConstrs(
            (gp.quicksum(daily_returns[t, i] * x[i] for i in V) >= R_var - (R_var - min_daily_return[t]) * z[t]
            for t in T_range),
            name="c1"
        )

    if config['delta_constr'] == 'inequality':
        model.addConstr(gp.quicksum(z[t] for t in T_range) / total_days <= delta, name="c2")
    elif config['delta_constr'] == 'equality':
        model.addConstr(gp.quicksum(z[t] for t in T_range) == math.floor(delta * total_days), name="c2")

    model.addConstr(gp.quicksum(x[i] for i in V) == 1, name="c3")

    if config['dist_constr'] == 'clique':
        model.addConstrs((gp.quicksum(y[i] for i in c) <= 1 for c in cliques))
    elif config['dist_constr'] == 'star':
        model.addConstrs((y[i] + gp.quicksum(y[j] for j in G.neighbors(i)) <= 1 for i in V))


    model.addConstrs((gamma * y[i] <= x[i] for i in V), name="c5")
    model.addConstrs((x[i] <= y[i] for i in V), name="c6")

    if config['valid_day_constr'] == 'upfront':
        model.addConstrs((gp.quicksum(y[i] for i in S[t]) >= 1 - z[t] for t in T_range), name="c7")

    if numOfselectedAssets:
        model.addConstr(gp.quicksum(y[i] for i in V) == numOfselectedAssets, name="c8")


    # Define callback functions
    def lazy_callback1(model, where):
        if where != GRB.Callback.MIPSOL: return
        
        x_ = model.cbGetSolution(x)
        z_ = model.cbGetSolution(z)

        for t in T_range:
            if z_[t] > 0.5 or sum(daily_returns[t, i] * x_[i] for i in V) >= R_var:
                continue
            model.cbLazy(gp.quicksum(daily_returns[t, i] * x[i] for i in V) >= R_var - (R_var - min_daily_return[t]) * z[t])
            if config['valid_day_constr'] == 'callback':
                model.cbLazy(gp.quicksum(y[i] for i in S[t]) >= 1 - z[t])

    def lazy_callback2(model, where):
        if where != GRB.Callback.MIPSOL: return

        x_ = model.cbGetSolution(x)
        y_ = model.cbGetSolution(y)
        z_ = model.cbGetSolution(z)

        S_sel = [i for i in V if y_[i] > 0.5]
        S_not_sel = [i for i in V if y_[i] <= 0.5]

        for t in T_range:
            if z_[t] > 0.5 or sum(daily_returns[t, i] * x_[i] for i in V) >= R_var:
                continue
            if max([daily_returns[t, i] for i in S_sel]) < R_var:
                model.cbLazy(gp.quicksum(y[i] for i in S_not_sel) >= 1 - z[t])
            else:
                model.cbLazy(gp.quicksum(daily_returns[t, i] * x[i] for i in V) >=
                             R_var - (R_var - min_daily_return[t]) * z[t])
    
    # Solve
    match callback:
        case 0:
            model.optimize()
        case 1:
            model.optimize(lazy_callback1)
        case 2:
            model.optimize(lazy_callback2)

    # Return no solution if model is infeasible or if timed out
    if model.status in [3, 4, 9]:
        status = "Infeasible" if model.status in [3, 4] else "Timed out"
        return {}, status, model.ObjVal, model.ObjBound

    weights = {i: x[i].X for i in V}
    selected_indices = [i for i in V if y[i].X > 0.5]
    return weights, selected_indices, model.ObjVal, None


def _solve_unconstrained(V, instance, delta, R_var):
    """
    Solve maximum mean return
    """
    (assets, daily_returns, min_daily_return, mean_return,
     correlation_matrix, sigma, asset_pairs, total_days) = instance
    T_range = range(total_days)

    # Create model
    model = gp.Model("Max_Return")

    # Suppress output
    model.setParam("OutputFlag", 0)

    # Add decision variables
    x = model.addVars(V, vtype=GRB.CONTINUOUS, lb=0, name="x")
    # z = model.addVars(T_range, vtype=GRB.BINARY, name="z")
    z = model.addVars(T_range, vtype=GRB.CONTINUOUS, ub=1, name="z")

    # Fixing
    # Fix dates that weighted return cannot surpass R_var
    for t in T_range:
        if max(daily_returns[t]) < R_var:
            z[t].lb = 1

    # Add constraints
    model.addConstrs(
        (gp.quicksum(daily_returns[t, i] * x[i] for i in V) >= R_var - (R_var - min_daily_return[t]) * z[t]
         for t in T_range),
        name="c1"
    )
    model.addConstr(gp.quicksum(z[t] for t in T_range) / total_days <= delta, name="c2")
    model.addConstr(gp.quicksum(x[i] for i in V) == 1, name="c3")
    
    # Solve for different dates
    solutions = []
    for tau in T_range:
        # Set objective function
        obj_fn = gp.quicksum(daily_returns[tau, i] * x[i] for i in V)
        model.setObjective(obj_fn, GRB.MAXIMIZE)

        # Solve
        model.optimize()

        solutions.append([model.ObjVal, [z[t].X for t in T_range]])
    
    return solutions


def _solve_iterative(G, cliques, instance, config, flags, delta, callback):
    """
    Solve the asset allocation problem using an iterative warm-start strategy
    """
    solution = None
    timestamps = []
    for k in range(1, 3):
        start_time = time.time()
        solution = _solve(G, cliques, instance, config, flags, delta, callback, k, solution)
        timestamps.append(time.time() - start_time)
    print(timestamps)

    return _solve(G, cliques, instance, config, flags, delta, callback, solution=solution)


def _save_log(model, save_flag):
    """
    Save logfile of gurobi formulation for debbuging
    """
    if not save_flag:
        # Disable all output
        model.setParam('OutputFlag', 0)
        return

    folder_path = "application/logfiles"
    date = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Create logfiles folder
    os.makedirs(folder_path, exist_ok=True)
    
    # Save logfile
    model.setParam("LogFile", folder_path + f"/gurobi_log_{date}.txt")