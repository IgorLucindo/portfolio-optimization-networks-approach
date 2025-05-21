import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import numpy as np


def solve_max_return(G, instance, delta=0.5, R_var=0.001, gamma=0.05):
    """
    MIP formulation for maximum independent set with min correlation
    Return optimal portifolio and average_corr
    """
    (assets, daily_returns, min_daily_return, mean_return,
     correlation_matrix, sigma, asset_pairs, total_days) = instance
    cliques = [tuple(c) for c in nx.find_cliques(G)]

    # Create model
    model = gp.Model("Max_Return")

    # Suppress output
    model.setParam("OutputFlag", 0)

    # Add decision variables
    x = model.addVars(G.nodes, vtype=GRB.CONTINUOUS, lb=0, name="x")
    y = model.addVars(G.nodes, vtype=GRB.BINARY, name="y")
    z = model.addVars(range(total_days), vtype=GRB.BINARY, name="z")

    # Set objective function
    obj_fn = gp.quicksum(mean_return[i] * x[i] for i in G.nodes)
    model.setObjective(obj_fn, GRB.MAXIMIZE)

    # Add constraints
    model.addConstrs(
        (gp.quicksum(daily_returns[t, i] * x[i] for i in G.nodes) >= R_var - (R_var - min_daily_return[t]) * z[t]
         for t in range(total_days)),
        name="c1"
    )
    model.addConstr(gp.quicksum(z[t] for t in range(total_days)) / total_days <= delta, name="c2")
    model.addConstr(gp.quicksum(x[i] for i in G.nodes) == 1, name="c3")
    model.addConstrs((gp.quicksum(y[i] for i in c) <= 1 for c in cliques), name="c4")
    model.addConstrs((gamma * y[i] <= x[i] for i in G.nodes), name="c5")
    model.addConstrs((x[i] <= y[i] for i in G.nodes), name="c6")
    
    # Solve
    model.optimize()

    return _extract_output(G, instance, x)


def _extract_output(G, instance, x):
    """
    Return optimal portifolio, expected return, portfolio variance, average correlation
    """
    (assets, daily_returns, min_daily_return, mean_return,
     correlation_matrix, sigma, asset_pairs, total_days) = instance

    # Optimal portifolio
    selected_indices = [i for i in G.nodes if x[i].X > 0]
    portifolio = [assets[i] for i in selected_indices]

    # Expected return
    expected_return = sum(x[i].X * mean_return[i] for i in G.nodes)

    # Portfolio variance
    variance = sum(x[i].X * sigma[i, j] * x[j].X for i in G.nodes for j in G.nodes)

    # Average correlation
    pairs = {(i, j) for idx, i in enumerate(selected_indices) for j in selected_indices[idx + 1:]}
    avg_corr = np.mean([abs(correlation_matrix[i, j]) for i, j in pairs]) if pairs else 0

    return len(portifolio), expected_return, variance, avg_corr