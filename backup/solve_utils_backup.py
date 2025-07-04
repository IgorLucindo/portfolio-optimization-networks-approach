from classes.Timer import *
import gurobipy as gp
from gurobipy import GRB
from datetime import datetime
import numpy as np
import math
import os


def solve_max_return(G, cliques, instance, config, flags, delta=0.65, callback=0):
    """
    Solve for maximum mean return, different methods depending on config
    """
    if config['iterative_warmstart']:
        return _solve_iterative(G, cliques, instance, config, flags, delta, callback)
    else:
        return _solve(G, cliques, instance, config, flags, delta, callback)


def _solve(G, cliques, instance, config, flags, delta, callback, numOfselectedAssets=0, solution={}):
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


    # Set objective function
    obj_fn = gp.quicksum(mean_return[i] * x[i] for i in V)
    model.setObjective(obj_fn, GRB.MAXIMIZE)


    # Set warmstart
    if 'x' in solution:
        for i in solution['selected_idx']:
            x[i].Start = solution['x'][i]
            y[i].Start = 1
        model.addConstr(obj_fn >= solution['obj_val'])
        model.setParam(GRB.Param.BestBdStop, solution['obj_val']-1e-6)


    # Fixing
    # Fix dates that weighted return cannot surpass R_var
    for t in T_range:
        if max(daily_returns[t]) < R_var:
            z[t].lb = 1

    # Add constraints
    # c1: Enforce minimum daily portfolio return, less strict on "bad days" (z[t]=1), if not using callbacks.
    if not callback:
        model.addConstrs(
            (gp.quicksum(daily_returns[t, i] * x[i] for i in V) >= R_var - (R_var - min_daily_return[t]) * z[t]
            for t in T_range),
            name="c1"
        )
    # c2: Limit the proportion or count of "bad days" (days where portfolio return is below R_var).
    if config['delta_constr'] == 'inequality':
        model.addConstr(gp.quicksum(z[t] for t in T_range) / total_days <= delta, name="c2")
    elif config['delta_constr'] == 'equality':
        model.addConstr(gp.quicksum(z[t] for t in T_range) == math.floor(delta * total_days), name="c2")
    # c3: Ensure the sum of all asset weights in the portfolio equals 1.
    model.addConstr(gp.quicksum(x[i] for i in V) == 1, name="c3")
    # Asset diversification: Prevent selecting highly correlated assets based on graph structure (G is G2 from main).
    if config['dist_constr'] == 'clique':
        # Allow at most one asset from any maximal clique in the power graph G2.
        model.addConstrs((gp.quicksum(y[i] for i in c) <= 1 for c in cliques))
    elif config['dist_constr'] == 'star':
        # If asset 'i' is selected, none of its neighbors in power graph G2 can be selected (independent set).
        model.addConstrs((y[i] + gp.quicksum(y[j] for j in G.neighbors(i)) <= 1 for i in V))
    # c5: If an asset 'i' is selected (y[i]=1), its weight x[i] must be at least gamma.
    model.addConstrs((gamma * y[i] <= x[i] for i in V), name="c5")
    # c6: Asset weight x[i] is 0 if not selected (y[i]=0), and at most 1 if selected (y[i]=1).
    model.addConstrs((x[i] <= y[i] for i in V), name="c6")
    # c7: If 'valid_day_constr' is 'upfront', ensure on "good days" (z[t]=0) at least one selected asset met R_var.
    if config['valid_day_constr'] == 'upfront':
        model.addConstrs((gp.quicksum(y[i] for i in S[t]) >= 1 - z[t] for t in T_range), name="c7")
    # c8: If 'numOfselectedAssets' is specified (e.g., in iterative solver), fix the total number of selected assets.
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


    # Infeasible
    if model.status in [3, 4, 15]:
        solution =  {'solved': True, 'obj_bound': model.ObjBound, 'status': 'Inf'}
    # Timed out
    elif model.status == 9:
        solution = {'solved': False, 'obj_bound': model.ObjBound, 'status': 'TL'}
        # If found solution
        if model.SolCount > 0:
            weights = {i: x[i].X for i in V}
            selected_idx = [i for i in V if y[i].X > 0.5]
            solution['x'] = weights
            solution['selected_idx'] = selected_idx
            solution['obj_val'] = model.ObjVal
    # Optimal Solution
    else:
        weights = {i: x[i].X for i in V}
        selected_idx = [i for i in V if y[i].X > 0.5]
        solution = {'solved': True, 'x': weights, 'selected_idx': selected_idx, 'obj_val': model.ObjVal, 'status': 'Optimal'}


    return solution


