| index | n | QPS @ 0.95 | slowdown vs smallest n | search param | build time (s) | log-log slope |
|---|---|---|---|---|---|---|
| Exact (flat) | 100,000 | 289 | 1.0x | - | 0.0 | -1.06 |
| Exact (flat) | 300,000 | 85 | 3.4x | - | 0.0 | -1.06 |
| Exact (flat) | 1,000,000 | 25 | 11.4x | - | 0.0 | -1.06 |
| HNSW | 100,000 | 15,117 | 1.0x | efSearch=32 | 3.1 | -0.29 |
| HNSW | 300,000 | 10,743 | 1.4x | efSearch=48 | 10.2 | -0.29 |
| HNSW | 1,000,000 | 7,761 | 1.9x | efSearch=48 | 39.6 | -0.29 |
| IVF-Flat | 100,000 | 6,332 | 1.0x | nprobe=32 | 7.4 | -0.65 |
| IVF-Flat | 300,000 | 3,146 | 2.0x | nprobe=64 | 17.4 | -0.65 |
| IVF-Flat | 1,000,000 | 1,413 | 4.5x | nprobe=64 | 84.8 | -0.65 |
