# Using mNet

Create a Module asset at `mLibraries/mNet` from [mNet.trs](../packages/mNet/src/mNet.trs). Leave it unattached. Use separate attached Server and Client entry scripts. Read the [API reference](api/mNet.md) for limits and failure results.

This API carries named events in both directions and client-to-server requests with replies. The server owns route policy and always receives the real sender through the native adapter.

The application creates and owns its RemoteEvent. Connect the server before exposing the remote to clients:

```truscript
# Server entry script
local mNet = import("/mLibraries/mNet")
local mCleanup = import("/mLibraries/mCleanup")
local lifetime = mCleanup.New()
local remote = new RemoteEvent() { Name = "ExampleNet" }
local server = mNet.NewServer({ Remote = remote })

server.Register({
    Name = "status", Kind = "Request",
    Authorize = func(context):
        return context.Sender.IsConnected
    , Validate = mNet.NoPayload,
    Run = func(context, value):
        return "ready"
})

lifetime.Add(server.Destroy)
lifetime.AddInstance(remote)
lifetime.AddConnection(game.Players.PlayerRemoved.Connect(func(player):
    server.RemovePeer(player)
))
lifetime.AddConnection(this.Removed.Connect(func(): lifetime.Destroy()))
remote.Parent = world
```

This example deliberately exposes a harmless public status route to connected players. Privileged routes need an explicit server-owned permission check. Never use a request field as the actor, ownership proof, grant or authorization context.

The client owns its endpoint and one frame connection for timeouts:

```truscript
# Client entry script
local mNet = import("/mLibraries/mNet")
local mCleanup = import("/mLibraries/mCleanup")
local lifetime = mCleanup.New()
local remote = world.WaitForChild("ExampleNet", 20)
if remote == nil: return
local client = mNet.NewClient({ Remote = remote })
lifetime.Add(client.Destroy)
lifetime.AddConnection(game.TimeSystem.FrameStepped.Connect(func(delta):
    client.Step()
))
lifetime.AddConnection(this.Removed.Connect(func(): lifetime.Destroy()))
lifetime.AddConnection(remote.Destroyed.Connect(func(): lifetime.Destroy()))

local call = client.Request("status", nil, func(outcome):
    if outcome.Ok:
        print(outcome.Value)
    else:
        print(outcome.Code, outcome.Message)
)
```

Completion can be inline, so the callback must not assume the local call variable has already been assigned. Keep the handle to inspect GetOutcome or stop waiting with Cancel. A timeout or cancellation does not cancel server work. Use IsActive and current application rules before server mutations.

For server notifications, subscribe on the client before the server sends:

```truscript
# Client, using the same owned client/lifetime from above
local subscription = client.On("notice", func(value):
    print(value)
)
lifetime.AddConnection(subscription)
```

On the server, when application policy says this actual engine Player should hear it:

```truscript
server.Send(player, "notice", "ready")
```

The server chooses player from engine state, not a request's actor field. A send result reports local acceptance. For a startup notification, have the client subscribe first and then send a ready request; the server can send from that request's handler. For broadcasting, iterate the intended engine players in trusted server code. The library does not replay earlier notifications or implement reverse RPC.

For a packet schema, use its decoder as the route validator:

```truscript
server.Register({
    Name = "inventory", Kind = "Request",
    Authorize = CanUseInventory,
    Validate = inventoryCodec.Decode,
    Run = ApplyValidatedInventoryRequest
})
```

CanUseInventory, inventoryCodec and ApplyValidatedInventoryRequest are application-owned definitions. A decoded packet proves structure and ranges, not that the client owns an item or may change inventory.

Injected transports let tests deliver data immediately, queue it, throw, duplicate replies or change an injected clock without creating remotes. See [mNet.spec.trs](../tests/mNet.spec.trs). The [server](../tests/mNetNativeServer.trs) and [client](../tests/mNetNativeClient.trs) fixtures check native RemoteEvent behavior separately. They are local Creator test entries. See [testing](testing.md) and the [verification record](verification/libraries-0.12.2.md). Local tests do not establish published-server, adverse-network, engine-wide delivery or maximum-throughput guarantees.
