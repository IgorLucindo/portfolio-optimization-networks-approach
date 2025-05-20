from utils.instance_utils import *
from utils.graph_utils import *
from utils.solve_utils import *
from utils.results_utils import *


# Set parameter flags
flags = {
    'plot': False,
    'plot_results': False,
    'save': False
}


def main():
    # Get instances
    instances = get_financial_assets()

    # Set parameters
    # thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    thresholds = [0.4]
    beta_factors = [1, 5, 10, 20, 50]
    # beta_factors = [0.5]

    results = []

    for instance in instances.values():
        sigma_diag_min = np.min(np.diag(instance[3]))
        # sigma_diag_min = np.mean(np.diag(instance[3]))
        for t in thresholds:
            # Create graph based on instance
            G = get_financial_correlation_graph(instance, t)

            # Solve optimal portifolio for different betas
            for factor in beta_factors:
                beta = sigma_diag_min * factor
                results.append(solve_max_return(G, instance, beta))

            # Show graphs
            show_graphs([G], flags['plot'])
        results.append(["", "", "", ""])
    
    # Save results
    save_results(results, flags['save'])
    plot_results(results, flags['plot_results'])


if __name__ == "__main__":
    main()