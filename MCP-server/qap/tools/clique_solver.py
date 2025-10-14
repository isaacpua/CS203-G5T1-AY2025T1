def run_clique(nodes, edges, size=None):
    import os 
    import matplotlib.pyplot as plt
    from qap.utils.optimisation_utils import create_graph, qaoa_result
    from qiskit_optimization.applications import Clique

    edges = [tuple(e) for e in edges]

    G = create_graph(nodes, edges)
    clique_problem = Clique(G, size)
    qp = clique_problem.to_quadratic_program()

    sampler_type = 'simulation'
    result = qaoa_result(qp, sampler_type)

    img_path = os.path.join(os.getcwd(), "static", "image", "graphs", "clique_graph.png")
    folder_path = os.path.dirname(img_path)

    os.makedirs(folder_path, exist_ok=True)

    plt.figure(figsize=(5, 5))  # Create a new figure
    clique_problem.draw(result)
    plt.savefig(img_path, format="png", dpi=300)
    plt.close()
    
    return clique_problem, result
