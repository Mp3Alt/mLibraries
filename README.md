# mLibraries

18 TruScript libraries for TruWorlds, by Mp3. The `m` stands for Mp3.

Use the libraries you need and install their dependencies. Current source version:
**0.12.2-dev**.

| Library | Purpose | Direct dependencies | API |
| --- | --- | --- | --- |
| **mSignal** | Ordered, synchronous application events | None | [Reference](docs/api/mSignal.md) |
| **mCleanup** | Explicit ownership and disposal of resources | None | [Reference](docs/api/mCleanup.md) |
| **mAsync** | Background jobs, delays and cooperative cancellation | None | [Reference](docs/api/mAsync.md) |
| **mCommand** | Bounded command parsing and authorized dispatch | None | [Reference](docs/api/mCommand.md) |
| **mPacket** | Bounded record schemas encoded as flat native arrays | None | [Reference](docs/api/mPacket.md) |
| **mTopbar** | Shared client buttons, menus and docking | mSignal, mCleanup | [Reference](docs/api/mTopbar.md) |
| **mNet** | Bounded events and correlated request/reply | None | [Reference](docs/api/mNet.md) |
| **mState** | Local observable values, derived state and batches | mSignal, mCleanup | [Reference](docs/api/mState.md) |
| **mPlayer** | Owned player and character lifetimes | mCleanup | [Reference](docs/api/mPlayer.md) |
| **mData** | Server profile sessions, saves and lease checks | mSignal | [Reference](docs/api/mData.md) |
| **mStore** | Atomic shared records without session leases | None | [Reference](docs/api/mStore.md) |
| **mBan** | Bounded ban records, expiry and stale-removal checks | None | [Reference](docs/api/mBan.md) |
| **mMessaging** | Polled DataStore topics with bounded retained messages | mStore, mSignal | [Reference](docs/api/mMessaging.md) |
| **mSpring** | Explicitly stepped springs for numbers and vectors | None | [Reference](docs/api/mSpring.md) |
| **mBind** | Owned native instances, events and property bindings | mCleanup | [Reference](docs/api/mBind.md) |
| **mReactive** | Scoped state, keyed lists, springs and tweens | mBind, mState, mSpring | [Reference](docs/api/mReactive.md) |
| **mControls** | Native components with validated shared themes | mBind | [Reference](docs/api/mControls.md) |
| **mWidgets** | Reactive themed components with explicit input requests | mReactive, mControls | [Reference](docs/api/mWidgets.md) |

## Install

Create **Module** scripts in Creator's Asset Browser at the paths below and copy
in the matching source. Module assets are separate from the instance hierarchy.
Leave them unattached and import them from your own scripts.

| Asset Browser path | Source |
| --- | --- |
| `mLibraries/mSignal` | [mSignal.trs](packages/mSignal/src/mSignal.trs) |
| `mLibraries/mCleanup` | [mCleanup.trs](packages/mCleanup/src/mCleanup.trs) |
| `mLibraries/mAsync` | [mAsync.trs](packages/mAsync/src/mAsync.trs) |
| `mLibraries/mCommand` | [mCommand.trs](packages/mCommand/src/mCommand.trs) |
| `mLibraries/mPacket` | [mPacket.trs](packages/mPacket/src/mPacket.trs) |
| `mLibraries/mTopbar` | [mTopbar.trs](packages/mTopbar/src/mTopbar.trs) |
| `mLibraries/mNet` | [mNet.trs](packages/mNet/src/mNet.trs) |
| `mLibraries/mState` | [mState.trs](packages/mState/src/mState.trs) |
| `mLibraries/mPlayer` | [mPlayer.trs](packages/mPlayer/src/mPlayer.trs) |
| `mLibraries/mData` | [mData.trs](packages/mData/src/mData.trs) |
| `mLibraries/mSpring` | [mSpring.trs](packages/mSpring/src/mSpring.trs) |
| `mLibraries/mBind` | [mBind.trs](packages/mBind/src/mBind.trs) |
| `mLibraries/mReactive` | [mReactive.trs](packages/mReactive/src/mReactive.trs) |
| `mLibraries/mControls` | [mControls.trs](packages/mControls/src/mControls.trs) |
| `mLibraries/mWidgets` | [mWidgets.trs](packages/mWidgets/src/mWidgets.trs) |
| `mLibraries/mStore` | [mStore.trs](packages/mStore/src/mStore.trs) |
| `mLibraries/mBan` | [mBan.trs](packages/mBan/src/mBan.trs) |
| `mLibraries/mMessaging` | [mMessaging.trs](packages/mMessaging/src/mMessaging.trs) |

Import paths are absolute and omit the `.trs` extension:

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

Methods use dot calls. mSignal sends one value per Fire; use a table for several
fields. Callbacks run synchronously in connection order.

## Guides

The [getting started guide](docs/community/mLibraries-devboard-topic.md) covers
mSignal, mCleanup and mAsync. Other guides cover:

- [Packets](docs/mPacket.md) and [network events and requests](docs/mNet.md).
- [State](docs/mState.md), [player lifetimes](docs/mPlayer.md) and [springs](docs/mSpring.md).
- [Player profiles](docs/mData.md), [shared records](docs/mStore.md),
  [ban records](docs/mBan.md) and [message topics](docs/mMessaging.md).
- [Native UI](docs/ui-libraries.md) and [topbar buttons](docs/mTopbar.md).

Each module's API reference describes its arguments, ownership rules and failure
results. Release resources when their owner closes. The UI guide includes a
client gallery with themes, controls and reactive state.

## Testing and limits

These libraries target TruScript and were checked with **Creator 2026.43.7**.
Follow [the testing guide](docs/testing.md) for contract suites, native fixtures,
local storage checks and remote load tests. Record the engine version and exact
workload when checking another build.

mPacket uses flat native arrays, not a binary buffer. It promises no automatic
memory, bandwidth or speed saving. mMessaging polls DataStore topics; it does not
provide instant delivery, native pub/sub or exactly-once messages. Keep authority
on the server and do not trust a client or message as permission to change data.

Local tests do not establish production storage durability, every scheduler
interleaving, physical-device performance or hosted cross-server behavior. The
[roadmap](docs/roadmap.md) lists remaining verification work.

## Development

- `packages/` contains library source.
- `tests/` contains contracts and optional native fixtures.
- `examples/` contains the UI gallery.
- `docs/` contains guides and API references.

[mLibraries.json](mLibraries.json) maps files to Asset Browser paths and script
types. It is a repository source map, not an engine configuration file. Test
entry scripts should remain detached outside their own test sessions.

Build a source ZIP with Python 3.9 or later:

```sh
python tools/build_mlibraries.py
```

The builder writes `dist/mLibraries-0.12.2-dev.zip` and includes a file-hash
manifest. For bug reports, include your Creator version, a small reproduction,
what you expected and what happened.

## License

[MIT](LICENSE), copyright 2026 Mp3. Include the license when distributing copies
or substantial portions.
