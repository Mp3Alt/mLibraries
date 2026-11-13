# mPlayer

mPlayer owns one resource scope per observed player and one per current character. It observes existing players and future joins without a frame loop. Call Destroy when the system using the observer ends.

~~~truscript
local mPlayer = import("/mLibraries/mPlayer")
local watch = mPlayer.New({
    OnCharacter = func(scope):
        print(scope.GetPlayer().Name)
        scope.Add(func(): print("Character scope ended"))
}, nil)
# Add watch.Destroy to the owner's mCleanup.
~~~

| Observer method | Contract |
| --- | --- |
| New(options, adapter) | Subscribes before reading the initial roster. Pass nil for the native adapter. |
| GetPlayers() | Fresh array of players with active player scopes, in observation order. |
| GetCharacter(player) | Current character with an active character scope, or nil. Uses player identity. |
| IsDestroyed() | True as soon as destruction or a terminal failure starts. |
| Destroy() | Idempotently invalidates scopes, disconnects subscriptions and drains owned resources. |

Use dot calls. Options accept only OnPlayer, OnCharacter, OnError and MaxPlayers. At least one of OnPlayer or OnCharacter is required. Callbacks are synchronous and must not wait or start unmanaged work. New may invoke callbacks for players already present before it returns.

OnPlayer(scope) runs once per observed membership. OnCharacter(scope) runs once per observed current character identity after its player callback. Duplicate notifications are coalesced. Replacing a character closes its previous scope before invoking the next callback. Removing a player closes its character scope before its player scope. Default observation uses Players.PlayerAdded/PlayerRemoved, Player.CharacterAdded/Changed, and the character's Removed/Destroyed signals.

| Scope method | Contract |
| --- | --- |
| IsActive() | False before owned cleanup callbacks begin. |
| GetPlayer() | Owning player while active, otherwise nil. |
| GetCharacter() | Character for a character scope; nil for a player scope or inactive scope. |
| Add(callback) | Adds a synchronous cleanup function. |
| AddConnection(connection) | Owns a connection with Disconnect(). |
| AddInstance(instance) | Owns an instance with Destroy(). |

Scopes expose no public Clean or Destroy. Ownership uses mCleanup: resources drain in reverse registration order, errors are isolated, and additions to inactive scopes throw. A previously retained scope releases its player and character references on invalidation. The observer retains current membership bookkeeping until the corresponding removal or observer destruction.

If OnPlayer throws, its resources are drained, that membership is excluded from getters, and its callback is not retried. Other players continue. If OnCharacter throws, that character's resources are drained and GetCharacter returns nil until a different character is observed. OnError(stage, error) receives the original failure after cleanup; stages are OnPlayer, OnCharacter, Cleanup, Adapter or Capacity. Errors thrown by OnError are discarded and no error history is retained.

Destroy immediately makes published scopes inactive. If a callback or event consumer is in progress, its finally path performs teardown after it returns. It does not forcibly stop callback code. Character and player cleanup callbacks must not assume a player remains connected or a character remains in the data model.

MaxPlayers defaults to 128 and accepts whole values from 1 through 1024. These are library bookkeeping bounds, not engine player limits. Exceeding the player limit, 4*MaxPlayers+16 pending events, or that many events in one drain retires the whole observer and reports Capacity. Unexpected adapter errors also retire the observer. Startup subscription errors clean up adopted resources and throw a static startup message.

The optional adapter is a copied record containing exactly these seven callable fields. It supports deterministic tests and alternate lifecycle sources:

| Field | Contract |
| --- | --- |
| GetPlayers() | Fresh dense array, at most 1024 player identities. |
| IsPresent(player) | Literal true while that membership is current. |
| GetCharacter(player) | Current live character identity or nil. |
| ConnectAdded(callback) | Connection; callback(player) on a membership starting. |
| ConnectRemoved(callback) | Connection; callback(player) on that membership ending. |
| ConnectCharacter(player, callback) | Connection; callback() when the current character may change. |
| ConnectEnded(character, callback) | Connection; callback() when that character lifetime ends. |

Connections must provide Disconnect(). Adapter subscriptions and reads must not wait; failures throw. Removal must use the same player identity supplied on addition. Adapter authors must notify when characters change, including transition to nil, and return nil from GetCharacter after an end notification. Reusing a user ID with a different player identity creates a new membership.

A lifecycle scope being active does not grant permissions or storage ownership. Keep authorization checks and persistence/session locks in their own trusted paths. See [testing](../testing.md) and the [verification record](../verification/libraries-0.12.2.md) for the local adapter and respawn workload. Real network disconnects and every scheduler ordering were not forced.
