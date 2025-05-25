import numpy as np


def extract_output(G, instance, x):
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