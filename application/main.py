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
    deltas = [0.55, 0.6, 0.65, 0.7, 0.8]
    R_var = 0.01

    # Create Timer class after loading instances
    timer = Timer()

    for instance_name, instance in instances.items():
        for t in thresholds:
            # Create network power graph and get maximal cliques
            G2 = get_correlation_power_graph(instance, t)
            cliques = [tuple(c) for c in nx.find_cliques(G2)]

            for delta in deltas:
                solutions = []
                timer.reset()
                # Solve optimal portifolio
                # solutions = solve_max_return_unconstrained(G2.nodes, instance, delta, R_var)
                solutions.append(solve_max_return(G2.nodes, cliques, instance, delta, R_var))
                timer.mark()
                solutions.append(solve_max_return_cb(G2.nodes, cliques, instance, delta, R_var))
                timer.mark()
                solutions.append(solve_max_return_cb2(G2.nodes, cliques, instance, delta, R_var))
                timer.mark()
                timer.update()

                # Set results
                results.set_data(solutions, t, delta, G2, instance, timer.instance_runtimes)

            # Show graphs
            show_graphs([G2], flags['plot'])

        results.set_save_data(instance_name, len(instance[0]))
    
    # Print results
    results.print(timer.total_runtime)
    # Plot results
    results.plot()
    # Save results
    results.save()


if __name__ == "__main__":
    main()