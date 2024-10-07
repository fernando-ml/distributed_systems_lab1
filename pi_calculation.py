def calculate_pi_leibniz():
    import random
    from time import perf_counter
    # Generate a random number of terms
    n_terms = random.randint(10_000_000, 100_000_000)  # Reduced upper limit for practical runtime in a distributed scenario
    print(f"Number of terms: {n_terms}")

    pi_approx = 0  # Initialize the variable to store the approximation

    start_time = perf_counter()

    # Calculate the approximation, updating progress periodically
    for i in range(n_terms):
        pi_approx += ((-1) ** i) / (2 * i + 1)  # Calculate the approximation
        
        # Update job progress every 1% of the total terms
        # if (i + 1) % (n_terms // 10) == 0:
        #     worker.job_progress = (i + 1) / n_terms * 100
        #     print(f"Progress: {worker.job_progress:.2f}%")  # Print progress for monitoring
    
    end_time = perf_counter()

    # Calculate the final value of pi
    pi_value = 4 * pi_approx

    # Print time taken for the calculation
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    # Set the progress to 100% as the task is complete
    # worker.job_progress = 100

    return pi_value

def calculate_pi_leibniz_chunked(n_terms, chunk_size=1_000_000):
    """Calculates pi using the Leibniz formula in chunks."""
    from time import perf_counter
    pi_approx = 0  # Initialize the variable to store the approximation

    start_time = perf_counter()

    # Calculate the approximation in chunks
    for chunk_start in range(0, n_terms, chunk_size):
        for i in range(chunk_start, min(chunk_start + chunk_size, n_terms)):
            pi_approx += ((-1) ** i) / (2 * i + 1)  # Calculate the approximation
        
        # After each chunk, print progress and return partial result
        yield pi_approx

    end_time = perf_counter()
    print(f"Total time taken: {end_time - start_time:.2f} seconds")

    # Return the final value of pi
    return 4 * pi_approx
