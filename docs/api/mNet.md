# mNet

mNet provides bounded named events in both directions and client-to-server requests with correlated replies over a trusted transport. It uses ordinary native values and creates no remote instances. A native endpoint owns its connection; the application owns the RemoteEvent and calls Destroy when its feature ends.

```truscript
local mNet = import("/mLibraries/mNet")
local server = mNet.NewServer({ Remote = remote })
server.Register({
    Name = "status", Kind = "Request",
    Authorize = func(context): return context.Sender.IsConnected,
    Validate = mNet.NoPayload,
    Run = func(context, value): return "ready"
})
```

## Endpoints

`mNet.NewServer(options)` and `mNet.NewClient(options)` return endpoint objects directly. Invalid construction options or a failed transport connection throw. Pass an engine-created, server-owned `RemoteEvent` as `Remote`, or pass both injected functions `Connect` and `Send`. Do not combine the two forms.

| Option | Contract |
| --- | --- |
| `Remote` | Native server-created RemoteEvent. Server uses Connect/FireTo; client uses Connect/Fire. The library does not destroy it. |
| `Connect` | Server: receives a callback `(peer, wire)`. Client: receives `(wire)`. Must return a connection with an idempotent Disconnect method. The adapter must supply the real sender and must not invoke arbitrary request data as code. |
| `Send` | Server: `(peer, wire)`. Client: `(wire)`. Sends one native array as one argument. |
| `Clock` | Optional finite, nonnegative, nondecreasing seconds; defaults to `host.time`. Exceptions or backwards values fail closed. |

Server options are `Burst` (default 8, integer 1..64), `Rate` (default 4 tokens/second, 0..100), `MaxPeers` (default 128, integer 1..256), `MaxInFlight` (default 32, integer 1..64), and `PerPeerInFlight` (default 2, integer 1..8).

Client options are `MaxPending` (default 32, integer 1..64) and `Timeout` (default 5 seconds, 0.01..120). The timeout stops local waiting. It does not cancel, undo or roll back server work.

## Server API

| Call | Result |
| --- | --- |
| `server.Register(definition)` | Registers a copied definition; returns true. Invalid, duplicate, busy or over-capacity registration throws. |
| `server.RemovePeer(peer)` | Invalidates that peer's current session and frees its capacity. Returns whether an active session was invalidated. |
| `server.Send(peer, name, payload)` | Sends a named event to one engine peer. Returns local acceptance or a fixed failure; it is not a delivery acknowledgement. |
| `server.IsDestroyed()` | Boolean. |
| `server.Destroy()` | Idempotent connection teardown and session invalidation. |

A definition requires `Name`, `Kind`, `Authorize`, `Validate` and `Run`. Name is case-sensitive, at most 32 characters, and starts with an ASCII letter followed by ASCII letters, digits, `_` or `-`. Kind is exactly `Event` or `Request`. At most 32 routes are registered, with no replacement/removal API. Register trusted definitions during startup; keep definition data stable while it is copied.

The server charges personal admission before parsing an incoming envelope. Malformed traffic spends available tokens too. Traffic above personal capacity, admission contention and exhausted peer capacity are silently dropped. Clients waiting for those replies will time out. Global and per-peer in-flight limits bound work that reaches route hooks, rather than the engine's preceding packet handling or task creation.

Dispatch checks the envelope and data budget, finds the matching route kind, then calls `Authorize(context)`. Only literal true permits validation. `Validate(payload)` must return a record with literal `Ok = true` and `Value = canonical_payload`. Run receives that value as `Run(context, value)`. `mNet.NoPayload` is a validator accepting only nil. A packet codec composes directly as `Validate = codec.Decode`; mNet does not depend on mPacket.

The context contains the transport-supplied `Sender` and `IsActive()`, which checks the exact original peer session and endpoint lifetime. A packet cannot replace the sender. Recheck current permissions, membership and application state immediately before consequential changes; IsActive is a lifetime check, not an application authorization policy. RemovePeer is not a ban: a later trusted delivery can create a fresh session for the same identity. The native adapter ignores disconnected Players.

