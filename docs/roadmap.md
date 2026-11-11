# mLibraries roadmap

mLibraries starts with events, resource cleanup and cooperative jobs. Each module has its own source, API documentation and tests.

## Foundation

1. [mSignal](api/mSignal.md): ordered synchronous events, connections, one-shot listeners and teardown.
2. [mCleanup](api/mCleanup.md): callback, connection and instance cleanup in reverse registration order.
3. [mAsync](api/mAsync.md): background jobs, delays and cooperative cancellation, with an injected scheduler for deterministic tests.

The **0.1.0-dev** baseline passed 52 contract tests, 9 native checks and 4 concurrency checks on both server and client in Creator **2026.43.7**. The [verification record](verification/2026-11-11.md) describes the workloads; [testing instructions](testing.md) explain how to repeat them.

## Work before a stable release

- Repeat installation in a fresh project using only the published package and instructions.
- Test long-running use and resource cleanup in more projects and supported Creator versions.
- Keep failure, cancellation and reentrancy tests with each API change.
- Record the engine version, hardware and workload for any performance measurements.

Document breaking changes and migration steps when an API changes.

## Possible next modules

- **Promise composition:** chaining and small combinators, with explicit settlement and cancellation rules.
- **Data helpers:** result records, collection operations and runtime validation where they remove repeated application code.
- **Networking helpers:** server-side validation and request handling after testing remote direction, serialization and failure behavior.
- **UI and state utilities:** small observers or components drawn from working examples.

Choose the next module from concrete use cases and bug reports. Keep each package usable without importing unrelated systems.
