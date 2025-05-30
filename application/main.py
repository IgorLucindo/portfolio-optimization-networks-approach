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
    'print_diagnosis': True,
    'save_results': True
}


def main():
    # Get dataset
    dt = Dataset("l")
    results = Results(flags)

    # Get instances
    instances = get_instances(dt.prices_dict)

    # Set parameters
    # thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    thresholds = [0.4]

    # Create Timer class after loading instances
    timer = Timer()

    for instance_name, instance in instances.items():
        results.set_data_instance_name(instance_name)

        for t in thresholds:
            timer.reset()

            # Create graph based on instance
            G = get_financial_correlation_graph(instance, t)
            G2 = power_graph(G, 2)
            remove_negative_return_vertices(G2, instance[3])

            # Solve optimal portifolio for different betas
            solution = solve_max_return(G2, instance)
            timer.mark()
            timer.update()

            results.set_data(t, G2, instance, solution, timer.instance_runtimes[0])

            # Show graphs
            show_graphs([G], flags['plot'])
    
    # Print results
    results.print(timer.total_runtime)
    # Plot results
    results.plot()
    # Save results
    results.save()


if __name__ == "__main__":
    main()