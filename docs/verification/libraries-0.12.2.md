# 0.12.2 library checks

Tested with TruWorlds Creator 2026.43.7 and installed documentation bundle
2026.43.7+876eaeb2 on November 12, 2026. This checkout contains 18 libraries.
[The JSON record](libraries-0.12.2.json) contains the results and source hashes.

## Current checks

The library-only runner passed **397 contracts with zero failures across 17
suites** in a fresh atomic editor run. The separate topbar suite needs a real
client and is not part of that total. The 27 library CPU workload cases also
passed a one-iteration smoke run. Those short smoke times are not performance
benchmarks. The filtered runner and workload module were evaluated without
changing the saved world or installing temporary assets.

All 18 production source bodies are unchanged from the locally tested inputs.
The production files retain their original copyright and MIT notices.

## Native remote workload

The same mNet and mPacket source and native fixtures completed a previous
two-client Creator run with 34 phase receipts and no failures:

- All 1,152 steady requests succeeded.
- The server verified 1,176 ordinary handler calls, including warmup and the
  healthy-client isolation probe.
- 32 denied requests reached neither the denied validator nor its handler.
- 32 invalid packets were rejected.
- Each client received four replies from its separate Burst 4 endpoint; the
  other eight requests timed out as expected after being dropped.
- One client sent 96 malformed messages while the other completed eight
  healthy requests.

This was paced local traffic through actual RemoteEvents. It was not a maximum
throughput, WAN, wire-byte or hosted cross-server test. The fixtures and
[testing guide](../testing.md) describe the bounds and local-storage requirement.

## Other native checks and limits

Earlier local checks passed 91 public UI checks and 59 topbar checks on each
of two clients. These are separate source-specific native and concurrency
workloads, not additional cases in the 397-contract editor result. Their
production library bodies are unchanged in this checkout. UI geometry checks
need an active usable viewport.

The optional load scripts expose their raw elapsed samples and operation
counts. Storage and transport inside the CPU-only workload are injected local
adapters. Native allocation bytes, physical-device performance, real server
shutdown and published cross-server behavior are not established by those
adapters. There is no universal speed or memory-saving claim for mPacket.

The original three-library release has its own historical
[verification record](2026-11-11.md). Its counts and source hashes remain tied
to that earlier release.
