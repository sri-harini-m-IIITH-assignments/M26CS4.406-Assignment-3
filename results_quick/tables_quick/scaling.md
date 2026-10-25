| index | n | QPS @ 0.95 | slowdown vs smallest n | search param | build time (s) | log-log slope |
|---|---|---|---|---|---|---|
| Exact (flat) | 25,000 | 2,001 | 1.0x | - | 0.0 | -1.67 |
| Exact (flat) | 50,000 | 527 | 3.8x | - | 0.0 | -1.67 |
| Exact (flat) | 100,000 | 199 | 10.1x | - | 0.0 | -1.67 |
| HNSW | 25,000 | 27,555 | 1.0x | efSearch=32 | 1.5 | -0.34 |
| HNSW | 50,000 | 23,475 | 1.2x | efSearch=32 | 1.7 | -0.34 |
| HNSW | 100,000 | 17,154 | 1.6x | efSearch=48 | 2.4 | -0.34 |
| IVF-Flat | 25,000 | 20,289 | 1.0x | nprobe=32 | 2.1 | -0.80 |
| IVF-Flat | 50,000 | 12,166 | 1.7x | nprobe=32 | 3.9 | -0.80 |
| IVF-Flat | 100,000 | 6,738 | 3.0x | nprobe=32 | 7.3 | -0.80 |
