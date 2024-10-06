import random

def calculate_pi_leibniz():
    n_terms = random.randint(10_000_000, 1_000_000_000)
    pi_approx = 0
    for i in range(n_terms):
        pi_approx += ((-1)**i) / (2*i + 1)
    return 4 * pi_approx

