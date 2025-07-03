from classes.Dataset import *
from classes.Timer import *
from classes.Results import *
from utils.instance_utils import *
from utils.graph_utils import *
from utils.solve_utils import *


# Set parameter flags
flags = {
    'plot': False,
    'plot_results': False,
    'print_diagnosis': False,
    'save_results': True,
    'save_log': False
}

# Set configuration
config1 = {
    'idx': 1,
    'dataset_name': 'l',           # 'm' or 'l'
    'assets': {'range': 500, '#partitions': 5},
    # 'thresholds': [0.3, 0.4, 0.5, 0.6, 0.7],
    'thresholds': [0.4],
    # 'deltas': [0.55, 0.6, 0.65, 0.7, 0.75],
    'deltas': [0.6],
    'R_var': 0.01,
    'gamma': 0.05,
    'time_limit': 7200,
    'dist_constr': 'star',       # 'clique' or 'star'
    'valid_day_constr': False,
    'delta_constr': 'inequality',   # 'equality' or 'inequality
    'iterative_warmstart': False
}
config2 = {
    'idx': 2,
    'dataset_name': 'l',           # 'm' or 'l'
    'assets': {'range': 500, '#partitions': 10},
    'thresholds': [0.4],
    'deltas': [0.05],
    'R_var': -0.01,
    'gamma': 0.05,
    'time_limit': 7200,
    'dist_constr': 'star',       # 'clique' or 'star'
    'valid_day_constr': False,
    'delta_constr': 'inequality',   # 'equality' or 'inequality
    'iterative_warmstart': True
}
config = config1


def main():
    # Get dataset
    dt = Dataset(config)
    results = Results(flags, config)

    # Get instances
    instances = get_instances(dt.prices_dict)

    # Create Timer class after loading instances
    timer = Timer()

    for asset_type, partition_instances in instances.items():
        results.set_data_row([asset_type])

        for partition_name, instance in partition_instances.items():
            for t in config['thresholds']:
                # Create network power graph and get maximal cliques
                G, G2 = get_correlation_power_graph(instance, t)
                cliques = [tuple(c) for c in nx.find_cliques(G2)]

                for delta in config['deltas']:
                    # Solve optimal portfolio
                    timer.reset()
                    solution = solve_max_return(G2, cliques, instance, config, flags, delta)
                    timer.mark()
                    timer.update()

                    # Set results
                    results.set_data(solution, partition_name, t, delta, G, instance, timer.runtimes[0])

                # Show graphs
                show_graphs([G2], flags['plot'])

        results.set_data_row([])
    results.set_data_config()
    
    # Print results
    results.print(timer.total_runtime)
    # Plot results
    results.plot()
    # Save results
    results.save()


if __name__ == "__main__":
    main()