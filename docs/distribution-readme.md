# mLibraries

TruScript utility libraries for TruWorlds, by Mp3. Version **0.1.0-dev**.

[Source repository and updates](https://github.com/Mp3Alt/mLibraries)

| Module | Purpose |
| --- | --- |
| [mSignal](docs/api/mSignal.md) | Ordered, synchronous application events |
| [mCleanup](docs/api/mCleanup.md) | Explicit ownership and disposal of resources |
| [mAsync](docs/api/mAsync.md) | Background jobs, delays and cooperative cancellation |

Each module is independent. Add only the modules your project uses. Implementations are original TruScript code under the [MIT license](LICENSE).

## Installation

Create the following **Module** scripts in Creator's Asset Browser, then copy the matching source into them:

| Asset Browser path | Source file |
| --- | --- |
| `mLibraries/mSignal` | [mSignal.trs](packages/mSignal/src/mSignal.trs) |
| `mLibraries/mCleanup` | [mCleanup.trs](packages/mCleanup/src/mCleanup.trs) |
| `mLibraries/mAsync` | [mAsync.trs](packages/mAsync/src/mAsync.trs) |

Use these exact names and paths, without the `.trs` extension. Module assets are separate from the instance tree. Import them with absolute paths:

```truscript
local mSignal = import("/mLibraries/mSignal")
local mCleanup = import("/mLibraries/mCleanup")
local owner = mCleanup.New()
local changed = mSignal.New()

owner.AddConnection(changed.Connect(func(value):
    print("changed: " + value)
))

changed.Fire(42)
owner.Destroy()
changed.Destroy()
```

Methods use dot syntax. `signal.Fire` sends one value; use a table for structured data. Read the module references for callback errors, dispatch order, reentrancy, cleanup, and cancellation behavior.

The development release is validated against the engine version and workloads in [the verification record](docs/verification/2026-11-11.md). It has no claim of Roblox API compatibility or measured superiority over other libraries.

## Tests

[Testing instructions](docs/testing.md) cover deterministic contract suites and native server/client checks. Tests are optional development assets, separate from the three distributable modules. `mLibraries.json` maps every file to its expected script path and type; it is this repository's source map, not a native package-manager format.

`source-manifest.json` records SHA-256 hashes for the distribution's source and documentation files.
