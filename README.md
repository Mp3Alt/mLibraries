# mLibraries

Three independent TruScript utility modules for TruWorlds, by Mp3.

| Module | Purpose | API |
| --- | --- | --- |
| **mSignal** | Ordered, synchronous application events | [Reference](docs/api/mSignal.md) |
| **mCleanup** | Explicit ownership and disposal of resources | [Reference](docs/api/mCleanup.md) |
| **mAsync** | Background jobs, delays and cooperative cancellation | [Reference](docs/api/mAsync.md) |

The `m` prefix stands for Mp3. Each module is original TruScript code and can be used on its own.

**0.1.0-dev** is a development prerelease tested with Creator **2026.43.7**. On both a local server and client, 52 contract tests, 9 native checks and 4 concurrency checks passed. See [the verification record](docs/verification/2026-11-11.md) for the workloads and limits of those results.

[Download the source ZIP](https://github.com/Mp3Alt/mLibraries/releases/download/v0.1.0-dev/mLibraries-0.1.0-dev.zip) or [browse the repository](https://github.com/Mp3Alt/mLibraries).

## Install

Create **Module** scripts in Creator's Asset Browser at the paths below and copy in the matching source. These are script assets, separate from the instance hierarchy. Use the paths without the `.trs` extension.

| Asset Browser path | Source |
| --- | --- |
| `mLibraries/mSignal` | [mSignal.trs](packages/mSignal/src/mSignal.trs) |
| `mLibraries/mCleanup` | [mCleanup.trs](packages/mCleanup/src/mCleanup.trs) |
| `mLibraries/mAsync` | [mAsync.trs](packages/mAsync/src/mAsync.trs) |

Import a module with an absolute Asset Browser path:

```truscript
local mSignal = import("/mLibraries/mSignal")
local changed = mSignal.New()

local connection = changed.Connect(func(value):
    print("changed: " + value)
)

changed.Fire(42)
connection.Disconnect()
changed.Destroy()
```

Methods use dot calls. `signal.Fire` sends one value; use a table for structured payloads. Callbacks run synchronously in connection order. The API references explain errors, reentrancy and cancellation. The [getting started guide](docs/community/mLibraries-devboard-topic.md) has examples for all three modules.

## Tests and development

Follow [the testing instructions](docs/testing.md) to run the contract suites and native server/client checks. The public modules are in `packages/`; development tests are in `tests/`.

[mLibraries.json](mLibraries.json) maps source files to their script asset paths and types. It is a repository source map, not a native Creator configuration file.

Rebuild the source ZIP from a checkout with Python 3.9 or later:

```sh
python tools/build_mlibraries.py
```

The build writes `dist/mLibraries-0.1.0-dev.zip` and includes a manifest of source and documentation hashes.

For bug reports, include the Creator version, a small reproduction, the expected result and the actual result. Proposed API changes should include a use case and tests. See [the roadmap](docs/roadmap.md) for possible next modules.

## License

[MIT](LICENSE), copyright 2026 Mp3. Include the license when distributing copies or substantial portions.
