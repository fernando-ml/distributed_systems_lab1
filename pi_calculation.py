import random
from time import perf_counter

def calculate_pi_leibniz(job_progress):
    
    n_terms = random.randint(10_000_000, 1_000_000_000) #generate a random number of terms
    print(n_terms)
    
    pi_approx = 0 #initialize the variable to store the approximation
    
    start_time = perf_counter()
    for i in range(n_terms):
        pi_approx += ((-1)**i) / (2*i + 1) #calculate the approximation
        
        if (i+1) % (n_terms // 100) == 0: #update the job progress every 1% of the total terms
            job_progress = (i+1) / n_terms * 100
        
    end_time = perf_counter()
    
    print(f"Time taken: {end_time - start_time}")
    
    pi_value = 4 * pi_approx
    
    return pi_value
