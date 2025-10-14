from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import SPSA
from qiskit.primitives import Sampler as Sampler_Simulation
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qap.utils.qiskit_backend import get_qiskit_backend
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_optimization.converters import QuadraticProgramToQubo
import networkx as nx
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def draw_graph(G, colors, pos):
    default_axes = plt.axes(frameon=True)
    nx.draw_networkx(G, node_color=colors, node_size=600, alpha=0.8, ax=default_axes, pos=pos)
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=edge_labels)

def draw_tsp_solution(G, order, colors, pos):
    G2 = nx.DiGraph()
    G2.add_nodes_from(G)
    n = len(order)
    for i in range(n):
        j = (i + 1) % n
        G2.add_edge(order[i], order[j], weight=G[order[i]][order[j]]["weight"])
    default_axes = plt.axes(frameon=True)
    nx.draw_networkx(
        G2, node_color=colors, edge_color="b", node_size=600, alpha=0.8, ax=default_axes, pos=pos
    )
    edge_labels = nx.get_edge_attributes(G2, "weight")
    nx.draw_networkx_edge_labels(G2, pos, font_color="b", edge_labels=edge_labels)

def create_graph(nodes, edges):
    G = nx.Graph()
    G.add_nodes_from(np.arange(0, nodes, 1))
    # edge_weights is a list of tuples: (i,j,weight) where (i,j) is the edge
    if len(edges[0]) == 3:
        G.add_weighted_edges_from(edges)
    else:
        G.add_edges_from(edges)

    return G

def qp2qubo(qp):
    qp2qubo = QuadraticProgramToQubo()
    qubo = qp2qubo.convert(qp)
    return qubo

# Currently, sampler_type can only run simulations, as V2 primitives are currently not supported by qiskit-optimization
def qaoa_result(qubo, sampler_type, backend = None):
    if sampler_type == 'simulation':
        sampler = Sampler_Simulation()
    elif sampler_type == 'real':
        backend = get_qiskit_backend()
        sampler = Sampler(backend)
    shots = 1000
    mes = QAOA(sampler=sampler, optimizer=SPSA(),reps = 1)
    meo = MinimumEigenOptimizer(min_eigen_solver=mes)
    result = meo.solve(qubo)
    return result

"""
create function to find out num_qubits used
# measure qubits 
qubo = qp2qubo(qp)
op, offset = qubo.to_ising()
print(f"num qubits:{op.num_qubits}, {offset}\n")
print(op)
"""