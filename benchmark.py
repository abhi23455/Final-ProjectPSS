# python benchmark.py

import requests
import time

BASE_URL = "http://localhost:8000/api"
ITERATIONS = 50


def benchmark_endpoint(url, label):
    """Mengukur rata-rata response time sebuah endpoint."""
    times = []

    for i in range(ITERATIONS):
        start = time.time()
        response = requests.get(url)
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\n{label}")
    print(f"  Iterasi   : {ITERATIONS}x")
    print(f"  Rata-rata : {avg_time:.2f} ms")
    print(f"  Minimum   : {min_time:.2f} ms")
    print(f"  Maksimum  : {max_time:.2f} ms")

    return avg_time


if __name__ == "__main__":
    print("=" * 50)
    print("BENCHMARK: Simple LMS API Performance")
    print("=" * 50)
    print("\nPastikan Redis sudah jalan sebelum benchmark!")
    print("Jalankan: docker-compose exec redis redis-cli MONITOR")
    print("untuk melihat cache hit/miss secara real-time\n")

    avg1 = benchmark_endpoint(f"{BASE_URL}/courses/", "GET /courses/ (list)")
    avg2 = benchmark_endpoint(f"{BASE_URL}/courses/1", "GET /courses/1 (detail)")
    avg3 = benchmark_endpoint(f"{BASE_URL}/courses/popular/", "GET /courses/popular/ (leaderboard)")

    print("\n" + "=" * 50)
    print("RINGKASAN")
    print("=" * 50)
    print(f"List courses  : {avg1:.2f} ms rata-rata")
    print(f"Detail course : {avg2:.2f} ms rata-rata")
    print(f"Popular       : {avg3:.2f} ms rata-rata")
    print("\nRequest ke-1 akan lambat (cache miss → query DB)")
    print("Request ke-2 dst akan cepat (cache hit → dari Redis)")