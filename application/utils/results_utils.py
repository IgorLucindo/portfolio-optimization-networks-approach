import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os


def save_results(results, save_flag=False):
    """
    Save results in results folder
    """
    if not save_flag:
        return
    
    results_path = "application/results"
    os.makedirs(results_path, exist_ok=True)

    # Create dataframe for exporting to xlsx file
    df = pd.DataFrame(results, columns=["Portifolio", "Expected Return", "Portifolio Variance", "Average Correlation"])
    df.to_excel(os.path.join(results_path, "results.xlsx"), index=False)


def plot_results(results, plot_flag=False):
    """
    Plot results with beta_factors as point labels (larger and repositioned)
    """
    if not plot_flag:
        return
        
    results = np.array(results)
    expected_return = results[:, 1]
    variance = results[:, 2]

    def split_on_empty(data):
        groups = []
        current = []
        for val in data:
            if val == '' or val is None:
                if current:
                    groups.append(current)
                    current = []
            else:
                current.append(val)
        if current:
            groups.append(current)
        return [[float(x) for x in group] for group in groups]

    # Split the data
    expected_return_groups = split_on_empty(expected_return)
    variance_groups = split_on_empty(variance)

    titles = ["Bonds", "Stocks", "Commodities", "Cryptocurrencies"]

    # Plot each group separately
    for i, (expect, var) in enumerate(zip(expected_return_groups, variance_groups)):
        plt.figure()
        plt.plot(var, expect, marker='o')
        title = titles[i] if i < len(titles) else f"Group {i+1}"
        plt.xlabel("Variance")
        plt.ylabel("Expected Return")
        plt.title(f"{title}: Expected Return vs Variance")
        plt.grid(True)
        plt.tight_layout()
        plt.show()