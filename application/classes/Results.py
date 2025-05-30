import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
import sys
import os


class Results:
    """
    class that contains methods to print and save results
    """
    def __init__(self, flags):
        self.flags = flags
        self.data = []

        # Create results folder
        os.makedirs('application/results', exist_ok=True)


    def set_data(self, t, G, instance, solution, runtime):
        """
        Return optimal portifolio, expected return, portfolio variance, average correlation
        """
        (assets, daily_returns, min_daily_return, mean_return,
        correlation_matrix, sigma, asset_pairs, total_days) = instance
        x, selected_indices = solution

        # Optimal portifolio
        portifolio = [assets[i] for i in selected_indices]

        # Expected return
        expected_return = sum(x[i] * mean_return[i] for i in G.nodes)

        # Portfolio variance
        variance = sum(x[i] * sigma[i, j] * x[j] for i in G.nodes for j in G.nodes)

        # Average correlation
        pairs = {(i, j) for idx, i in enumerate(selected_indices) for j in selected_indices[idx + 1:]}
        avg_corr = np.mean([abs(correlation_matrix[i, j]) for i, j in pairs]) if pairs else 0

        self.data.append([t, nx.density(G), portifolio, len(portifolio), expected_return, variance, avg_corr, runtime])


    def set_data_instance_name(self, instance_name):
        self.data.append([instance_name, "", "", "", "", "", "", ""])


    def print(self, total_runtime):
        """
        Print methods for results class
        """
        self.print_instance_diagnosis(total_runtime)
        

    def print_instance_diagnosis(self, total_runtime):
        """
        Print instance diagnosis
        """
        if not self.flags['print_diagnosis']: return

        sys.stdout.write(f"\rCurrent Time: {int(total_runtime // 60):02}:{int(total_runtime % 60):02}")
        sys.stdout.flush()


    def plot(self):
        """
        Plot results with beta_factors as point labels (larger and repositioned)
        """
        if not self.flags['plot_results']:
            return
            
        results = np.array(results.data)
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


    def save(self):
        """
        Save results in results folder
        """
        if not self.flags['save_results']:
            return
        
        # Create dataframe for exporting to xlsx file
        df = pd.DataFrame(self.data, columns=["Threshold", "Density", "Portifolio", "#Portifolio", "Expected Return", "Portifolio Variance", "Average Correlation", "Runtime (s)"])
        df.to_excel(os.path.join("application/results", "results.xlsx"), index=False)