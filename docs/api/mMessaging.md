# mMessaging

mMessaging provides bounded server messages through a **polled DataStore topic**.
It depends on [mStore](mStore.md) and [mSignal](mSignal.md). It does not wrap a
native publish/subscribe service: none was found in the inspected TruWorlds
2026.43.7 documentation.

```truscript
local messages = import("/mLibraries/mMessaging").New({ Topic = "admin" }, nil)
local connection = messages.Subscribe(func(message):
    if message.Data.Kind == "PolicyChanged":
        print("Read current policy from its authoritative store.")
)
messages.Step() # Establish the receiver cursor before expecting new messages.
local published = messages.Publish({ Kind = "PolicyChanged" })
if not published.Ok: print("publication unconfirmed: " + published.Code)
```

Drive `Step()` from your server's existing timer or scheduler. There is no hidden
loop, background task or native event subscription. Step and Publish can wait;
call them from a Server script. Disconnect your listener or destroy the channel
when its owner closes.

## Configuration

`mMessaging.New(config, runtime)` returns a channel. Construction performs no
storage read or write. Invalid configuration throws; unknown fields are rejected.

| Field | Default | Contract |
| --- | --- | --- |
| `Topic` | Required | 1 to 32 characters, beginning with a letter; letters, digits, underscore and hyphen only |
| `Name` | `mMessaging1` | Native store name, validated by mStore |
| `PollSeconds` | `10` | Finite interval from 5 to 300 seconds |
| `Capacity` | `32` | Integer maximum retained message count from 1 to 64 |
| `MaxAge` | `120` | Finite maximum message age from 10 to 3,600 seconds |

The key is `topic:` followed by Topic. Keep the same topic configuration across
publishers and receivers for predictable retention. Capacity is an upper bound:
large messages can evict more history to stay within mStore's aggregate data
bounds. Age pruning happens during publication; receivers skip expired entries
without issuing a cleanup write.

The optional runtime is `{ Store, Clock }`. Store is an mStore backend adapter
with `GetAsync(key)` and `UpdateAsync(key, transform)`; nil uses native storage.
Clock returns finite Unix seconds from zero to `1e15 - 3600`; the default is
`host.time`. A backwards clock is rejected until it catches up with the last
accepted reading. Remote server clocks are not assumed synchronized.

## API

| Call | Contract |
| --- | --- |
| `channel.Publish(data)` | Validates and copies a plain-data record, atomically appends a message, prunes retained history and returns a confirmed copied message in `Value` |
| `channel.Subscribe(handler)` | Returns an mSignal connection. Each handler receives its own detached `{ Sequence, SentAt, Data }` copy |
| `channel.Step()` | Performs a due poll, processes retained new messages and returns a progress report; an early call is a successful no-op |
| `channel.Destroy()` | Closes the channel, disconnects its listeners and closes its owned mStore handle; idempotent |
| `channel.IsDestroyed()` | Whether destruction has begun |

Publish and Step return `{ Ok = true, Value = ... }` or
`{ Ok = false, Code, Message }`. Invalid subscriptions throw. At most 64 local
subscribers are allowed; disconnecting one frees that slot.

Publish returns a message with a monotonically increasing topic Sequence, the
publisher's wall-clock SentAt and copied Data. Sequence is limited to `1e15`.
The timestamp is captured before the atomic update and reused if the native
transform runs again after a conflict. No notification callbacks or other effects
run inside the transform.

The **first successful Step establishes the cursor at the latest sequence and
delivers no retained history**. Subscribe before driving Step. A subscriber added
later receives messages processed after registration, rather than its own replay.
Publications from the same channel can also be received by its subscribers.

Subsequent polls process messages in sequence order. A cached older reply does
not rewind the cursor. The cursor advances before listener delivery, so a failed
listener is not retried. Listener failures are counted and later listeners still
run. Subscribe, disconnect and destroy during delivery follow mSignal ordering;
destruction stops further callbacks and message dispatch.

## Step reports

| Field | Meaning |
| --- | --- |
| `Initialized` | This poll established the initial cursor |
| `Noop` | The polling deadline has not arrived; no storage read occurred |
| `Stale` | Storage returned an older sequence than the receiver already observed |
| `Delivered` | New, unexpired messages processed by the local signal, including a message with no listeners |
| `Missed` | Sequence positions absent from the retained history since the cursor |
| `Expired` | Newly observed retained entries skipped for age |
| `ListenerErrors` | Total listener failures collected during this poll |
| `Stopped` | A callback destroyed the channel during delivery |
| `Sequence` | The current local cursor; nil until a successful initial poll |

A failed or malformed read leaves the cursor unchanged. A due read consumes the
polling interval even on failure, preventing repeated calls from hammering storage.
A second overlapping Step or Publish of the same kind returns Busy. mStore also
serializes the shared handle, so an overlap between reading and publication can
return Busy. There is no queued retry.

## Message and storage bounds

Data must be a root record containing only nil, booleans, finite numbers, strings,
arrays and string-keyed records. Every message is limited to 128 value nodes,
2,048 total text characters including keys, depth four, and keys of 1 to 64
characters. Cycles, object identities as keys, functions, instances and native
vector/color objects are rejected. Zero and false remain intact.

The retained topic also stays within mStore's 4,096-node and 65,536-text-character
limits. Up to 64 small messages can fit; a topic of maximum-size messages retains
fewer. These are library policies, not platform throughput or memory measurements.
Do not write the channel key independently with SetAsync or another envelope.

## Delivery and security limits

Polling is not instant delivery. Native GetAsync has a four-second cache, and a
receiver adds its polling interval, storage latency and scheduling delays. A
receiver that sleeps too long can miss evicted or expired history. A new receiver
deliberately skips existing history. This API offers no exactly-once, guaranteed
delivery, acknowledgement, request/reply or persistent consumer cursor.

Publication has **no automatic mutation retry**. A failed acknowledgement can
follow a successful commit. An explicit later Publish is a new publication and
can duplicate the application's intended event. Include application identifiers
when consumers need additional deduplication. Destroy does not cancel a native
write that is already in flight and cannot prove that it did not commit.

Use messages as invalidation hints and keep authoritative state in a separate
record. For bans and permissions, reread current stored policy and retain a
bounded fallback refresh when a hint is lost. Do not let a message grant a role,
execute arbitrary source/commands or replace server-side authorization.
Server-only storage access is a transport boundary, not application permission.
Validate message kinds and identifiers at the receiving application boundary.

Typical result codes include InvalidPayload, ClockError, Busy, Closed,
SequenceLimit and mStore storage/schema failures. A failure does not silently
replace corrupt or newer-schema topic data with defaults. There is no shutdown
flush: each confirmed publication was already persisted independently.

## Verification

The injected-runtime specification is
[`tests/mMessaging.spec.trs`](../../tests/mMessaging.spec.trs), installed as
`mLibraries/tests/mMessagingSpec`. It requires mTestKit, mMessaging, mStore and
mSignal. Run it in the atomic editor runner:

```truscript
return import("/mLibraries/tests/mMessagingSpec").Run()
```

Its 25 cases cover polling, conflict reruns, lost acknowledgements, copied payloads,
retention gaps, expiry, stale/corrupt responses, subscriber ordering, failure
isolation, reentry, teardown and structural boundaries. These cases are authored
test coverage, not a pass claim until the current native run is recorded.

The [verification record](../verification/libraries-0.12.2.md) describes the
recorded local scope. Hosted cross-server behavior remains unverified. See
[testing](../testing.md) before running the native storage fixtures.