Callbacks are trusted application code. Keep authorization and validation synchronous. Running handlers cannot be forcibly stopped by RemovePeer or Destroy; stale sessions receive no reply. Handler results must obey the same data limits as requests. Caught failures use fixed public codes/messages, without raw exceptions. Event results are discarded.

## Client API

| Call | Result |
| --- | --- |
| `client.Send(name, payload)` | `{ Ok = true }` or a fixed `{ Ok = false, Code, Message }` failure. Local acceptance does not acknowledge server execution. |
| `client.On(name, handler)` | Subscribes to server events; returns an idempotent Disconnect handle. Invalid, busy or over-capacity registration throws. |
| `client.Request(name, payload, callback, timeout)` | A call handle, even for an immediate failure. Callback and timeout may be omitted. |
| `client.Step()` | Expires due requests; returns the number settled by that step. Call regularly from an owned native frame connection. |
| `client.IsDestroyed()` | Boolean. |
| `client.Destroy()` | Idempotently disconnects and settles pending calls with Destroyed. |
| `call.Cancel()` | Returns true only for its first accepted terminal claim. Stops waiting locally; sends no server cancellation. |
| `call.GetOutcome()` | Fresh metadata snapshot: `{ Status, Ok, Value, Code, Message }`. |

Status is `Pending`, `Succeeded`, `Failed`, `TimedOut` or `Cancelled`. Check Ok and Status; nil, false and zero are valid successful values. Timeout requires Step: there is no hidden timer or background task.

Completion callbacks receive the same outcome shape. They may run inline before Request returns, including with an injected immediate transport. The pending slot is released before invoking the callback. Exceptions are isolated. Keep callbacks synchronous; destroying an endpoint does not forcibly stop a callback already running.

Event handlers receive one payload value. Each client permits 32 distinct event names and 64 total listeners. Disconnect frees listener/name capacity. Dispatch snapshots the matching records; listeners added during dispatch start with the next event, and disconnected listeners that have not been claimed are skipped. Destroy stops remaining dispatch and releases all subscriptions. An already claimed callback may finish. Errors are isolated, and payloads use normal shared reference semantics. Register before requesting a server push; there is no application-level event replay or acknowledgement.

Terminal metadata is committed once and copied for readers/callbacks. Nested Value data uses normal reference semantics; it is not deep-cloned. Inputs must remain stable while operations read them. The library retains pending callback/correlation metadata, not a request payload history, and clears completion callbacks on settlement.

Client instances use increasing private epochs and non-wrapping request IDs. Late, duplicate, cancelled and previous-client-epoch replies cannot settle a different pending call. These values provide correlation, not secrecy or authorization. Replacing the module code itself while an old transport is alive is outside this lifetime contract; stop and rebuild the feature instead.

## Data and wire limits

The private protocol uses exactly five array fields. Client events are `[0, 0, 0, name, payload]`, server events `[4, 0, 0, name, payload]`, requests `[1, client_epoch, request_id, name, payload]`, and replies `[2, client_epoch, request_id, ok, value_or_error_code]`. Correlation values must be exact integers from 1 through 2,147,483,647. The server rejects client messages using the server-event kind and replies only to the transport sender.

Payloads support nil, booleans, finite numbers, strings, arrays and string-keyed records. Limits are 1,024 visited values including containers, four container levels, 64 entries per record, 64 characters per record key, and 4,096 total native string characters including record keys. Cycles, instances, vectors, functions and other objects fail. These are mNet policies; they are not byte counts or engine limits. Native send limits still apply.

Failure codes are `InvalidInput`, `InvalidPayload`, `UnknownRoute`, `Denied`, `ValidationError`, `HandlerError`, `InvalidResponse`, `Busy`, `Limit`, `TransportError`, `ClockError`, `Timeout`, `Cancelled` and `Destroyed`.

Injected contracts and native RemoteEvent fixtures cover different execution paths. See [testing](../testing.md) and the [verification record](../verification/libraries-0.12.2.md) for the recorded scope. They do not certify production security, adverse-network behavior, maximum throughput or delivery guarantees.
