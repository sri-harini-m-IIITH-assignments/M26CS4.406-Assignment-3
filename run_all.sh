#!/usr/bin/env bash
set -e

mkdir -p results

echo "=== Running Unit Tests ==="
python part1/faiss_exact.py --test

echo "Running in Quick Mode..."
python part1/faiss_exact.py --quick

echo "All tasks completed successfully! Results saved to results/results_part1.csv. Run the full"