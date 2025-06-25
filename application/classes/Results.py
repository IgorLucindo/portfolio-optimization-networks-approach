from collections import defaultdict
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
    def __init__(self, flags, config):
        self.flags = flags
        self.config = config

        self.data = defaultdict(list)
        self.iters_data = defaultdict(list)
        self.save_data = []
        self.save_iters_data = []

        self.save_solution_collumns = [
            "Partition", "Threshold", "Delta", "Density", "Portifolio",
            "Expected Return", "Expected Return (Bound)", "Portifolio Variance",
            "Average Correlation", "Runtime (s)", "Status"
        ]
        self.save_iters_collumns = [
            "Partition", "Best ObjVal", "ObjVals", "#Solved Iterations (%)",
            "Unsolved Cases", "ObjVals (unsolved)", "ObjBounds (unsolved)",
            "Gaps (%) (unsolved)", "Runtimes (s)"
        ]
        self.row_length = [
            len(self.save_solution_collumns),
            len(self.save_iters_collumns)
        ]

        # Create results folder
        self.path = "application/results/"
        os.makedirs(self.path, exist_ok=True)


    def set_data(self, solutions, partition_name, t, delta, G, instance, runtimes):
        """
        Set data results
        """
        (assets, daily_returns, min_daily_return, mean_return,
         correlation_matrix, sigma, asset_pairs, total_days) = instance

        for k, solution in enumerate(solutions):
            keys = ['x', 'selected_idx', 'obj_val', 'obj_bound', 'status', 'obj_vals', 'obj_bounds', 'solved_iters', 'iter_runtimes', 'idx']
            x, selected_idx, obj_val, obj_bound, status, obj_vals, obj_bounds, solved_iters, iter_runtimes, best_idx = (solution.get(k, "-") for k in keys)

            # Optimal portifolio
            portifolio = [assets[i] for i in selected_idx]

            # Portfolio variance
            variance = sum(x[i] * sigma[i, j] * x[j] for i in G.nodes for j in G.nodes)

            # Average correlation
            pairs = {(i, j) for idx, i in enumerate(selected_idx) for j in selected_idx[idx + 1:]}
            avg_corr = np.mean([abs(correlation_matrix[i, j]) for i, j in pairs]) if pairs else 0

            # Append solution result data
            self.data[k].append([
                partition_name, t, delta, nx.density(G), {len(portifolio): portifolio},
                obj_val, obj_bound, variance, avg_corr, runtimes[k], status
            ])

            # --- Iteration warmstart method ---
            if self.config['iterative_warmstart']:
                # Best objective value
                obj_val = {(best_idx+1): round(obj_val, 4)}

                # Solved cases percentage
                solved_iters_percentage = sum(solved_iters) / len(solved_iters) * 100

                # Unsolved cases
                unsolved_idx = [idx for idx, val in enumerate(solved_iters) if not val]
                unsolved_cases = [idx+1 for idx in unsolved_idx]

                # Objective values of unsolved cases
                obj_vals_unsolved = {idx+1: round(obj_vals[idx], 4) for idx in unsolved_idx}

                # Objective bounds of unsolved cases
                obj_bounds_unsolved = {idx+1: round(obj_bounds[idx], 4) for idx in unsolved_idx}

                # Gaps of unsolved cases
                gaps_unsolved = {
                    idx: round(abs((obj_vals_unsolved[idx] - obj_bounds_unsolved[idx]) / (obj_vals_unsolved[idx]) * 100))
                    for idx in obj_vals_unsolved if obj_vals_unsolved[idx] != "-"
                }

                # Round values
                obj_vals = [round(value, 4) if value != "-" else "-" for value in obj_vals]
                obj_vals_unsolved = {key: round(value, 4) if value != "-" else "-" for key, value in obj_vals_unsolved.items()}
                obj_bounds_unsolved = {key: round(value, 4) if value != "-" else "-" for key, value in obj_bounds_unsolved.items()}

                # Append iteration warmstart result data
                self.iters_data[k].append([
                    partition_name, obj_val, obj_vals, solved_iters_percentage,
                    unsolved_cases, obj_vals_unsolved, obj_bounds_unsolved,
                    gaps_unsolved, iter_runtimes
                ])


    def set_save_data(self, asset_type):
        """
        Set data results for saving
        """
        table_names = ["No Callback", "Callback 1", "Callback 2"]
        
        self.save_data.append(self.fill_row([asset_type], 0))
        self.save_iters_data.append(self.fill_row([asset_type], 1))

        for k in self.data.keys():
            self.save_data.append(self.fill_row([table_names[k]], 0))
            self.save_data.extend(self.data[k])
            self.save_iters_data.append(self.fill_row([table_names[k]], 1))
            self.save_iters_data.extend(self.iters_data[k])

        # Reset data
        self.data = defaultdict(list)
        self.iters_data = defaultdict(list)


    def set_save_data_config(self, config):
        """
        Set configuration for saving
        """
        for _ in range(3):
            self.save_data.append(self.fill_row([], 0))
            self.save_iters_data.append(self.fill_row([], 1))

        for key, value in config.items():
            self.save_data.append(self.fill_row([key, value], 0))
            self.save_iters_data.append(self.fill_row([key, value], 1))


    def fill_row(self, _list, row_idx):
        return (_list + [""] * self.row_length[row_idx])[:self.row_length[row_idx]]


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
        self.save_solution()
        self.save_iters()


    def save_solution(self):
        """
        Save solution results
        """
        if not self.flags['save_results']:
            return
        
        # Create dataframe for exporting to xlsx file
        df = pd.DataFrame(self.save_data, columns=self.save_solution_collumns)
        df.to_excel(self.path + "results.xlsx", index=False)


    def save_iters(self):
        """
        Save results in results folder
        """
        if not self.flags['save_results'] or not self.config['iterative_warmstart']:
            return
        
        # Create dataframe for exporting to xlsx file
        df = pd.DataFrame(self.save_iters_data, columns=self.save_iters_collumns)
        df.to_excel(self.path + "iters_results.xlsx", index=False)