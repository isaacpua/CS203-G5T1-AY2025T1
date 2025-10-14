from qiskit_ibm_runtime import QiskitRuntimeService
import os

def get_qiskit_backend(backend = None):
    api_key = os.getenv("API_KEY")
    service = QiskitRuntimeService(channel = 'ibm_quantum', token=api_key)
    if backend == None:
        backend = service.least_busy(simulator = False, operational = True)
    else:
        backend = backend
        
    return backend
    
