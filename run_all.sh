#!/usr/bin/env bash
set -e

mkdir -p results

echo "Running Part 1:" 
python part1/faiss_exact.py

echo "Running Part 2:"
python part2/benchmark.py
python part2/analyze.py

echo "All tasks completed successfully!"