def calculate_pi_leibniz():
    import random
    from time import perf_counter
    # generate a random number of terms so that the pi calculation can take a variable amount of time
    n_terms = random.randint(10_000_000, 32_000_000)
    print(f"Number of terms: {n_terms}")

    pi_approx = 0  # initialize the variable to store the approximation

    start_time = perf_counter()

    # calculate the approximation
    for i in range(n_terms):
        pi_approx += ((-1) ** i) / (2 * i + 1)

    end_time = perf_counter()

    pi_value = 4 * pi_approx

    print(f"Time taken: {end_time - start_time:.2f} seconds")

    return pi_value
