# Using mMessaging

mMessaging carries messages between server instances through a **polled
DataStore topic**. It is not native pub/sub. Polling, the native read cache,
storage latency and retained-history limits affect delivery. Keep authoritative
state in storage and use messages to tell receivers that it may have changed.

## Install and subscribe

Create these **Module** assets and leave them unattached:

| Asset path | Source |
| --- | --- |
| `mLibraries/mSignal` | [mSignal.trs](../packages/mSignal/src/mSignal.trs) |
| `mLibraries/mStore` | [mStore.trs](../packages/mStore/src/mStore.trs) |
| `mLibraries/mMessaging` | [mMessaging.trs](../packages/mMessaging/src/mMessaging.trs) |

Run the native adapter from a **Server** script. Use a separate store namespace
for local development and confirm **Live data in playtests** is off.

```truscript
local messages = import("/mLibraries/mMessaging").New({
    Name = "mMessagingExample",
    Topic = "status"
}, nil)
local connection = messages.Subscribe(func(message):
    if message.Data.Kind == "PolicyChanged":
        print("Read authoritative policy after event " + message.Sequence)
)
messages.Step()

local published = messages.Publish({ Kind = "PolicyChanged" })
if not published.Ok: print("publication unconfirmed: " + published.Code)
```

The first successful Step starts the receiver at the latest sequence and
delivers no retained history. Subscribe before driving it. A newly started
server should load its actual policy independently; the topic is not a replay
log for reconstructing current roles, bans or settings.

## Drive polling explicitly

Call Step from your existing server scheduler. For example, a caller-owned loop
can check whether the channel is due:

```truscript
spawn(func():
    while not messages.IsDestroyed():
        local result = messages.Step()
        if not result.Ok: print("message poll failed: " + result.Code)
        wait(1)
)
```

Step performs a storage read only when its polling deadline arrives. The
default interval is ten seconds; the early calls above are no-ops. A failed due
poll still consumes the interval. Destroy the channel when its owner closes;
that disconnects listeners and closes its store handle. There is no automatic
shutdown flush, because each confirmed publication is already stored.

Use a few shared topics and route a bounded Kind field in the payload. Avoid a
topic per player, a message per frame or publishing full state on every change.
The [API reference](api/mMessaging.md) lists configuration, subscriber and
message limits, Step reports and structural bounds.

## Expect gaps and duplicates

Later polls process retained messages in sequence order. Missed reports count
sequence positions no longer retained; expired entries are skipped. A stale
cached read cannot rewind the local cursor. Handler failures do not stop later
listeners, but the failed delivery is not retried.

Publish has no automatic mutation retry. If its acknowledgement is lost, the
publication may already exist. An explicit later call is a new message and can
duplicate the intended event. Include an application identifier when consumers
need deduplication. There is no guaranteed delivery, exactly-once behavior,
request/reply protocol or durable receiver cursor.

Use messages as hints, then reread the stored state and keep a fallback refresh
for missed messages. Repeating a revision hint should not repeat the underlying
mutation. A message does not authorize a state change.

The [verification record](verification/libraries-0.12.2.md) separates helper
contracts and local tests from hosted multi-server behavior. See [testing](testing.md)
for the included fixtures.
