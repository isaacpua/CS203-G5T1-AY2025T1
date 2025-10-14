from fastmcp import FastMCP
import os, base64
#QAP imports, add back data_analysis when deploying
from qap.tools.clique_solver import run_clique
from qap.tools.exact_cover_solver import run_exact_cover
from qap.tools.graph_partition_solver import run_graph_partition
from qap.tools.knapsack_solver import run_knapsack
from qap.tools.max_cut_solver import run_max_cut
from qap.tools.number_partition_solver import run_number_partition
from qap.tools.stable_set_solver import run_stable_set
from qap.tools.tsp_solver import run_tsp
from qap.tools.vertex_cover_solver import run_vertex_cover

mcp = FastMCP("QAP MCP Server")

#QAP Tools
@mcp.tool()
def solve_clique(nodes: int, edges: list[list[int, int]], size: int) -> dict[str, str]:
    """
    Solve the Clique problem for a given graph defined by nodes and edges.

    Clique Problem:
    Given an undirected graph, find a subset of nodes with a specified size 
    (or the maximum size) such that the subgraph induced by these nodes is complete 
    (i.e., every pair of nodes is connected by an edge).

    Args:
        nodes: The number of nodes in the graph.
        edges: A list of lists representing edges between nodes, 
            e.g., [[0, 1], [1, 2], [2, 0]].
        size: (Optional) The desired size of the clique to find. If not specified, 
            find the maximum clique.

    Returns:
        solution: A list of nodes forming the clique.
        time: The time taken to compute the solution in seconds.
    """
    if not isinstance(edges, list) or not all(isinstance(e, list) and len(e) == 2 for e in edges):
        raise ValueError("Invalid edges format. Expected list of 2-element lists.")
    
    if not isinstance(nodes, int) or not nodes > 0:
        raise ValueError("Invalid nodes value. Expected positive integer.")
    
    if size is not None and (not isinstance(size, int) or not size > 0):
        raise ValueError("Invalid size format. Expected positive integer.")
    
    clique_problem, result = run_clique(nodes, edges, size)
    return ({
        'solution': clique_problem.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })    

@mcp.tool()
def solve_exact_cover(subsets: list[list[int]]) -> dict[str, str]:
    """
    Solve the Exact Cover problem for a given collection of subsets.

    Exact Cover Problem:
    Given a collection of subsets of items, find a subcollection such that 
    each item is covered exactly once (no overlaps or omissions).

    Args:
        subsets: A list of lists representing subsets of items, 
                e.g., [[1, 2], [2, 3], [3, 4]].

    Returns:
        solution: A list of subsets that form an exact cover of the items.
        time: The time taken to compute the solution in seconds.
    """
    if subsets is None:
        raise ValueError("Missing required fields: subsets")
    
    if not isinstance(subsets, list) or not all(isinstance(v, list) and all(isinstance(i, int) for i in v) for v in subsets):
        raise ValueError ("Invalid subsets format. Expected a list of integers. ")  
    
    exact_cover_problem, result = run_exact_cover(subsets)

    return ({
        'solution': exact_cover_problem.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })    

    
@mcp.tool()
def solve_graph_partition(nodes: int, edges: list[list[int, int]]) -> dict[str, str]:
    """
    Solve the Graph Partition problem for a given graph defined by nodes and edges.

    Graph Partition Problem:
    Given an undirected graph, partition the set of nodes into two subsets 
    such that the number of edges between the two subsets is minimized. 
    The algorithm aims to produce two subsets that are as close in size as possible, 
    but perfect balance is not required.

    Args:
        nodes: The number of nodes in the graph.
        edges: A list of lists representing edges between nodes, 
            e.g., [[0, 1], [1, 2], [2, 0]].

    Returns:
        solution: A list containing two lists of node indices, each representing one partition.
                For example, [[0, 2], [1, 3]].
        time: The time taken to compute the solution in seconds.
    """
    if not isinstance(edges, list) or not all(isinstance(e, list) and len(e) == 2 for e in edges):
        raise ValueError("Invalid edges format. Expected list of 2-element lists.")
    
    if not isinstance(nodes, int) or not nodes > 0:
        raise ValueError("Invalid nodes value. Expected positive integer.")
    
    graph_partition_problem, result = run_graph_partition(nodes, edges)

    return ({
        'solution': graph_partition_problem.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })    

