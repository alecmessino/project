"""Independent version stamps. Protocol (method), Collector (engineering), and Benchmark
Dataset (data) evolve separately, so each is tracked on its own axis.

    Protocol            — the validation ladder + safeguards + stopping rules (methodology)
    Collector           — the live data-collection pipeline (engineering)
    Benchmark Dataset   — the released/curated historical data (date-versioned; grows)
"""

PROTOCOL_VERSION = "1.0"        # protocol/protocol.md — bump on a new safeguard / rung change
COLLECTOR_VERSION = "1.1"       # live_engine + sources/* — 1.1 = FanDuel market-inPlay fix + status capture
BENCHMARK_DATASET = "2026.06"   # the frozen Paper-1 dataset (June 2026); live panels accrue toward v2

VERSIONS = {
    "protocol": PROTOCOL_VERSION,
    "collector": COLLECTOR_VERSION,
    "benchmark_dataset": BENCHMARK_DATASET,
}
