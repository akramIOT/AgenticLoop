import random
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from merge_sort import merge_sort


def bubble_sort(arr: list) -> list:
    a = arr.copy()
    n = len(a)
    for i in range(n):
        for j in range(0, n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a


def benchmark():
    sizes = [100, 500, 1000]
    print("size,merge_ms,bubble_ms,merge_faster")
    for n in sizes:
        arr = [random.randint(0, n) for _ in range(n)]

        t0 = time.perf_counter()
        merge_sort(arr)
        t1 = time.perf_counter()
        merge_ms = (t1 - t0) * 1000

        t0 = time.perf_counter()
        bubble_sort(arr)
        t1 = time.perf_counter()
        bubble_ms = (t1 - t0) * 1000

        faster = bubble_ms / merge_ms if merge_ms > 0 else 0
        print(f"{n},{merge_ms:.3f},{bubble_ms:.3f},{faster:.1f}x")


if __name__ == "__main__":
    benchmark()
