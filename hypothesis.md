# Hypothesis

## Part 3: Scaling 

As the dataset scales from 100K to 1M vectors ($10\times$), the computational cost of reaching a recall of 0.95 will increase across all index types. Because exact search compares each query against every vector, its cost will scale linearly, causing queries/second to drop by a factor of 10. For HNSW and IVF, search complexity is not linear. While the cost will also increase due to the increase in vectors, it will not increase to the same extent as exact search.

## Part 4: Memory limits

Under a strict memory budget, neither search method will be able to reach a recall of 0.95. IVF-PQ's recall will drop due to aggressive compression, while HNSW will drop due to graph and routing errors. Both search methods will cause a decrease in recall and search speed (queries/second).