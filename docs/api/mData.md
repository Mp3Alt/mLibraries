# mData

mData owns server profile sessions over an UpdateAsync backend. It combines copied profile data, lease tokens, fenced generations, explicit autosave steps and release receipts. It depends on [mSignal](mSignal.md). It is not a universal no-loss guarantee or a replacement for application permissions and transaction rules.

```truscript
local mData = import("/mLibraries/mData")
local data = mData.New({ Name = "Progress", Defaults = { Coins = 0 } }, nil)
local loaded = data.Load("example-profile")
if loaded.Ok:
    loaded.Profile.Update(func(value): value.Coins += 1)
    local saved = loaded.Profile.Save()
```

Use the default adapter from a Server script. Methods use dot calls. Load, Save, Release, Step and Close can wait.

## Configuration

`mData.New(config, runtime)` returns a service. Runtime may be nil for the native server adapter. Invalid configuration throws.

| Field | Default | Contract |
| --- | --- | --- |
| `Name` | Required | Store name, 1-50 characters without control characters |
| `Defaults` | Required | Root data record, validated and copied |
| `Version` | `1` | Integer schema version from 1 to 1,000 |
| `Migrate` | `nil` | Optional synchronous `Migrate(data, fromVersion, toVersion)` |
| `LeaseSeconds` | `120` | Finite duration from 30 to 600 seconds |
| `AutosaveSeconds` | `30` | Finite duration at least 5; `AutosaveSeconds + 5` must be less than half the lease |
| `Retries` | `3` | Integer from 1 to 5; outer backend attempts per operation |
| `MaxProfiles` | `128` | Integer tracked-profile limit from 1 to 1,024, including loading entries |

The injected runtime contains `Store.UpdateAsync(key, transform)`, `Clock()`, `Wait(seconds)`, `Spawn(work)` and a nonempty `SessionId` of at most 128 characters. Clock supplies finite wall-clock seconds from 0 to 1e15. Keep the adapter stable for the service's lifetime. The default uses `game.DataSystem.GetStore(Name)`, `host.time`, `wait`, `spawn` and the server ID. Creator's empty server ID gets a clock-based prefix; individual session tokens also include a module counter.

Outer retries use increasing waits of 0.25 seconds per failed attempt number. They are not a platform request budget. The backend's own conflict retry policy is separate.

## Service API

| Call | Contract |
| --- | --- |
| `data.Load(key)` | Claims a key and returns `{ Ok = true, Profile = profile }`, or `{ Ok = false, Code, Message }` without a profile. Keys are nonempty strings of at most 50 characters without control characters. |
| `data.Step(maximum)` | Saves due profiles in round-robin order. Default maximum is 4; accepted values are integers 1-16. Returns `{ Ok = true, Value = [{ Key, Result }, ...] }` or a service failure. |
| `data.Close(timeout)` | Starts closing, rejects new loads and releases through at most four workers. Default timeout is 25 seconds, with a range of 0-25. Returns a progress report; it can return `Busy` before closing starts if an Update/migration callback is active. |
| `data.GetCount()` | Number of tracked entries, including loading or unfinished release work. |
| `data.IsClosed()` | Whether closing has started, not whether every release succeeded. |

Close reports contain `Ok`, `Pending`, `Released` and `Failed`. Repeated Close calls return the current progress snapshot rather than starting another release pass. A timeout stops waiting; it does not cancel an in-flight storage call or stop workers from processing later entries. Failed operations remain failures in the report. A caller must not interpret `IsClosed()` alone as a successful save.

Step has no hidden loop. Initial autosave deadlines include 0-4 seconds of jitter. Successful saves renew the lease and schedule the next autosave. Inspect each returned Result; a successful Step wrapper does not mean every individual save succeeded.

## Profile API

