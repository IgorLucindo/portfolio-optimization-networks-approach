import gurobipy as gp
from gurobipy import GRB
import networkx as nx


def solve_max_return(G, instance, delta=0.5, R_var=0.001, gamma=0.05):
    """
    MIP formulation for maximum mean return
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
    model.addConstrs((gp.quicksum(y[i] for i in c) <= 1 for c in cliques))
    model.addConstrs((gamma * y[i] <= x[i] for i in G.nodes), name="c5")
    model.addConstrs((x[i] <= y[i] for i in G.nodes), name="c6")
    
    # Solve
    model.optimize()

    weights = [x[i].X for i in G.nodes]
    selected_indices = [i for i in G.nodes if y[i].X > 0.5]
    
    return weights, selected_indices