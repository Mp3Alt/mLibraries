# Using mPacket with native remotes

mPacket gives a message a fixed schema and a flat native-array representation. The game still owns the remote, the sender policy and the action taken after decoding. Read the [API reference](api/mPacket.md) for schema rules and failure results.

## Install the module

Create a **Module** script at `mLibraries/mPacket` in Creator's Asset Browser and copy in [mPacket.trs](../packages/mPacket/src/mPacket.trs). Leave it unattached. Asset paths omit `.trs` and are separate from the instance tree.

For the example below, create a second Module asset named `mGame/mInventoryPacket`. Both entry scripts import this same schema:

```truscript
local mPacket = import("/mLibraries/mPacket")

return mPacket.New({
    Id = 7,
    Version = 1,
    MaxRecords = 16,
    Fields = [
        { Name = "ItemId", Type = "integer", Min = 0, Max = 65535 },
        { Name = "Quantity", Type = "integer", Min = 0, Max = 255 }
    ]
})
```

The ID and version identify the format. They grant no permission and do not prove that a player owns an item.

## Receive on the server

Create a **Server** script named `mGame/mInventoryServer`. This small example authorizes only a positive engine-reported world creator. It accepts at most one handler at a time and charges a 250 ms cooldown before decoding, including malformed requests.

```truscript
local inventory = import("/mGame/mInventoryPacket")
local nativeRemote = new RemoteEvent() { Name = "InventoryPacket" }
local owner_id = world.CreatorId
local next_allowed = 0
local claims = 0

nativeRemote.Connect(func(player, payload):
    # The engine supplies player; no packet field chooses the actor.
    if owner_id <= 0 or player.UserId != owner_id:
        return
    local ticket = claims++
    if ticket != 0:
        return
    try:
        local now = host.time()
        if now < next_allowed:
            return
        next_allowed = now + 0.25
        local decoded = inventory.Decode(payload)
        if not decoded.Ok:
            return
        # Apply game-specific ownership and state checks before any mutation.
        print("accepted " + decoded.Value.length + " rows")
    finally:
        claims = 0
)
nativeRemote.Parent = world
```

The handler is connected before the remote is exposed in `world`. Authorization uses the actual sender before examining the payload. The private admission guard covers the cooldown and bounded decode; contending requests are dropped. This is a minimal single-owner policy, not a general per-player rate limiter or flood-protection guarantee.

In a Creator test where `world.CreatorId` is zero, this policy denies every request. To test an unpublished world, substitute your own explicit, server-owned test-ID policy gated by the Creator playtest context. Never accept an actor, owner flag or permission context from the payload.

The example only prints a count. Do not grant inventory or accept arbitrary quantities because a packet decoded. Look up the authoritative game state, check the requested action and recheck current permissions before consequential changes. Do not forward raw request arrays or arbitrary decoded fields to other players.

## Send from the client

Create a **Client** script named `mGame/mInventoryClient`:

```truscript
local inventory = import("/mGame/mInventoryPacket")
local nativeRemote = world.WaitForChild("InventoryPacket")
if nativeRemote == nil:
    return

local result = inventory.Encode([{ ItemId = 7, Quantity = 2 }])
if result.Ok:
    nativeRemote.Fire(result.Value)
```

Send the array as one argument, as shown. mPacket does not replace RemoteEvent or change its direction. Create the remote on the server; a client-created remote cannot serve as a server channel.

Create a Folder under `game.ScriptSystem`, such as `mPacketDemo`, and attach the server and client entry scripts once each. Leave both Module assets unattached. Use a fresh playtest for the example. In a real feature, own the remote and its connections through an explicit lifetime, for example with mCleanup; mPacket does not clean up networking objects for you.

## Bounds and compatibility

A schema has at most eight fields and 64 rows. The largest flat array is 515 elements. Numeric ranges validate values without choosing a physical wire width. Strings have a per-field limit and a total packet character budget; neither is a measurement of remote bytes. Native remote limits and send errors still apply.

Both ends should use a consistent schema definition. Decode checks ID and version, then applies the receiver's field order, types and bounds. The header has no schema hash: reusing an ID/version for a different field order can reinterpret valid values rather than reject them. Reserve IDs within your project and make deliberate version changes when a format changes. There is no automatic migration. A client can copy every schema value, so none of these checks substitutes for authorization.

Keep inputs unchanged while a call reads them. The compiled schema is private and output containers are fresh, but the library is not a transaction over concurrently edited application data. Fields accept only their declared primitive types; nested field values, instances, functions and arbitrary objects are rejected.

## Why a flat array

The codec uses ordinary TruScript arrays with a small schema header. It gives
bounded validation and one shared structure for sender and receiver. It does
not add a native byte buffer or promise lower wire bytes, memory use or latency.

Measure your own records through the actual native remote path before choosing
a transport shape. CPU-only codecs, native transport and whole-process memory
are different measurements. See [testing](testing.md) and the
[verification record](verification/libraries-0.12.2.md) for the recorded scope.
