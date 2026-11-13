# Observe players with owned lifetimes

mPlayer connects lifecycle events, includes players already present, and gives each player and character its own cleanup scope. This keeps a system's connections and temporary instances attached to the lifetime that needs them.

~~~truscript
local mCleanup = import("/mLibraries/mCleanup")
local mPlayer = import("/mLibraries/mPlayer")
local lifetime = mCleanup.New()
local options = {}
options.OnCharacter = func(scope):
    local player = scope.GetPlayer()
    local character = scope.GetCharacter()
    print(player.Name + " spawned")
    scope.AddConnection(character.Changed.Connect(func(property): print(property)))
local watch = mPlayer.New(options, nil)
lifetime.Add(watch.Destroy)
# When this system ends:
# lifetime.Destroy()
~~~

Player scopes last until removal. Character scopes end on replacement, removal from the data model, destruction, or observer destruction. The old scope is inactive before cleanup begins, and its cleanup finishes before a replacement callback starts. Both getters return nil for an inactive scope; capture only values needed by a cleanup function.

Callbacks run synchronously. Keep them short, own every resource they create, and do not wait inside them. Put long-running work behind a separate cancellation design that checks the scope's IsActive state. Destroy invalidates scopes immediately but lets an already running callback return before its owned resources drain.

A thrown setup callback closes its own scope and is reported through OnError(stage, error). An OnPlayer failure skips that membership. An OnCharacter failure skips that character identity and permits the next one. Cleanup errors do not abandon other resources. Report errors outside the failing callback, since the observer catches setup failures by design.

The native adapter observes identity, not UserId. Two Player objects with the same account number have separate lifetimes. GetPlayers returns a copy; mutating that array cannot change observation. GetCharacter returns a native reference, so ordinary engine permissions still apply.

Tests use an injected adapter for snapshot/join races, removals, replacement ordering, callback failures, capacity and reentrant destruction. Run the optional mPlayerNativeServer and mPlayerNativeClient fixtures alone in a fresh two-player Creator playtest with other character-mutating fixtures detached. The server calls LoadCharacter for local Player1. The fixture refuses published servers; stop Play and detach it when finished.

The native fixtures cover local observation and server-driven respawn. See [testing](testing.md), the [verification record](verification/libraries-0.12.2.md) and the [API contract](api/mPlayer.md). Local respawn checks do not force real network disconnects or every scheduler ordering.
