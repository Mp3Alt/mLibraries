# Testing mLibraries

Use a separate local Creator test world. The source map lists each file's Asset
Browser path and script type. Modules stay unattached; native entry scripts run
only when attached to a test host.

These fixtures were developed against **Creator 2026.43.7**. Record the source
revision, Creator version, client count and workload with every new result.
Do not treat an earlier pass as acceptance of a changed source file.

## Contract suites

Install the Module test assets from [mLibraries.json](../mLibraries.json), then
run this in the editor command console:

```truscript
return import("/mLibraries/tests/mRunAll").Run()
```

The result contains `Passed`, `Failed` and a `Suites` array. Each suite includes
its own failures. Individual specifications also expose `Run()`:

```truscript
return import("/mLibraries/tests/mStoreSpec").Run()
```

The deterministic suites use injected adapters for scheduling, storage and
transport. They cover bounds, failures, ownership, cancellation and copied data
without relying on a live service. They do not measure native I/O or prove every
scheduler interleaving.

## Native scheduling and UI

Creator's atomic editor runner cannot wait, spawn tasks or subscribe to native
signals. Run those checks through real Server or Client scripts in Play.

Create one test Folder under ScriptSystem. Attach only the entries for the phase
you are running, once each. Use a fresh two-player local playtest for paired
workloads and inspect the server and both clients' results.

| Fixture | Use |
| --- | --- |
| mNativeSmokeServer + mNativeSmokeClient | Native scheduling and core concurrency checks |
| mUiNativeServer + mUiNativeClient | UI instances, bindings, input handlers, motion and cleanup |
| mTopbarNativeClient | Topbar geometry, selection, menus, docks and lifetime checks |
| mPacketNativeServer + mPacketNativeClient | Codec integration through native remotes |
| mNetNativeServer + mNetNativeClient | Native event/request/reply behavior |
| mPlayerNativeServer + mPlayerNativeClient | Player observation and character replacement |
| mStateNativeClient | Native state/concurrency checks |
| mLibraryAuditNativeServer + mLibraryAuditNativeClient | Focused public-library regressions |

The names above are asset names under `mLibraries/tests/`. The paired UI
collector stores receipts beneath `world/mUiNativeReports`. Topbar and smoke
fixtures also print their summaries to the script console. A passing result on
one client does not establish the other client's result.

Run the optional [UI gallery](../examples/mUiGallery.client.trs) separately from
the test entries. It shows themes, reactive state, dropdown layering and window
behavior. Observe actual pointer input and useful viewport sizes separately from
handler-driven tests. Inactive or tiny Creator viewports cannot establish
rendered visibility or physical-device behavior.

## Storage fixtures

Keep **Live data in playtests** off and use only the fixtures' dedicated local
namespaces. Run storage fixtures alone and inspect their source before use.

`mDataNativeServer` exercises profile loading, save/release and local restart
persistence. `mSharedStoreNativeServer` exercises shared records and polling
helpers. Follow their phase settings and printed instructions. Local data can
survive stopping Play, so a restart is different from a clean first run.

Do not substitute production store names or delete unrelated records. A local
restart does not certify cloud durability, real shutdown handling or concurrent
published servers.

## Load measurements

- `mLibraryLoadBench` and its Server entry run bounded CPU-side cases with
  synchronous injected adapters. Warmup and calibration are separate from the
  measured samples; preserve operation counts, sample order and raw times.
- `mNetLoadServer` and `mNetLoadClient` run a paced two-client native transport
  workload. It checks successful requests, denied routes, invalid payloads,
  personal burst limits and malformed-traffic isolation.
- `mTopbarLoadBench.Run()` is called from a local Client script. It observes two
  docked icons over real frames and checks owned instances after teardown.

Run timed workloads separately. The CPU runner writes receipts to the dedicated local `mLibrariesBench` store,
under its configured `server-before` or `server-after` key. The independent native
remote fixture uses `mPerformance20261112` and its `remote-before` or `remote-after`
key. Reporting and preparation happen outside measured library operations.

`host.time()` has documented millisecond precision. Batch small operations,
repeat trials and retain zero/short batches rather than inventing precision.
Elapsed wall time includes scheduling and collection. Counted fields or JSON
length are not wire bytes, and native instance counts are not heap bytes.

Record slower results and long frames too. An injected backend result is not a
native storage result. Paced local traffic is not maximum throughput or WAN
latency. Real hosted cross-server checks require distinct nonempty ServerIds in
an isolated test environment; they remain separate from Creator multiplayer.

## Cleanup

Stop Play and explicitly detach the test entries and gallery. Verify the test
host's `GetScriptCount()` is zero before removing temporary script assets.
Source deletion alone does not prove that an attachment disappeared. Check
saved source/types and attachment GUIDs when preserving a test milestone.

The [original foundation verification](verification/2026-11-11.md) records the
0.1.0-dev sources. Its results belong to that revision, not later modules.
