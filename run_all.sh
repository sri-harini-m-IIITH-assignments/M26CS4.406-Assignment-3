#!/usr/bin/env bash
set -e

mkdir -p results

echo "Running Part 1." 
python part1/faiss_exact.py
echo "Part 1 done."

echo "Running Part 2:"
python part2/benchmark.py
python part2/analyze.py
echo "Part 2 done."

echo "Running Part 3:" 
python part3/scaling.py
echo "Part 3 done." 

echo "Running Part 4:" 
python part4/memory_limits.py
echo "Part 4 done." 

echo "All tasks completed successfully!"