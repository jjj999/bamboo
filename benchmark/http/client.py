
import sys
import time

import requests


URI = "http://localhost:8000/test"


def mean(arr: list) -> float:
    return sum(arr) / len(arr)


def std(arr: list) -> float:
    m = mean(arr)
    return mean([(i - m)**2 for i in arr])


def exec_benchmark(total: int, times: int):
    print("Benchmark starts...")
    print("--------------------------------")
    
    results_a_time = []
    results_means = []
    for _ in range(times):
        for __ in range(total):
            time_init = time.time()
            requests.get(URI)
            results_a_time.append(time.time() - time_init)
        results_means.append(mean(results_a_time))
    
    mean_result = mean(results_means)
    std_result = std(results_means)
        
    print(f"Total requests: {times} phases, {total} requests/phase")
    print(f"Requests per second (mean): {1 / mean_result} [/sec]")
    print(f"Seconds per request (mean): {mean_result} [sec]")
    print(f"Seconds per request (std): {std_result} [sec]")

if __name__ == "__main__":
    total = sys.argv[1]
    times = sys.argv[2]
    exec_benchmark(int(total), int(times))
