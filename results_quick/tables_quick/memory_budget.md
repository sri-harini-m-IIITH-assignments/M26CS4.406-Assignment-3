| budget (B/vec) | setting | index | configs that fit | best recall | QPS @ 0.90 | QPS @ 0.95 |
|---|---|---|---|---|---|---|
| 1000 | control | HNSW | M=16,efC=100, M=32,efC=100, M=4,efC=100, M=8,efC=100 | 0.983 | 38,956 | 36,442 |
| 1000 | control | IVF-Flat | nlist=256 | 0.996 | 49,676 | 41,722 |
| 1000 | control | IVF-PQ | nlist=256,m=128, nlist=256,m=16, nlist=256,m=32, nlist=256,m=64, nlist=256,m=8 | 0.936 | 11,430 | not reached |
| 600 | limit | HNSW | M=4,efC=100, M=8,efC=100 | 0.978 | 26,208 | 20,344 |
| 600 | limit | IVF-Flat | nlist=256 | 0.996 | 49,676 | 41,722 |
| 600 | limit | IVF-PQ | nlist=256,m=128, nlist=256,m=16, nlist=256,m=32, nlist=256,m=64, nlist=256,m=8 | 0.936 | 11,430 | not reached |
| 150 | limit | HNSW | none (smallest is 561 B/vec) | - | - | - |
| 150 | limit | IVF-Flat | none (smallest is 523 B/vec) | - | - | - |
| 150 | limit | IVF-PQ | nlist=256,m=128, nlist=256,m=16, nlist=256,m=32, nlist=256,m=64, nlist=256,m=8 | 0.936 | 11,430 | not reached |
| 50 | limit | HNSW | none (smallest is 561 B/vec) | - | - | - |
| 50 | limit | IVF-Flat | none (smallest is 523 B/vec) | - | - | - |
| 50 | limit | IVF-PQ | nlist=256,m=16, nlist=256,m=32, nlist=256,m=8 | 0.562 | not reached | not reached |
