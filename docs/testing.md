# Testing mLibraries

Use a local test world. The public modules create no instances or background work when imported; the test scripts deliberately exercise the runtime.

## Script asset layout

Install the three public modules using the root README. Add the development assets at the exact paths and types listed under `tests` in [mLibraries.json](../mLibraries.json). All test helpers except the two native entry scripts are **Module** scripts.

`mLibraries/mTestKit` is the assertion helper. The contract suites are `mLibraries/tests/mSignalSpec`, `mCleanupSpec`, and `mAsyncSpec`. `mLibraries/tests/mRunAll` imports them and returns their combined report.

## Deterministic contracts

Run this in Creator's editor command console, or through `run_truscript` with `dry_run: true`:

```truscript
return import("/mLibraries/tests/mRunAll").Run()
```

The report contains `Passed`, `Failed`, and a `Suites` array. Every suite includes its name and failure messages. The mAsync suite injects a deterministic scheduler; this checks its contract without using the native background scheduler.

These tests exercise callback ordering, reentrancy, listener mutations, one-shot delivery, cleanup failures and reuse, falsy values, cancellation and scheduler failures. They do not replace a playtest.

## Native server and client tests

1. Create a Folder named `mLibrariesTests` under `game.ScriptSystem`. Scripts attach to this folder, not to ScriptSystem itself.
2. Install `mLibraries/tests/mNativeSmoke` as a **Module** script and any additional Module test dependencies in the source map.
3. Install `mLibraries/tests/mNativeSmokeServer` as a **Server** script and attach it to `ScriptSystem/mLibrariesTests`.
4. Install `mLibraries/tests/mNativeSmokeClient` as a **Client** script and attach it to the same folder.
5. Start a local one-player playtest. Inspect the Script Console for both `server` and `client` contract and native summaries. Each must report zero failures. Read every failure line if a summary reports any.
6. Stop testing after both contexts finish. Test-created runtime instances belong to the playtest; the editor's original geometry is unchanged.

The host folder can also be created with one editor command after installing the script assets:

```truscript
local host = new Folder() { Name = "mLibrariesTests", Parent = game.ScriptSystem }
host.AttachScript("mLibraries/tests/mNativeSmokeServer")
host.AttachScript("mLibraries/tests/mNativeSmokeClient")
```

Run the setup once in a fresh test world. Later runs only need the Play control. The native entry point also invokes each lifecycle suite's yielding `RunConcurrent()` function and prints a separate named concurrency summary for each side.

The native suite uses real spawn/wait behavior, cancellation, failures after waiting, concurrent jobs, and real connection/instance cleanup. Polls are bounded by scheduler turns so failed assumptions do not create an endless assertion wait. A successful stress run samples a workload; it does not prove every possible scheduler interleaving.

For reproducibility, keep the engine version, source hashes, script layout, suite summaries and test conditions with each result. The [November 11 verification record](verification/2026-11-11.md) contains the current development baseline.