@mcp.tool()
def solve_knapsack(values: list[int], weights: list[int], max_weight: int) -> dict[str, str]:
    """
    Solve the Knapsack problem given a list of item values and weights.

    Knapsack Problem:
    Given a set of items, each with a value and a weight, find the subset of items 
    such that the total weight is within the maximum capacity and the total value is maximized.

    Args:
        values: A list of positive integers representing the value of each item, 
                e.g., [60, 100, 120].
        weights: A list of positive integers representing the weight of each item, 
                e.g., [10, 20, 30].
        max_weight: A positive integer representing the maximum allowed total weight.

    Returns:
        solution: A list of indices representing the selected items.
        time: The time taken to compute the solution in seconds.
    """
    if values is None or weights is None or max_weight is None:
        raise ValueError("Missing required fields: values, weights, max_weight")

    if not isinstance(values, list) or not all(isinstance(v, int) and v > 0 for v in values):
        raise ValueError("Invalid values format. Expected a list with positive integers.")

    if not isinstance(weights, list) or not all(isinstance(w, int) and w > 0 for w in weights):
        raise ValueError("Invalid weights format. Expected a list with positive integers.")

    if not isinstance(max_weight, int) or max_weight < 0:
        raise ValueError("Invalid max_weight format. Expected a positive integer.")

    knapsack_problem, result = run_knapsack(values, weights, max_weight)

    return ({
        'solution': knapsack_problem.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })

@mcp.tool()
def solve_max_cut(nodes: int, edges: list[list[int, int, int]]) -> dict[str, str]:
    """
    Solve the Max-Cut problem for a given graph defined by nodes and weighted edges.

    Max-Cut Problem:
    Given an undirected graph, partition the set of nodes into two subsets such that 
    the total weight of the edges crossing between the two subsets is maximized.

    Args:
        nodes: The number of nodes in the graph.
        edges: A list of lists representing weighted edges between nodes, 
            e.g., [[0, 1, 2], [1, 2, 3], [2, 0, 1]], where the third value is the edge weight.

    Returns:
        solution: A list containing two lists of node indices, each representing one partition.
                For example, [[0, 2], [1]] means nodes 0 and 2 are in one subset, and node 1 is in the other.
        time: The time taken to compute the solution in seconds.
    """
    if not isinstance(edges, list) or not all(isinstance(e, list) and len(e)==3 for e in edges):
        raise ValueError("Invalid edges format. Expected lists with 3 elements.")
    
    if not isinstance(nodes, int) or nodes <= 0:
        raise ValueError("Invalid nodes format. Expected positive integer. ")
    
    maxcut, result = run_max_cut(nodes, edges)
    
    return ({
        'solution': maxcut.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })

@mcp.tool()
def solve_number_partition(number_set: list[int]) -> dict[str, str]:
    """
    Solve the Number Partition problem for a given multiset of positive integers.

    Number Partition Problem:
    Given a multiset of positive integers, find a partition into two subsets 
    such that the sum of the numbers in each subset is equal or as close as possible.

    Args:
        number_set: A list of positive integers, e.g., [3, 1, 1, 2, 2, 1].

    Returns:
        solution: A list containing two lists of integers, each representing a subset in the partition.
        time: The time taken to compute the solution in seconds.
    """
    if number_set is None:
        raise ValueError("Missing required field: number_set")

    if not isinstance(number_set, list) or not all(isinstance(v, int) for v in number_set):
        raise ValueError("Invalid number_set format. Expected a list of integers.")

    number_partion_problem, result = run_number_partition(number_set)

    return ({
        'solution': number_partion_problem.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })


