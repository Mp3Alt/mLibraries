# mLibraries roadmap

Current source version: **0.12.2-dev**. The package has 18 reusable TruScript
libraries. The [README](../README.md) lists their purposes and dependencies.

The core utilities, commands, networking, state, player lifetimes, data helpers,
springs, topbar and native UI stack are implemented. Their contracts, examples
and optional test fixtures live beside the source.

## Next checks

- Run storage and messaging tests in an isolated published environment with
  distinct server IDs. Creator multiplayer alone is not a cross-server test.
- Check real server shutdown and storage failures separately from local restart tests.
- Extend longer-session memory and sustained-load measurements.
- Test supported physical devices and additional Creator versions.
- Recheck topbar geometry and motion when the native HUD changes.
- Keep adding small regression cases for reproduced failures.

Keep changes simple and preserve public contracts. Record source versions,
workloads and raw measurements before claiming a speed or memory improvement.
A passing correctness test is not a performance result.
