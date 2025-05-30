import gurobipy as gp
from gurobipy import GRB
import networkx as nx


def solve_max_return(G, instance, delta=0.68, R_var=0.01, gamma=0.05):
    """
    MIP formulation for maximum mean return
    """
    (assets, daily_returns, min_daily_return, mean_return,
     correlation_matrix, sigma, asset_pairs, total_days) = instance
    cliques = [tuple(c) for c in nx.find_cliques(G)]
    T_range = range(total_days)

    # Create model
    model = gp.Model("Max_Return")

    # Suppress output
    model.setParam("OutputFlag", 0)

    # Add decision variables
    x = model.addVars(G.nodes, vtype=GRB.CONTINUOUS, lb=0, name="x")
    y = model.addVars(G.nodes, vtype=GRB.BINARY, name="y")
    z = model.addVars(T_range, vtype=GRB.BINARY, name="z")

    # Set objective function
    obj_fn = gp.quicksum(mean_return[i] * x[i] for i in G.nodes)
    model.setObjective(obj_fn, GRB.MAXIMIZE)

    # Fixing
    # Fix dates that weighted return cannot surpass R_var
    for t in T_range:
        if max(daily_returns[t]) < R_var:
            z[t].lb = 1

    # Add constraints
    model.addConstrs(
        (gp.quicksum(daily_returns[t, i] * x[i] for i in G.nodes) >= R_var - (R_var - min_daily_return[t]) * z[t]
         for t in T_range),
        name="c1"
    )
    model.addConstr(gp.quicksum(z[t] for t in T_range) / total_days <= delta, name="c2")
    model.addConstr(gp.quicksum(x[i] for i in G.nodes) == 1, name="c3")
    model.addConstrs((gp.quicksum(y[i] for i in c) <= 1 for c in cliques))
    model.addConstrs((gamma * y[i] <= x[i] for i in G.nodes), name="c5")
    model.addConstrs((x[i] <= y[i] for i in G.nodes), name="c6")
    
    # Solve
    model.optimize()

    weights = {i: x[i].X for i in G.nodes}
    selected_indices = [i for i in G.nodes if y[i].X > 0.5]
    
    return weights, selected_indices


def solve_max_return_cb(G, instance, delta=0.68, R_var=0.01, gamma=0.05):
    """
    MIP formulation for maximum mean return
    """
    (assets, daily_returns, min_daily_return, mean_return,
     correlation_matrix, sigma, asset_pairs, total_days) = instance
    cliques = [tuple(c) for c in nx.find_cliques(G)]
    T_range = range(total_days)

    # Create model
    model = gp.Model("Max_Return")

    # Suppress output
    model.setParam("OutputFlag", 0)

    # Enable lazy constraints
    model.setParam(GRB.Param.LazyConstraints, 1)

    # Add decision variables
    x = model.addVars(G.nodes, vtype=GRB.CONTINUOUS, lb=0, name="x")
    y = model.addVars(G.nodes, vtype=GRB.BINARY, name="y")
    z = model.addVars(T_range, vtype=GRB.BINARY, name="z")

    # Set objective function
    obj_fn = gp.quicksum(mean_return[i] * x[i] for i in G.nodes)
    model.setObjective(obj_fn, GRB.MAXIMIZE)

    # Fixing
    # Fix dates that weighted return cannot surpass R_var
    # for t in T_range:
    #     if max(daily_returns[t]) < R_var:
    #         z[t].lb = 1

    # Add constraints
    model.addConstr(gp.quicksum(z[t] for t in T_range) / total_days <= delta, name="c1")
    model.addConstr(gp.quicksum(x[i] for i in G.nodes) == 1, name="c2")
    model.addConstrs((gp.quicksum(y[i] for i in c) <= 1 for c in cliques))
    model.addConstrs((gamma * y[i] <= x[i] for i in G.nodes), name="c4")
    model.addConstrs((x[i] <= y[i] for i in G.nodes), name="c5")

    def lazy_callback(model, where):
        if where == GRB.Callback.MIPSOL:
            # Get the current solution
            x_ = model.cbGetSolution(x)
            y_ = model.cbGetSolution(y)
            z_ = model.cbGetSolution(z)

            S, S_bar = [], []
            for i in G.nodes:
                (S if y_[i] > 0.5 else S_bar).append(i)

            # Check violation
            for t in T_range:
                if z_[t] > 0.5 or sum(daily_returns[t, i] * x_[i] for i in G.nodes) >= R_var:
                    continue
                daily_returns_St = [daily_returns[t, i] for i in S]
                if max(daily_returns_St) < R_var:
                    model.cbLazy(gp.quicksum(y[i] for i in S_bar) >= 1)
                else:
                    model.cbLazy(gp.quicksum(daily_returns[t, i] * x[i] for i in G.nodes) >= R_var)

    # Solve
    model.optimize(lazy_callback)

    weights = [x[i].X for i in G.nodes]
    selected_indices = [i for i in G.nodes if y[i].X > 0.5]
    
    return weights, selected_indices