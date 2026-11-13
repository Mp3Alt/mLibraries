# Using mBan

mBan handles ban records and their expiry. It does not store data, grant
permissions, filter text or kick players. The application owns those operations.
Use it inside your own storage and permission flow.

## Install and check

Create a **Module** asset at `mLibraries/mBan` from
[mBan.trs](../packages/mBan/src/mBan.trs). Leave it unattached. The module has no
dependencies or background work.

```truscript
local bans = import("/mLibraries/mBan").New({ Limit = 128 })
local records = {}
local result = bans.Set(records, {
    Id = "ban:1:42", UserId = 42, Name = "Example",
    ActorId = 7, Actor = "Owner", Reason = "World rules",
    IssuedAt = 1000, ExpiresAt = 0
}, 1000)
if result.Ok:
    records = result.Value
    print(bans.Get(records, 42, 1001).Reason)
```

This example only constructs valid data. A successful Set result is not a save
receipt. Get returns a copied active record or nil, and List returns copied
active records ordered by UserId. Zero expiry means permanent; otherwise a ban
expires when now reaches ExpiresAt.

## Persist through the application's policy

Use [mStore](mStore.md) to edit the authoritative record. Authorize the actor and
target against that fresh draft, then call Set or Remove for its Bans field.
Save the returned map in the accepted proposal. Perform a kick or publish a
revision hint only after the storage write is confirmed.

Capture the Unix timestamp outside the native UpdateAsync transform and reuse
it if the transform runs again. Give every new or replacement ban a fresh ID.
For a ban inside one shared policy record, its next committed revision and
target UserId can form that ID. The fixed ID in the small example is not an ID
generator for repeated production operations.

Remove requires the expected ban ID:

```truscript
local removed = bans.Remove(records, 42, "ban:1:42", 1002)
if removed.Ok: records = removed.Value
```

If another operation replaced the ban, Remove returns Conflict and preserves
the newer record. Reusing an old ID defeats that protection. Set and Remove
also prune expired records from their copied output; Get and List do not issue
cleanup writes.

## Keep enforcement on the server

Always check the engine-supplied actor, configured owners, target hierarchy and
current session in trusted server code. Validate and filter user-provided text
before the transaction, then recheck permission after any wait. A client row or
message cannot authorize a ban.

Malformed records throw instead of being silently repaired. Storage outages
must remain failures rather than becoming empty ban lists. The
[API reference](api/mBan.md) lists exact fields, limits and operational failures.
See [testing](testing.md) for helper contracts and local storage fixtures.
Production enforcement and hosted-server behavior need their own checks.
