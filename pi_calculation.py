import random
from time import perf_counter

def calculate_pi_leibniz(worker):
    # Generate a random number of terms
    n_terms = random.randint(10_000_000, 100_000_000)  # Reduced upper limit for practical runtime in a distributed scenario
    print(f"Number of terms: {n_terms}")

    pi_approx = 0  # Initialize the variable to store the approximation

    start_time = perf_counter()

    # Calculate the approximation, updating progress periodically
    for i in range(n_terms):
        pi_approx += ((-1) ** i) / (2 * i + 1)  # Calculate the approximation
        
        # Update job progress every 1% of the total terms
        if (i + 1) % (n_terms // 10) == 0:
            worker.job_progress = (i + 1) / n_terms * 100
            print(f"Progress: {worker.job_progress:.2f}%")  # Print progress for monitoring
    
    end_time = perf_counter()

    # Calculate the final value of pi
    pi_value = 4 * pi_approx

    # Print time taken for the calculation
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    # Set the progress to 100% as the task is complete
    worker.job_progress = 100

    return pi_value