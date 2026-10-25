| budget (B/vec) | setting | index | configs that fit | best recall | QPS @ 0.90 | QPS @ 0.95 |
|---|---|---|---|---|---|---|
| 1000 | control | HNSW | M=16,efC=200, M=32,efC=200, M=4,efC=200, M=8,efC=200 | 0.987 | 16,385 | 14,073 |
| 1000 | control | IVF-Flat | nlist=1024 | 1.000 | 17,295 | 15,957 |
| 1000 | control | IVF-PQ | nlist=1024,m=128, nlist=1024,m=16, nlist=1024,m=32, nlist=1024,m=64, nlist=1024,m=8 | 0.967 | 6,389 | 4,636 |
| 600 | limit | HNSW | M=4,efC=200, M=8,efC=200 | 0.987 | 9,461 | 7,419 |
| 600 | limit | IVF-Flat | nlist=1024 | 1.000 | 17,295 | 15,957 |
| 600 | limit | IVF-PQ | nlist=1024,m=128, nlist=1024,m=16, nlist=1024,m=32, nlist=1024,m=64, nlist=1024,m=8 | 0.967 | 6,389 | 4,636 |
| 150 | limit | HNSW | none (smallest is 561 B/vec) | - | - | - |
| 150 | limit | IVF-Flat | none (smallest is 523 B/vec) | - | - | - |
| 150 | limit | IVF-PQ | nlist=1024,m=128, nlist=1024,m=16, nlist=1024,m=32, nlist=1024,m=64, nlist=1024,m=8 | 0.967 | 6,389 | 4,636 |
| 50 | limit | HNSW | none (smallest is 561 B/vec) | - | - | - |
| 50 | limit | IVF-Flat | none (smallest is 523 B/vec) | - | - | - |
| 50 | limit | IVF-PQ | nlist=1024,m=16, nlist=1024,m=32, nlist=1024,m=8 | 0.594 | not reached | not reached |
