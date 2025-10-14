def run_max_cut(nodes, edges):
    import os
    import matplotlib.pyplot as plt
    import networkx as nx
    from qap.utils.optimisation_utils import create_graph, qaoa_result, draw_graph
    from qiskit_optimization.applications import Maxcut
    edges = [tuple(e) for e in edges]

    G = create_graph(nodes, edges)
    maxcut = Maxcut(G)
    qp = maxcut.to_quadratic_program()

    sampler_type = 'simulation'
    result = qaoa_result(qp, sampler_type)

    img_path = os.path.join(os.getcwd(), "static", "image", "graphs", "max_cut_graph.png")
    folder_path = os.path.dirname(img_path)

    os.makedirs(folder_path, exist_ok=True)

    plt.figure(figsize=(5, 5))  # Create a new figure
    colors = ["r" if result[i] == 0 else "c" for i in range(nodes)]
    pos = nx.spring_layout(G, seed=111)
    draw_graph(G, colors, pos)
    plt.savefig(img_path, format="png", dpi=300)
    plt.close()

    return maxcut, result
