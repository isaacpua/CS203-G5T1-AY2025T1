def run_number_partition(number_set):
    from qiskit_optimization.applications import NumberPartition
    from qap.utils.optimisation_utils import qaoa_result

    number_partition_problem = NumberPartition(number_set) 
    qp = number_partition_problem.to_quadratic_program()
    
    sampler_type = 'simulation'
    result = qaoa_result(qp, sampler_type)

    return number_partition_problem, result