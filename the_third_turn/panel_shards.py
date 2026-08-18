#!/usr/bin/env python3
"""Shard the large append-only panels so git can store them, and put them back together.

WHY (2026-08-18 postmortem, E-026 corrected). GitHub hard-rejects any single file over
100 MiB (104,857,600 bytes). `book_panel.jsonl` grew into that wall: the last checkpoint
that landed, on 08-14, left it at 104,857,591 bytes — nine bytes short. Every checkpoint
after that pushed it over the limit, the push was rejected, and because the checkpoint
piped everything to /dev/null the collector went on reporting healthy while persisting
nothing for 79 hours.

The fix keeps the analysis contract intact. Every script still reads
`output/book_panel.jsonl`; git never stores that file. Git stores fixed-size shards,
`book_panel.part00.jsonl` and so on, and the runner reassembles the whole file after
checkout. Sharding is by LINE COUNT, not by date: round-tripping is then exact by
construction, with no assumption that rows are chronologically ordered.

A useful side effect is that appends only ever touch the final shard, so each checkpoint
commits a small delta instead of restating 100 MiB.

    python3 the_third_turn/panel_shards.py split       # monolith -> shards
    python3 the_third_turn/panel_shards.py reassemble  # shards -> monolith
    python3 the_third_turn/panel_shards.py verify      # round-trip is byte-identical
"""

from __future__ import annotations

import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "output"

# Files big enough to need it. Kept well under the 100 MiB ceiling so a shard never
# approaches the limit even if rows get longer.
SHARDED = ("book_panel.jsonl", "provenance_probe.jsonl", "game_state_panel.jsonl")
LINES_PER_SHARD = 200_000
# A line cap alone is not enough: provenance rows are far longer than quote rows, so
# 200k of them is 65 MiB. Cap bytes too, and cut on whichever limit is reached first.
BYTES_PER_SHARD = 32 * 1024 * 1024


def shard_paths(name: str) -> list[Path]:
    stem = name[: -len(".jsonl")]
    return sorted(OUT.glob(f"{stem}.part*.jsonl"))


def split(name: str) -> int:
    src = OUT / name
    if not src.exists():
        return 0
    stem = name[: -len(".jsonl")]
    for old in shard_paths(name):
        old.unlink()
    n = idx = nbytes = 0
    buf: list[str] = []
    with src.open() as fh:
        for line in fh:
            buf.append(line)
            n += 1
            nbytes += len(line.encode())
            if len(buf) >= LINES_PER_SHARD or nbytes >= BYTES_PER_SHARD:
                (OUT / f"{stem}.part{idx:02d}.jsonl").write_text("".join(buf))
                buf, idx, nbytes = [], idx + 1, 0
    # always write the tail, even when empty, so a shard set exists for an empty file
    if buf or idx == 0:
        (OUT / f"{stem}.part{idx:02d}.jsonl").write_text("".join(buf))
    return n


def reassemble(name: str) -> int:
    parts = shard_paths(name)
    if not parts:
        return 0
    dst = OUT / name
    n = 0
    with dst.open("w") as out:
        for p in parts:
            text = p.read_text()
            n += text.count("\n")
            out.write(text)
    return n


def verify(name: str) -> bool:
    """Round-trip must be byte-identical. Anything less and we are corrupting the panel."""
    src = OUT / name
    if not src.exists():
        print(f"  {name}: absent, skipped")
        return True
    before = src.read_bytes()
    split(name)
    reassemble(name)
    after = src.read_bytes()
    ok = before == after
    print(f"  {name}: {len(before):,} bytes, {len(shard_paths(name))} shards, "
          f"round-trip {'IDENTICAL' if ok else 'MISMATCH'}")
    return ok


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "split":
        for f in SHARDED:
            print(f"  split {f}: {split(f):,} lines -> {len(shard_paths(f))} shards")
    elif cmd == "reassemble":
        for f in SHARDED:
            print(f"  reassemble {f}: {reassemble(f):,} lines")
    else:
        ok = all(verify(f) for f in SHARDED)
        if not ok:
            print("ROUND-TRIP FAILED — do not commit shards")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