@mcp.tool()
def solve_stable_set(nodes: int, edges: list[list[int, int]]) -> dict[str, str]:
    """
    Solve the Stable Set Problem for a given graph defined by nodes and edges.

    Stable Set Problem:
    Given an undirected graph, find the largest possible subset of nodes such that 
    no two nodes in the subset are connected by an edge.

    Args:
        nodes: The number of nodes in the graph.
        edges: A list of lists representing edges between nodes, 
            e.g., [[0, 1], [1, 2], [2, 0]].

    Returns:
        solution: A set of nodes that form a stable set (also known as an independent set) in the graph.
        time: The time taken to compute the solution in seconds.
    """
    if not isinstance(edges, list) or not all(isinstance(e, list) and len(e) == 2 for e in edges):
        raise ValueError("Invalid edges format. Expected list of 2-element lists.")
    
    if not isinstance(nodes, int) or not nodes > 0:
        raise ValueError("Invalid nodes value. Expected positive integer.")
    
    stable_set_problem, result = run_stable_set(nodes, edges)

    return ({
        'solution': stable_set_problem.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })

@mcp.tool()
def solve_tsp(nodes: int, edges: list[list[int, int, int]]) -> dict[str, str]:
    """
    Solve the Travelling Salesman Problem (TSP) for a given graph defined by nodes and weighted edges.

    Travelling Salesman Problem:
    Given a graph, find a route with the minimum total distance such that 
    the route visits each city (node) exactly once and returns to the starting city.

    Args:
        nodes: The number of nodes in the graph.
        edges: A list of lists representing weighted edges between nodes, 
            e.g. [[0, 1, 1], [1, 2, 2], [2, 0, 3]], where the third value is the weight.

    Returns:
        solution: A list of nodes representing the shortest route that visits all nodes once and returns to the start.
        time: The time taken to compute the solution in seconds.
    """

    if not isinstance(edges, list) or not all(isinstance(e, list) and len(e)==3 for e in edges):
        raise ValueError("Invalid edges format. Expected lists with 3 elements.")
    
    if not isinstance(nodes, int) or nodes <= 0:
        raise ValueError("Invalid nodes format. Expected positive integer. ")

    tsp_problem, result = run_tsp(nodes, edges)

    return ({
        'solution': tsp_problem.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })

@mcp.tool()
def solve_vertex_cover(nodes: int, edges: list[list[int, int]]) -> dict[str, str]:
    """
    Solve the Vertex Cover problem for a given graph defined by nodes and edges.

    Vertex Cover Problem:
    Given an undirected graph, find the smallest possible subset of nodes such that 
    every edge in the graph has at least one of its endpoints in that subset.

    Args:
        nodes: The number of nodes in the graph.
        edges: A list of lists representing edges between nodes, 
            e.g., [[0, 1], [1, 2], [2, 0]].

    Returns:
        solution: A set of nodes that form a vertex cover for the graph.
        time: The time taken to compute the solution in seconds.
    """

    if not isinstance(edges, list) or not all(isinstance(e, list) and len(e) == 2 for e in edges):
        raise ValueError("Invalid edges format. Expected list of 2-element lists.")

    if not isinstance(nodes, int) or nodes <= 0:
        raise ValueError("Invalid nodes value. Expected positive integer.")
    
    vertexcover, result = run_vertex_cover(nodes, edges)

    return({
        'solution': vertexcover.interpret(result),
        'time': result.min_eigen_solver_result.optimizer_time
    })

@mcp.tool()
def get_graph_image_solution(problem: str) -> dict:
    """
    Get the solution image for a solved graph problem.

    Args:
        problem: Problem name (e.g., "vertex_cover", "tsp")

    Returns:
        type: 'image'
        mime_type: 'image/png'
        data: Base64-encoded PNG
    """
    img_path = os.path.join(os.getcwd(), "static", "image", "graphs", f"{problem}.png")
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Image for problem '{problem}' not found at {img_path}")
    
    with open(img_path, "rb") as img_file:
        img_data = img_file.read()
    base64_img = base64.b64encode(img_data).decode('utf-8')

    return {
        "type": "image",
        "mime_type": "image/png",
        "data": base64_img
    }

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=server_port,
        path="/qap"
    )