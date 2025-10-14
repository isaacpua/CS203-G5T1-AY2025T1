def run_exact_cover(subsets):
    from qiskit_optimization.applications import ExactCover
    from qap.utils.optimisation_utils import qaoa_result

    exact_cover_problem = ExactCover(subsets) 
    qp = exact_cover_problem.to_quadratic_program()
    
    sampler_type = 'simulation'
    result = qaoa_result(qp, sampler_type)

    return exact_cover_problem, result