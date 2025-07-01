from utils.calculation_utils import *
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

        self.data = []
        self.iters_data = []
        self.ref_data = []

        self.solution_columns = [
            "Partition", "Threshold", "Delta", "Density", "Portfolio",
            "Expected Return", "Expected Return (Bound)", "Portfolio Variance",
            "Average Correlation", "Runtime (s)", "Status"
        ]
        self.iters_columns = [
            "Partition", "Best ObjVal", "Ref ObjVal", "Dif ObjVal (%)", "ObjVals",
            "#Solved Iterations (%)", "Unsolved Cases", "ObjVals (unsolved)",
            "ObjBounds (unsolved)", "Gaps (%) (unsolved)", "Runtimes (s)",
            "Total Runtime (s)", "Ref Total Runtime (s)", "Ref Status"
        ]
        self.row_length = [
            len(self.solution_columns),
            len(self.iters_columns)
        ]

        # Create results folder
        self.path = "application/results/"
        os.makedirs(self.path, exist_ok=True)

        # Get reference data
        self.get_ref_data()

    
    def get_ref_data(self):
        """
        Get reference data for saving results
        """
        if not self.flags['save_results'] or not self.config['iterative_warmstart']:
            return
        
        # Get file path
        file_name = f"results_ref{self.config['idx']}.xlsx"
        file_path = os.path.join("application/results/reference", file_name)

        # Read the Excel file
        df = pd.read_excel(file_path)

        # Get subset of Excel file
        subset = df.loc[1:, ['Portfolio', 'Expected Return', 'Runtime (s)', 'Status']]
        mask = subset['Portfolio'].isna()
        first_empty_index = mask.idxmax() if mask.any() else subset.index[-1] + 1
        final_subset = subset.loc[:first_empty_index - 1]

        # Convert to lists
        portfolios = final_subset['Portfolio'].tolist()
        objvals = final_subset['Expected Return'].tolist()
        runtimes = final_subset['Runtime (s)'].tolist()
        status = final_subset['Status'].tolist()

        # Append to reference result data
        for i in range(len(portfolios)):
            self.ref_data.append([{portfolios[i][1]: round(objvals[i], 4)}, runtimes[i], status[i]])


    def set_data(self, solution, partition_name, t, delta, G, instance, runtime):
        """
        Set data results
        """
        (assets, daily_returns, min_daily_return, mean_return,
         correlation_matrix, sigma, asset_pairs, total_days) = instance

        keys = ['x', 'selected_idx', 'obj_val', 'obj_bound', 'status']
        keys_iter = ['obj_vals', 'obj_bounds', 'solved_iters', 'iter_runtimes', 'best_idx']
        x, selected_idx, obj_val, obj_bound, status = (solution.get(k, "-") for k in keys)
        obj_vals, obj_bounds, solved_iters, iter_runtimes, best_idx = (solution.get('iter_results').get(k, "-") for k in keys_iter)

        # Calculate data resutls
        portfolio = [assets[i] for i in selected_idx]
        variance = sum(x[i] * sigma[i, j] * x[j] for i in G.nodes for j in G.nodes)
        pairs = {(i, j) for idx, i in enumerate(selected_idx) for j in selected_idx[idx + 1:]}
        avg_corr = np.mean([abs(correlation_matrix[i, j]) for i, j in pairs]) if pairs else 0

        # Append solution result data
        self.data.append([
            partition_name, t, delta, nx.density(G), {len(portfolio): portfolio},
            obj_val, obj_bound, variance, avg_corr, runtime, status
        ])

        # --- Iteration warmstart method ---
        if self.config['iterative_warmstart']:
            # Calculate data iter results
            obj_val = {best_idx: round(obj_val, 4)}
            solved_iters_percentage = sum(solved_iters) / len(solved_iters) * 100
            unsolved_idx = [idx+1 for idx, value in enumerate(solved_iters) if not value]
            obj_vals_unsolved = {idx: obj_vals[idx-1] for idx in unsolved_idx}
            obj_bounds_unsolved = {idx: obj_bounds[idx-1] for idx in unsolved_idx}
            gaps_unsolved = {
                idx: round(abs((value - obj_bounds_unsolved[idx]) / obj_vals_unsolved[idx] * 100), 1)
                for idx, value in obj_vals_unsolved.items() if isinstance(value, (int, float))
            }
            ref_objval, ref_runtime, ref_status = self.ref_data.pop(0)
            obj_val_value = list(obj_val.values())[0]
            ref_obj_val_value = list(ref_objval.values())[0]
            dif_objval = round((ref_obj_val_value - obj_val_value) / ref_obj_val_value * 100, 1)

            # Round values
            obj_vals = round_array(obj_vals, 4)
            obj_vals_unsolved = round_dict(obj_vals_unsolved, 4)
            obj_bounds_unsolved = round_dict(obj_bounds_unsolved, 4)

            # Append iteration warmstart result data
            self.iters_data.append([
                partition_name, obj_val, ref_objval, dif_objval, obj_vals,
                solved_iters_percentage, unsolved_idx, obj_vals_unsolved,
                obj_bounds_unsolved, gaps_unsolved, iter_runtimes, runtime,
                ref_runtime, ref_status
            ])

            
    def fill_row(self, _list, row_idx):
        return (_list + [""] * self.row_length[row_idx])[:self.row_length[row_idx]]
    

    def set_data_row(self, row):
        """
        Set data row
        """
        self.data.append(self.fill_row(row, 0))
        self.iters_data.append(self.fill_row(row, 1))


    def set_data_config(self):
        """
        Set configuration for saving
        """
        for _ in range(3):
            self.data.append(self.fill_row([], 0))
            self.iters_data.append(self.fill_row([], 1))

        for key, value in self.config.items():
            self.data.append(self.fill_row([key, value], 0))
            self.iters_data.append(self.fill_row([key, value], 1))


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
        df = pd.DataFrame(self.data, columns=self.solution_columns)
        df.to_excel(self.path + f"results{self.config['idx']}.xlsx", index=False)


    def save_iters(self):
        """
        Save results in results folder
        """
        if not self.flags['save_results'] or not self.config['iterative_warmstart']:
            return
        
        # Create dataframe for exporting to xlsx file
        df = pd.DataFrame(self.iters_data, columns=self.iters_columns)
        df.to_excel(self.path + f"iters_results{self.config['idx']}.xlsx", index=False)