| Call | Contract |
| --- | --- |
| `profile.Get()` | Returns a detached deep copy of active data. |
| `profile.Update(transform)` | Copies current data, runs synchronous `transform(draft)`, validates/copies the result, then publishes one revision. A non-nil return replaces the draft. Throws on failure; no partial draft is published. |
| `profile.Save()` | Persists an owned snapshot and renews the lease; returns `{ Ok = true, Value = nil }` or a structured failure. |
| `profile.Release()` | Saves an owned snapshot, clears its lease and closes the local profile on success. Returns the same result shape as Save. |
| `profile.IsActive()` | Checks local phase, service closure and lease expiry. Can retire an expired profile. |
| `profile.GetStatus()` | Returns copied `Key`, `State`, `ExpiresAt` and `Dirty` fields. |
| `profile.Closed` | mSignal sending the closure reason after local invalidation. Observer failures are isolated. |

Update and migration callbacks must finish quickly and must not wait. Call Close after those callbacks finish; attempting it inside one returns Busy. Save and Update have separate claims: an Update accepted during an in-flight save remains a newer dirty revision after that older snapshot is acknowledged. Overlapping I/O returns Busy.

GetStatus describes local bookkeeping. A phase can still read Active while the service is closing; use IsActive for admission. Dirty compares the current revision to the acknowledged saved revision, and a closed profile's false Dirty value does not prove a successful save. Update alone is not durable until a save/release is confirmed.

## Data and schema rules

Data must be a root string-keyed record containing nil, booleans, finite numbers, text, arrays and other string-keyed records. Native vectors, instances, functions, nonfinite numbers and cycles are rejected. Library validation caps one copied value at 4,096 nodes, 65,536 total text characters including keys, depth 16 and keys of at most 256 characters. These are mData limits, not measured engine or network budgets.

Defaults fill missing record fields recursively. Existing false and zero values remain. Arrays are preserved rather than merged with default arrays. A migration runs after the lease claim, outside the UpdateAsync transform. It may mutate its detached data or return a replacement record. Failure releases the claim where possible and does not replace the stored data with defaults.

Stored records use a private `mData/1` envelope with Schema, Fence, Data, Lock and Commit metadata. Raw records from another writer, malformed envelopes and newer schema versions are rejected without overwriting their data. Do not write these keys independently through SetAsync or another unfenced writer.

## Ownership, errors and limits

Each save/release checks the stored token, fenced generation and lease expiry inside UpdateAsync. A release operation carries a commit receipt so a retry can recognize a release whose acknowledgement was lost. A lost or expired owner cannot keep writing through its old handle. There is no force-steal option.

Failures use codes such as `InvalidKey`, `Closed`, `Busy`, `AlreadyLoaded`, `Capacity`, `Locked`, `Corrupt`, `NewerSchema`, `StoreError`, `Migration`, `Inactive`, `Expired` and `Lost`. Missing or invalid local arguments can throw. Do not fabricate a profile or save defaults after a failed Load.

A failed release retains local data for retry while ownership is valid. If all Load acknowledgements are lost, a remote claim can remain until its lease expires even though no profile was returned. Storage outages, process termination, clock assumptions and unconfirmed writes remain limits. Four close workers and retry caps bound application scheduling, not underlying cloud latency.

The native contract is checked against installed documentation bundle `2026.43.7+876eaeb2`: [DataStore](https://create.truworlds.com/docs/classes/DataStore), [DataSystem](https://create.truworlds.com/docs/classes/DataSystem) and [DataModel](https://create.truworlds.com/docs/classes/DataModel). Installed docs explain that UpdateAsync can rerun its nonyielding transform, nil cancels without writing, and ShuttingDown handlers can wait. The public website supplies less detail. No live-cloud throughput, budget or durability benchmark is claimed.

## Verification

The injected-runtime specification covers profile preparation, ownership,
validation, failures and retirement. The optional local Server fixture checks
save/release and playtest restart persistence with the native adapter. See
[testing](../testing.md) and the [verification record](../verification/libraries-0.12.2.md).
These checks do not certify live-cloud durability or real server shutdown.
