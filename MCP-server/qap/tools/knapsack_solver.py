def run_knapsack(values, weights, max_weight):
    from qiskit_optimization.applications import Knapsack
    from qap.utils.optimisation_utils import qaoa_result

    knapsack_problem = Knapsack(values=values, weights=weights, max_weight=max_weight) 
    qp = knapsack_problem.to_quadratic_program()
    
    sampler_type = 'simulation'
    result = qaoa_result(qp, sampler_type)

    return knapsack_problem, result