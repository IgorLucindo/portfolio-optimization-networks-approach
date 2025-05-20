import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import numpy as np


def solve_max_return(G, instance, beta):
    """
    MIP formulation for maximum independent set with min correlation
    Return optimal portifolio and average_corr
    """
    assets, mean, correlation_matrix, sigma, asset_pairs = instance
    cliques = nx.find_cliques(G)
    cliques = [tuple(c) for c in cliques]
    min_weight = 0.05

    # Create model
    model = gp.Model("Max_Return")

    # Suppress output
    model.setParam("OutputFlag", 0)

    # Add decision variables
    x = model.addVars(G.nodes, vtype=GRB.CONTINUOUS, lb=0, name="x")
    z = model.addVars(G.nodes, vtype=GRB.BINARY, name="z")

    # Set objective function
    obj_fn = gp.quicksum(x[i] * mean[i] for i in G.nodes)
    model.setObjective(obj_fn, GRB.MAXIMIZE)

    # Add constraints
    model.addConstr(gp.quicksum(x[i] for i in G.nodes) == 1, name="c1")
    model.addConstrs((gp.quicksum(z[i] for i in c) <= 1 for c in cliques), name="c2")
    # model.addConstrs((z[i] * min_weight <= x[i] for i in G.nodes), name="c3")
    model.addConstrs((x[i] <= z[i] for i in G.nodes), name="c4")
    model.addQConstr(gp.QuadExpr(sum(x[i] * sigma[i, j] * x[j] for i in G.nodes for j in G.nodes)) <= beta, name="c5")
    
    # Solve
    model.optimize()

    return _extract_output(G, instance, x)


def _extract_output(G, instance, x):
    """
    Return optimal portifolio, expected return, portfolio variance, average correlation
    """
    assets, mean, correlation_matrix, sigma, asset_pairs = instance

    # Optimal portifolio
    selected_indices = [i for i in G.nodes if x[i].X > 0]
    portifolio = [assets[i] for i in selected_indices]

    # Expected return
    expected_return = sum(x[i].X * mean[i] for i in G.nodes)

    # Portfolio variance
    variance = sum(x[i].X * sigma[i, j] * x[j].X for i in G.nodes for j in G.nodes)

    # Average correlation
    pairs = {(i, j) for idx, i in enumerate(selected_indices) for j in selected_indices[idx + 1:]}
    avg_corr = np.mean([abs(correlation_matrix[i, j]) for i, j in pairs]) if pairs else 0

    return len(portifolio), expected_return, variance, avg_corr