from classes.Dataset import *
from utils.instance_utils import *
from utils.graph_utils import *
from utils.solve_utils import *
from utils.results_utils import *


# Set parameter flags
flags = {
    'plot': False,
    'plot_results': False,
    'save': True
}


def main():
    # Get dataset
    dt = Dataset("yahoo_finance")

    # Get instances
    instances = get_instances(dt.prices_dict)

    # Set parameters
    # thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    thresholds = [0.4]

    results = []

    for instance in instances:
        for t in thresholds:
            # Create graph based on instance
            G = get_financial_correlation_graph(instance, t)
            G2 = power_graph(G, 2)

            # Solve optimal portifolio for different betas
            results.append(solve_max_return(G2, instance))

            # Show graphs
            show_graphs([G], flags['plot'])
        results.append(["", "", "", ""])
    
    # Save results
    save_results(results, flags['save'])
    plot_results(results, flags['plot_results'])


if __name__ == "__main__":
    main()