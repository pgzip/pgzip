#!/usr/bin/env python
import pgzip
import gzip
import pathlib
import statistics
import sys
import timeit

DATA = pathlib.Path(sys.argv[1]).read_bytes()

SIZES = [1000000, 10000000, 100000000]


def benchmark(bench_string, number=3, repetitions=10):
    for size in SIZES:
        data = DATA[:size]
        compressed_data = pgzip.compress(data)
        timeit_kwargs = dict(globals=dict(**locals(), **globals()), number=number)
        results = [
            timeit.timeit(bench_string, **timeit_kwargs) for _ in range(repetitions)
        ]
        average = statistics.mean(results)
        print(
            f"Data size {size}: {round(average * (1_000_000 / number),2)} microseconds average"
        )


if __name__ == "__main__":
    # pgzip
    print("pgzip compression")
    benchmark("pgzip.compress(data)")
    print()
    print("pgzip decompression")
    benchmark("pgzip.decompress(compressed_data)")
    print()
    print()
    # gzip
    print("gzip compression")
    benchmark("gzip.compress(data)")
    print()
    print("gzip decompression")
    benchmark("gzip.decompress(compressed_data)")
