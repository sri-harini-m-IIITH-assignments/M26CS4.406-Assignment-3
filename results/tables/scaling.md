| index | n | QPS @ 0.95 | slowdown vs smallest n | search param | build time (s) | log-log slope |
|---|---|---|---|---|---|---|
| Exact (flat) | 100,000 | 154 | 1.0x | - | 0.0 | -1.07 |
| Exact (flat) | 300,000 | 45 | 3.4x | - | 0.0 | -1.07 |
| Exact (flat) | 1,000,000 | 13 | 11.8x | - | 0.0 | -1.07 |
| HNSW | 100,000 | 8,816 | 1.0x | efSearch=32 | 10.5 | -0.36 |
| HNSW | 300,000 | 5,166 | 1.7x | efSearch=48 | 26.8 | -0.36 |
| HNSW | 1,000,000 | 3,823 | 2.3x | efSearch=48 | 71.9 | -0.36 |
| IVF-Flat | 100,000 | 3,149 | 1.0x | nprobe=32 | 20.5 | -0.66 |
| IVF-Flat | 300,000 | 1,771 | 1.8x | nprobe=64 | 48.3 | -0.66 |
| IVF-Flat | 1,000,000 | 689 | 4.6x | nprobe=64 | 254.7 | -0.66 |
