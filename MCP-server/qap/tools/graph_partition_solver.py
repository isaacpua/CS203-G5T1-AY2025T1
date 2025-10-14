def run_graph_partition(nodes, edges):
    import os 
    import matplotlib.pyplot as plt
    from qap.utils.optimisation_utils import create_graph, qaoa_result
    from qiskit_optimization.applications import GraphPartition

    edges = [tuple(e) for e in edges]

    G = create_graph(nodes, edges)
    graph_partition_problem = GraphPartition(G)
    qp = graph_partition_problem.to_quadratic_program()

    sampler_type = 'simulation'
    result = qaoa_result(qp, sampler_type)

    img_path = os.path.join(os.getcwd(), "static", "image", "graphs", "graph_partition_graph.png")
    folder_path = os.path.dirname(img_path)

    os.makedirs(folder_path, exist_ok=True)

    plt.figure(figsize=(5, 5))  # Create a new figure
    graph_partition_problem.draw(result)
    plt.savefig(img_path, format="png", dpi=300)
    plt.close()

    return graph_partition_problem, result