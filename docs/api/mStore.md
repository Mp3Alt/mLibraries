# mStore

mStore reads and atomically edits one shared persistent record. It has no lease,
autosave loop, cache or outer write retries. Use [mData](mData.md) for profiles
that need one server to own a session.

```truscript
local store = import("/mLibraries/mStore").New({
    Name = "World",
    Key = "Settings",
    Defaults = { Open = true }
}, nil)

local saved = store.Update(func(data, revision):
    data.Open = false
    return { Ok = true, Value = data }
)
if saved.Ok: print(saved.Revision)
```

Use the native adapter from a Server script. Methods use dot calls. Read and
Update may wait. Importing the module does no engine work.

## Configuration

`mStore.New(config, runtime)` returns a record handle. Invalid configuration
throws. Configuration accepts only the fields below.

| Field | Contract |
| --- | --- |
| `Name` | Required store name, 1-50 characters without control characters |
| `Key` | Required key, 1-50 characters without control characters |
| `Defaults` | Required root string-keyed record, validated and copied |
| `Version` | Integer schema version from 1 to 1,000; default 1 |
| `Validate` | Optional synchronous validator; throwing or returning false rejects data |

Validate receives a disposable deep copy. Its changes are discarded. Returning
nil or true accepts the record. It must finish quickly without waiting or doing
external work. Defaults are validated at construction; existing saved records
are not automatically merged with defaults or migrated.

Pass nil for the native `game.DataSystem.GetStore(Name)` adapter. An injected
runtime is `{ Store = backend }`, where backend supplies `GetAsync(key)` and
`UpdateAsync(key, transform)`. Keep the adapter stable for the handle's lifetime.
Construction gets the store but does not read or write a key.

## Record API

| Call | Contract |
| --- | --- |
| `store.Read(fresh)` | Returns a copied `{ Ok = true, Value, Revision }` snapshot or a structured failure. Fresh defaults to false. |
| `store.Update(transform)` | Edits the latest stored record through native UpdateAsync and confirms the returned value and revision. |
| `store.Destroy()` | Stops accepting work. Idempotent; does not read, save or cancel an already started native call. |
| `store.IsDestroyed()` | Whether Destroy has been called. It is not a save receipt. |

Read(false) uses GetAsync. In installed Creator documentation, GetAsync can serve
a server-local cached answer for four seconds. Read(true) captures a validated
snapshot inside UpdateAsync and returns nil from its native transform, cancelling
the write. It accepts the captured snapshot only if that outer call succeeds.
This is not a request-budget bypass. A missing key returns copied defaults and
revision zero without creating a stored record. [DataStore reference](https://create.truworlds.com/docs/classes/DataStore)

Update calls `transform(draft, currentRevision)`. The draft is detached. Return
one of these explicit proposal results:

```truscript
return { Ok = true, Value = draft }
return { Ok = false, Code = "Denied", Message = "This change is not allowed." }
```

An accepted proposal saves revision `currentRevision + 1`. A rejection cancels
the native write and returns its copied Code and Message. Codes must be nonempty
text of at most 32 characters; messages are text of at most 256 characters. Extra
proposal fields are rejected. Zero and false values remain valid data.

Native UpdateAsync may rerun the transform with newer data after a conflict.
Every invocation must derive its proposal from that draft, including any stored
permission check. Do not kick players, send messages, write another store, wait
or modify external state inside it. Perform those actions after a confirmed
result. Native callback replay is distinct from retrying an unconfirmed write.

One operation may run per handle. Overlap, including callback reentry, returns
Busy. Separate handles and separate servers rely on native UpdateAsync conflict
handling, not a process-local lock. No cached whole-record snapshot is written
back automatically.

## Stored format and data limits

Records use an envelope with exactly Format, Schema, Revision and Data fields.
The format is `mStore/1`; Revision is a nonnegative safe integer. Unrecognized,
malformed, older-schema or newer-schema records are rejected without replacing
their contents. Migration is deliberately separate from this API.

Data contains nil, booleans, finite numbers, strings, arrays and string-keyed
records. Native vectors, instances, functions, nonfinite numbers and cycles are
rejected. A copied Data value is capped at 4,096 nodes, 65,536 aggregate text
characters including keys, depth 16 and keys of at most 256 characters. These
are application validation bounds, not engine limits or measured throughput.

## Failure handling

Failures contain `{ Ok = false, Code, Message }` without a Value. Codes include
Busy, Closed, InvalidInput, Corrupt, NewerSchema, SchemaMismatch, InvalidProposal,
InvalidData, Transform, RevisionLimit and StoreError. Application rejections keep
their bounded caller-supplied code and message.

A StoreError means the operation was not confirmed. A write may already have
committed before its reply was lost. mStore never retries it automatically.
Reconcile with a fresh read, or use an application operation ID when duplicate
edits must be recognized. Destroy during an in-flight call can likewise return
Closed after the native write has committed. A failure does not prove rollback.
Closure during current-data or proposed-data validation rejects the candidate;
closure during validation of a saved reply refuses local confirmation. A native
write already committed before that last check is not undone.

Messages can notify other servers that a revision changed; they do not replace
the stored record or establish transaction ordering for external actions.
