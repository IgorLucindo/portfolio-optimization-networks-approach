import networkx as nx
import matplotlib.pyplot as plt


def get_financial_correlation_graph(instance, threshold=0.5):
    """
    Returns an undirected graph representing correlated financial assets
    """
    assets, mean, correlation_matrix, sigma, asset_pairs = instance
    
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
