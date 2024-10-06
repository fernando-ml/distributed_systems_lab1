import random
from time import perf_counter

def calculate_pi_leibniz():
    n_terms = random.randint(10_000_000, 1_000_000_000)
    print(n_terms)
    
    pi_approx = 0
    
    start_time = perf_counter()
    for i in range(n_terms):
        pi_approx += ((-1)**i) / (2*i + 1)
        
    end_time = perf_counter()
    
    print(f"Time taken: {end_time - start_time}")
    return 4 * pi_approx

