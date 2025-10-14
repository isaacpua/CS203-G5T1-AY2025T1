def run_tsp(nodes, edges):
    import os 
    import matplotlib.pyplot as plt
    import networkx as nx
    from qap.utils.optimisation_utils import create_graph, qaoa_result, draw_tsp_solution
    from qiskit_optimization.applications import Tsp  

    edges = [tuple(e) for e in edges]

    G = create_graph(nodes, edges)
    colors = ["r" for node in G.nodes()]
    pos = nx.spring_layout(G, seed=42)

    tsp_problem = Tsp(G) # Create TSP object
    qp = tsp_problem.to_quadratic_program()
    
    sampler_type = 'simulation'
    result = qaoa_result(qp, sampler_type)

    img_path = os.path.join(os.getcwd(), "static", "image", "graphs", "tsp_graph.png")
    folder_path = os.path.dirname(img_path)

    os.makedirs(folder_path, exist_ok=True)

    plt.figure(figsize=(5, 5))  # Create a new figure
    draw_tsp_solution(G, tsp_problem.interpret(result), colors, pos)
    plt.savefig(img_path, format="png", dpi=300)
    plt.close()

    return tsp_problem, result