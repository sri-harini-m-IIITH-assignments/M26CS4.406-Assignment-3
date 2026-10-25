#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [[ "${1:-}" == "--quick" ]]; then
    RESULTS_DIR="results_quick"
    QUICK_ARGS="--quick"
elif [[ $# -eq 0 ]]; then
    RESULTS_DIR="results"
    QUICK_ARGS=""
else
    echo "Usage: bash run_all.sh [--quick]" >&2
    exit 2
fi

rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

echo "Running Part 1." 
python part1/faiss_exact.py $QUICK_ARGS
echo "Part 1 done."

echo "Running Part 2:"
python part2/benchmark.py $QUICK_ARGS
python part2/analyze.py $QUICK_ARGS
echo "Part 2 done."

echo "Running Part 3:" 
python part3/scaling.py $QUICK_ARGS
echo "Part 3 done." 

echo "Running Part 4:" 
python part4/memory_limits.py $QUICK_ARGS
echo "Part 4 done." 

echo "All tasks completed successfully!"