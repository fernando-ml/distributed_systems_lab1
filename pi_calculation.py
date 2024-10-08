def calculate_pi_leibniz():
    import random
    from time import perf_counter
    # Generate a random number of terms
    n_terms = random.randint(5_000_000, 40_000_000)
    print(f"Number of terms: {n_terms}")

    pi_approx = 0  # Initialize the variable to store the approximation

    start_time = perf_counter()

    # Calculate the approximation
    for i in range(n_terms):
        pi_approx += ((-1) ** i) / (2 * i + 1)

    end_time = perf_counter()

    # Calculate the final value of pi
    pi_value = 4 * pi_approx

    # Print time taken for the calculation
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    return pi_value