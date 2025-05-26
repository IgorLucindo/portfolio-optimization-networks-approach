import numpy as np


def get_instances(prices_dict):
    instances = {}

    for asset_type, (assets, prices) in prices_dict.items():
        n = len(assets)

        # Compute parameters for instance
        daily_returns = np.diff(prices, axis=0) / prices[:-1]
        min_daily_return = np.min(daily_returns, axis=1)
        mean_return = np.mean(daily_returns, axis=0)
        correlation_matrix = np.corrcoef(daily_returns, rowvar=False)
        sigma = np.cov(daily_returns, rowvar=False)
        asset_pairs = {(i, j) for i in range(n) for j in range(i + 1, n)}
        total_days = len(daily_returns)

        # Append to instances
        instances[asset_type] = (
            assets, daily_returns, min_daily_return, mean_return,
            correlation_matrix, sigma, asset_pairs, total_days
        )

    return instances