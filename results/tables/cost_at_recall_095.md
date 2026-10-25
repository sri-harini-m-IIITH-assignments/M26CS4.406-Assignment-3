| dataset | index | config | search param | recall | build time (s) | index size (MB) | bytes/vector |
|---|---|---|---|---|---|---|---|
| glove | HNSW | M=32,efC=200 | efSearch=384 | 0.955 | 77.0 | 796 | 672 |
| glove | IVF-Flat | nlist=1024 | nprobe=256 | 0.980 | 13.9 | 483 | 408 |
| glove | IVF-PQ | nlist=1024,m=25 | nprobe=256 | 0.613 (max, <0.95) | 28.4 | 40 | 33 |
| glove | Exact (flat) | IndexFlatL2 | - | 1.000 | ~0 | 473 | 400 |
| sift | HNSW | M=16,efC=200 | efSearch=48 | 0.953 | 38.7 | 656 | 656 |
| sift | IVF-Flat | nlist=4096 | nprobe=64 | 0.974 | 78.0 | 522 | 522 |
| sift | IVF-PQ | nlist=1024,m=32 | nprobe=128 | 0.733 (max, <0.95) | 31.5 | 41 | 41 |
| sift | Exact (flat) | IndexFlatL2 | - | 1.000 | ~0 | 512 | 512 |
