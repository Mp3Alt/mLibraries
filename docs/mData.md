# Using mData

mData keeps server-owned profile data behind a lease and fenced generation. Start with local test storage or the injected test backend. The default adapter uses native server storage; the library does not turn profile values into replicated client state.

## Install and load

Create **Module** assets `mLibraries/mSignal` and `mLibraries/mData`, using [mSignal.trs](../packages/mSignal/src/mSignal.trs) and [mData.trs](../packages/mData/src/mData.trs). Leave them unattached. Run the native adapter from your own **Server** script.

This example uses a dedicated test store and key:

```truscript
local mData = import("/mLibraries/mData")
local data = mData.New({
    Name = "mDataExample",
    Defaults = { Coins = 0, Items = [], Settings = { Music = true } }
}, nil)

local loaded = data.Load("example-profile")
if not loaded.Ok:
    print("profile unavailable: " + loaded.Code)
    return

local profile = loaded.Profile
profile.Update(func(value):
    value.Coins += 1
)
local saved = profile.Save()
if not saved.Ok: print("save failed: " + saved.Code)
```

For player data, derive the key from the actual engine player's UserId on the server. Keep only successfully loaded profiles in your application's registry. A failed load has no profile and must not lead to saving a new default record over existing progress.

Get returns a detached copy. Change data through Update, which works on a draft and validates before publishing. Retaining or editing that draft afterward cannot change the profile. Update and migration callbacks must not yield; use separate save/release calls for storage work.

## Drive autosaves and release on leave

Step is explicit. There is no hidden background autosave task:

```truscript
spawn(func():
    while not data.IsClosed():
        wait(1)
        if data.IsClosed(): break
        local stepped = data.Step(4)
        if stepped.Ok:
            for item in stepped.Value:
                if not item.Result.Ok: print("autosave failed: " + item.Result.Code)
)
```

In your player loader, put each successfully loaded profile in a server registry, keyed by the account ID string. The leave handler removes that registry entry and starts yielding release work separately:

```truscript
local active = {}
# Your loader assigns active[tostring(player.UserId)] after a successful Load.

game.Players.PlayerRemoved.Connect(func(player):
    local key = tostring(player.UserId)
    local leaving = active[key]
    table.remove(active, key)
    if leaving != nil:
        spawn(func():
            local released = leaving.Release()
            if not released.Ok: print("release failed: " + released.Code)
        )
)

game.ShuttingDown.Connect(func():
    local report = data.Close(25)
    if not report.Ok: print("profile close did not complete successfully")
)
```

Call Close after your synchronous Update/migration callbacks have finished. Busy means closing did not begin; the caller must retry after that callback ends. Close starts up to four workers and waits up to the supplied timeout. A timeout does not cancel native storage requests, and workers can continue to later profiles. Inspect Pending and Failed rather than treating IsClosed as a completion flag. Repeated Close calls report progress without starting new work.

The local acceptance run verified explicit native Close, including the default adapter. Creator Stop produced no observable ShuttingDown callback/output. It therefore does not verify the shutdown handler above on a real server, and it is not evidence of an engine defect.

Do not put `profile.Release` directly into an mCleanup teardown callback: Release can wait, while mCleanup requires synchronous callbacks. Coordinate release through your server lifecycle. Runtime loss or a forcibly stopped script cannot promise successful storage completion.

## Schema changes

Keep one store/key namespace under mData ownership. Its records include private session and schema metadata. Raw data from another writer and newer schemas are rejected rather than replaced.

When increasing Version, provide a synchronous migration:

```truscript
local data = mData.New({
    Name = "PlayerProgress",
    Defaults = { Coins = 0, Settings = { Music = true } },
    Version = 2,
    Migrate = func(value, previous, next_version):
        if previous < 2 and value.Settings == nil: value.Settings = { Music = true }
        return value
}, nil)
```

A migration receives detached data after the session claim and outside UpdateAsync's transform. It may mutate that data or return a replacement record. Defaults then fill missing record fields. False and zero remain intact, and arrays are not merged. A failed migration does not save defaults over the old record.

## Failure handling and tests

Ownership loss or lease expiry closes the local handle. Observe `profile.Closed` to stop application use, and keep server permission checks separate from storage ownership. A failed Save/Release does not prove whether a remote commit occurred. Release receipts recover a supported lost-acknowledgement case; exhausting Load acknowledgements can leave its claim locked until expiry.

The [API reference](api/mData.md) lists configuration, data limits, result codes and Close reports. These library limits are not engine throughput budgets. No universal no-loss, cross-server fairness or performance claim is made.

Install [mData.spec.trs](../tests/mData.spec.trs) as Module asset `mLibraries/tests/mDataSpec` with `mLibraries/mTestKit`. Its injected backend tests failures without cloud access:

```truscript
return import("/mLibraries/tests/mDataSpec").Run()
```

The optional local fixture covers restart persistence and explicit Close through the native adapter. See [testing](testing.md) and the [verification record](verification/libraries-0.12.2.md) for the recorded scope. Local checks do not certify live-cloud storage, multiple published servers or a real shutdown callback.
