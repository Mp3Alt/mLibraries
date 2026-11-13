# mBan

mBan validates and copies bounded ban records. It has no storage, permissions,
native player operations, clock, connections or background work. The caller owns
those decisions. The record helper can be called inside an application-owned
atomic update.

```truscript
local bans = import("/mLibraries/mBan").New({ Limit = 128 })
local records = {}
local result = bans.Set(records, {
    Id = "ban:1", UserId = 42, Name = "Player",
    ActorId = 7, Actor = "Owner", Reason = "World rules",
    IssuedAt = 1000, ExpiresAt = 0
}, 1000)
if result.Ok:
    records = result.Value
    print(bans.Get(records, 42, 1001).Reason)
```

Methods use dot calls. All calls are synchronous and do not wait. Inputs and
returned records are detached: changing a result does not mutate the input map.

## API

| Call | Result |
| --- | --- |
| `mBan.New(config)` | A stateless record helper. Config may be nil or a map containing only `Limit`, an integer from 1 to 1,024, default 128. |
| `bans.Validate(records)` | Returns true after validating the entire map, including expired records. |
| `bans.Get(records, userId, now)` | A copied active ban or nil. |
| `bans.List(records, now)` | Copied active records sorted by numeric UserId ascending. |
| `bans.Set(records, record, now)` | `{ Ok = true, Value = newRecords }` after replacing that account's ban. Expired existing entries are pruned before checking capacity. |
| `bans.Remove(records, userId, expectedId, now)` | `{ Ok = true, Value = newRecords, Removed = boolean }`. The current record ID must match expectedId. Missing or expired bans return Removed false. Output also prunes expired records. |

Malformed inputs throw the fixed string `Invalid mBan data.`. They are never
silently repaired or removed. Operational failures return
`{ Ok = false, Code, Message }`, without partial output:

- `Full`: Set would exceed the active registry capacity.
- `Expired`: the incoming Set record has already expired at now.
- `Conflict`: Set uses an ID held by another retained account, or Remove's
  expectedId differs from the stored record's ID, including an expired record.

## Record format

The root is a plain table with string keys, exactly `tostring(record.UserId)`.
Every value has exactly these eight fields. Arrays, numeric map keys, extra
fields, missing values and duplicate ban IDs across accounts are rejected.

| Field | Contract |
| --- | --- |
| `Id` | Nonempty text of at most 64 characters. Supply a fresh ID for each new ban or replacement. |
| `UserId` | Exact nonzero integer in the safe range -9,007,199,254,740,991 through 9,007,199,254,740,991. |
| `Name` | Text of at most 64 characters. Empty is allowed. |
| `ActorId` | Same numeric rules as UserId. |
| `Actor` | Text of at most 64 characters. Empty is allowed. |
| `Reason` | Text of at most 256 characters. Empty is allowed. |
| `IssuedAt` | Finite nonnegative Unix seconds. Fractional seconds are allowed. |
| `ExpiresAt` | Finite nonnegative Unix seconds. Zero means permanent; every other value must be greater than IssuedAt. |

Every text field rejects ASCII control characters, including newline, tab and
DEL. All now arguments must be finite nonnegative seconds. A temporary ban is
active only while ExpiresAt is greater than now; it is expired at equality.
Permanent zero expiry is preserved explicitly. There is no hidden time read.

Negative account IDs support Creator fixtures. An application must decide which
IDs it permits in live data. mBan does not know whether an account is an owner,
staff member or connected player, and validation does not filter user text.

## Storage and security boundary

Use these helpers inside the application's authorized UpdateAsync transform.
Validate and modify the latest stored record, then perform kicks, notices and
cross-server invalidations only after a confirmed commit. Never save a cached
whole registry over a newer value. A successful Set or Remove result only means
the copied data is valid; it does not mean a storage write occurred.

Remove's expectedId protects a newer ban from an old panel action. The caller
must issue fresh IDs when replacing a ban; reusing the old ID defeats that
protection. The library permits same-account replacement because it cannot mint
or verify globally unique IDs without owning application state.

Application caps bound work and output; they are not TruWorlds service quotas or
a measured performance claim. Get and List validate the whole bounded map. Set
and Remove additionally copy retained active records. List uses the native array
sort. No persistent writes or native enforcement happen on import or New.

## Verification

The [specification](../../tests/mBan.spec.trs) covers expiry boundaries, permanent
zero, numeric identity bounds, plain-map shapes, duplicate IDs, stale removal,
copy isolation, capacity pruning, malformed text and clocks. Native results are
recorded separately in the persistence milestone after installation and testing.
