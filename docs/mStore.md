# Using mStore

mStore owns one shared persistent record. It reads the latest stored data for
each update and returns a confirmed value and revision. It does not hold a
profile lease or save cached snapshots on a timer. Use [mData](mData.md) when one
server must own a player's profile session.

## Install and update

Create a **Module** asset at `mLibraries/mStore` from
[mStore.trs](../packages/mStore/src/mStore.trs). Leave it unattached. The native
adapter runs from your own **Server** script.

```truscript
local shared = import("/mLibraries/mStore").New({
    Name = "mStoreExample",
    Key = "visits",
    Defaults = { Visits = 0 }
}, nil)

local changed = shared.Update(func(data, revision):
    data.Visits += 1
    return { Ok = true, Value = data }
)
if changed.Ok:
    print("visits: " + changed.Value.Visits)
else:
    print("update unconfirmed: " + changed.Code)
```

Use a dedicated test namespace while developing and keep **Live data in
playtests** off. A confirmed update is persisted immediately; there is no later
Save call. Importing the module does no engine work, and New does not read or
write a key.

## Read deliberately

`shared.Read(false)` uses native GetAsync, including its documented four-second
server-local cache. `shared.Read(true)` uses a cancelling UpdateAsync transform
to read fresh data without writing a new record. Both return copied Value and
Revision fields on success. A missing key returns copied defaults at revision
zero and remains absent from storage.

Fresh reads can wait and consume service capacity. Do not call them per frame.
A recent cached value is useful for display, but it is not a substitute for a
current authorization check. When installing a snapshot, compare its revision
with your current revision so an older reply cannot roll local state backwards.

## Keep transactions narrow

Update receives a detached draft and current revision. Return an accepted
`{ Ok = true, Value = draft }` proposal, or reject with
`{ Ok = false, Code = "Denied", Message = "This change is not allowed." }`.
The native transform can run again after a competing write, so derive each
proposal from that invocation's draft. Stored roles and target protection should
be checked there too.

Do not kick players, publish messages, call another store or wait inside the
transform. Those effects belong after a confirmed result. Keep related checks
and changes in the same record when they must use one atomic document. There is
no cross-key transaction here.

## Handle uncertainty

A failed acknowledgement can follow a successful write. mStore returns a
failure without a Value and never retries the mutation automatically. Reconcile
with a fresh read. If an application must recognize repeated operations, include
its own stable operation ID in the stored transaction.

Destroy closes the handle to new work. It does not cancel a native write that
already started or prove that no commit occurred. A second overlapping read or
update of the same handle returns Busy rather than adding an unbounded queue.

The [API reference](api/mStore.md) lists proposal rules, copying limits, schema
handling and failures. Corrupt or newer-schema data is never replaced with
defaults. There is no implicit migration. See [testing](testing.md) for local
storage fixtures and [the verification record](verification/libraries-0.12.2.md)
for the recorded scope. Those checks are not a general cloud durability or
throughput guarantee.
