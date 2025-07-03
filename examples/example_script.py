import time
import numpy as np

if __name__ == "__main__":
    # Create two large matrices
    N = 2000
    A = np.random.rand(N, N)
    B = np.random.rand(N, N)

    # Time the dot product
    start = time.perf_counter()
    C = np.dot(A, B)
    end = time.perf_counter()

    # Print only the elapsed time
    print(end - start)
