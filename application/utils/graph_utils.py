import networkx as nx
import matplotlib.pyplot as plt


def get_correlation_power_graph(instance, t):
    """
    Return an undirected power graph representing correlated assets
    """
    G = get_correlation_graph(instance, t)
    G2 = power_graph(G, 2)
    remove_negative_return_vertices(G, instance[3])
    remove_negative_return_vertices(G2, instance[3])

    return G, G2


def get_correlation_graph(instance, threshold=0.5):
    """
    Returns an undirected graph representing correlated assets
    """
    (assets, daily_returns, min_daily_return, mean_return,
     correlation_matrix, sigma, asset_pairs, total_days) = instance
    
    # Create graph
    G = nx.Graph()

    # Add vertices
    G.add_nodes_from(range(len(assets)))

    # Add edges
    edges_to_add = {
        (i, j) for i, j in asset_pairs if correlation_matrix[i, j] > threshold
    }
    G.add_edges_from(edges_to_add)

    return G


def power_graph(G, k):
    """
    Return k-th power of a graph
    """
    edges_to_add = set()
    vertices = list(G.nodes)

    for u in vertices:
        lengths = nx.single_source_shortest_path_length(G, u, cutoff=k)
        for v in lengths:
            if u != v:
                edge = tuple(sorted([u, v]))
                edges_to_add.add(edge)

    G_power = nx.Graph()
    G_power.add_nodes_from(vertices)
    G_power.add_edges_from(edges_to_add)

    return G_power


def remove_negative_return_vertices(G, mean_return):
    """
    Remove vertices that correspond to assets with negative mean return
    """
    vertices_to_remove = [i for i in G.nodes if mean_return[i] < 0]
    G.remove_nodes_from(vertices_to_remove)


def show_graphs(graphs, plot_flag=True):
    """
    Plot graphs with faint edges and no labels.
    """
    if not plot_flag:
        return

    num_graphs = len(graphs)
    _, axes = plt.subplots(1, num_graphs, figsize=(5 * num_graphs, 5))
    if num_graphs == 1:
        axes = [axes]

    for i, G in enumerate(graphs):
        pos = nx.spring_layout(G, k=1)

        # Draw graph without any labels
        nx.draw(
            G,
            pos,
            with_labels=False,
            node_color='lightblue',
            edge_color='gray',
            alpha=0.8,
            width=0.5,
            ax=axes[i]
        )

    plt.tight_layout()
    plt.show()