def _solve_iterative(G, cliques, instance, config, flags, delta, callback):
    """
    Solve the asset allocation problem using an iterative warm-start strategy
    """
    best_solution = {'obj_val': float('-inf')}
    upper_bounds = [0]
    max_num_of_assets = _solve_max_num_of_assets(G, config)
    solutions = [{} for _ in range(max_num_of_assets)]
    prev_solved_iters = []
    time_limit = 300
    _timer = Timer(time_limit)
    _timer = Timer()

    # Set config for iterations
    config_iter = config
    config_iter['time_limit'] = time_limit

    # Get upper bounds
    for k in range(2, max_num_of_assets+1):
        upper_bounds.append(_solve_ub(instance, config, k))

    while True:
        # Solve bottom-up
        _timer.reset()

        for k in range(1, max_num_of_assets+1):
            # Skip if already solved
            if solutions[k-1].get('solved'):
                continue

            # Solve iteration
            if upper_bounds[k-1] < best_solution['obj_val']:
                current_solution = {'solved': True, 'obj_bound': upper_bounds[k-1], 'status': 'Inf-Ub'}
            else:
                current_solution = _solve(G, cliques, instance, config_iter, flags, delta, callback, k, best_solution)
            _timer.mark()

            # Update solutions and current best solution
            solutions[k-1] = current_solution
            best_solution = _get_best_solution(best_solution, current_solution, k)
        _timer.update()

        # Update solution unsolved cases
        solutions = _update_solutions(best_solution, solutions)

        # break
        # Stop if solved all, or if there is no improvement
        solved_iters = [d['solved'] for d in solutions]
        if all(solved_iters) or prev_solved_iters == solved_iters:
            break
        prev_solved_iters = solved_iters

    # Solve unsolved cases
    # solution = _solve(G, cliques, instance, config, flags, delta, callback, solution=solution)

    # Set iteration warmstart results to solution
    best_solution = _set_iter_results(best_solution, solutions, _timer)

    return best_solution


def _solve_max_num_of_assets(G2, config):
    """
    Solve maximum number of assets possible
    """
    gamma = config['gamma']
    V = G2.nodes

    # Create model
    model = gp.Model("Max_#Assets")

    # Suppress output
    model.setParam("OutputFlag", 0)

    # Add decision variables
    y = model.addVars(V, vtype=GRB.BINARY, name="y")

    # Set objective function
    obj_fn = gp.quicksum(y[i] for i in V)
    model.setObjective(obj_fn, GRB.MAXIMIZE)

    # Add constraints
    model.addConstrs((y[i] + y[j] <= 1 for (i, j) in G2.edges), name="c1")
    model.addConstr(obj_fn <= 1 / gamma, name="c2")
    
    # Solve
    model.optimize()
    
    return int(sum(y[i].X for i in V))


def _solve_ub(instance, config, numOfselectedAssets):
    """
    Calculate a simple upper bound on the objective value.
    """
    # Unpack instance data
    (assets, daily_returns, min_daily_return, mean_return,
     correlation_matrix, sigma, asset_pairs, total_days) = instance
    
    gamma = config['gamma']
    
    # Assign largest weight to best asset and others set to gamma
    top_k_indices = np.argsort(mean_return)[-numOfselectedAssets:]
    top_k_returns = mean_return[top_k_indices]
    weights = np.ones(numOfselectedAssets) * gamma
    weights[-1] = 1 - gamma * (numOfselectedAssets - 1)  

    # The dot product gives the objective value for this ideal, unconstrained portfolio.
    return weights.dot(top_k_returns)


def _get_best_solution(best_solution, current_solution, k):
    """
    Compare current solution to best solution and update
    """
    if current_solution.get('obj_val', float('-inf')) > best_solution['obj_val']:
        best_solution = current_solution
        best_solution['idx'] = k
        
    return best_solution


def _update_solutions(solution, solutions):
    """
    Update solutions unsolved cases
    """
    for d in solutions:
        if not d['solved'] and solution['obj_val'] >= d['obj_bound']:
            d['solved'] = True

    return solutions



def _set_iter_results(solution, solutions, timer):
    """
    Set iteration warmstart results to solution
    """
    solution['iter_results'] = {
        'obj_vals': [d.get('obj_val', d['status']) for d in solutions],
        'obj_bounds': [d.get('obj_bound', "-") for d in solutions],
        'solved_iters': [d['solved'] for d in solutions],
        'iter_runtimes': timer.runtimes_list,
        'loop_runtimes': timer.runtimes_sum,
        'best_idx': solution['idx']
    }
    solution['status'] = "Optimal" if all(solution['iter_results']['solved_iters']) else "Unsolved"

    return solution


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