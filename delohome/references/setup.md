# Pairing and credentials

Every device here needs a one-time ceremony, and every one of them requires a human at the
device. None can be completed by an agent alone. Get the person in position *before*
starting, because several have short windows.

## Credential rules

Credentials resolve environment-first, then 1Password, and are never written to disk.

**Reference by item UUID, not title.** Titles are not unique in `DeLoSecrets`, and a title
containing parentheses cannot be resolved by an `op://` reference at all — `op read`
returns an empty string and a bare error, which then surfaces as a baffling 401 from
whatever service you were actually trying to reach. That cost real time once already.

```
op://DeLoSecrets/<ITEM-UUID>/<field>          # right
op://DeLoSecrets/Jellyfin (DeLoFlix)/cred     # returns empty, silently
```

Already stored:

| What | Item UUID | Status |
|---|---|---|
| Hue application key (+ clientkey) | `mf5sqxr544cmzcyeoc7pxfmzsu` | paired |
| Jellyfin / DeLoFlix API key | `2aym4v3pqkyjzey2i5ivjewedi` | working |
| Samsung Bedroom TV token | `jqvhzxoo2rx6hmue6l7ncfwoza` | paired |
| Z-Wave S2 network keys | item "Z-Wave Network Keys" | created |

Still missing: both LG client keys, and the Fire TV ADB keypair.

## Hue bridge — done

Press the large round button on top of the bridge, then run the poller, which retries for
five minutes so the press can happen whenever the person gets there:

```bash
mise run hue:pair
```

`generateclientkey` is a **one-shot** opportunity: omit it on the pairing POST and the
entertainment clientkey can never be retrieved without deleting the app entry and pressing
the button again. The script always requests it.

Pairing failure returns **HTTP 200** with a single-element list holding
`error.type == 101`. Anything using `raise_for_status()` as its error gate sails straight
past "link button not pressed" and then `KeyError`s on `["success"]`.

## LG webOS — outstanding, both sets

```bash
delohome displays pair-display office
delohome displays pair-display "ava's room"
```

A modal appears on the TV and must be accepted **with the TV remote inside about ten
seconds** (`aiowebostv`'s `RECEIVE_TIMEOUT`). Have the remote in hand before calling.

The call returns a client key. It is **not persisted automatically** — store it in a new
1Password item, then set `credential:` on that display in `config/home.yaml` by item UUID.
The key must be kept forever; losing it means another trip to the TV.

The env-var fallback names are `LG_CLIENT_KEY_LG_OFFICE` and `LG_CLIENT_KEY_LG_AVA`.

## Fire TV — outstanding, two phases

**Phase 1** generates the keypair. Nothing is written to disk — the returned strings must
be stored immediately, both of them, in one 1Password item with fields `private_key` and
`public_key`:

```bash
delohome displays pair-display "living room"
```

Set `credential:` on `firetv_living` to that item's UUID. The client derives the public-key
reference by swapping `/private_key` for `/public_key`.

**Phase 2**, with the TV awake, run the same command again and accept **"Allow USB
debugging?"** on screen with **"Always allow from this computer" ticked**. Without the
checkbox the grant lasts only for that session.

Two traps worth knowing:

- `keygen()` **overwrites existing files without warning**. Regenerating the keypair
  silently un-authorises the TV, and the failure only appears as an auth timeout at the
  next connect. An ephemeral container filesystem would do this on every deploy.
- The private key is the whole credential — arbitrary shell on that TV, forever, no further
  prompt.

## Samsung — done

Turn the TV on first; it is invisible to every scan while asleep. Then:

```bash
mise run samsung:capture
```

One pass captures IP and MAC, completes token pairing, and writes the token straight from
the websocket into `op item create -` over stdin, so it never lands in argv or a file.

## Z-Wave — outstanding, four devices

Requires the sidecar running (`mise run up`). Full procedure in
[lights.md](./lights.md#z-wave). The short version: **exclude before include**, and tap the
paddle once rather than holding it.

## After pairing anything

1. Store the credential in 1Password, by UUID.
2. Set `credential:` on the device in `~/code/DeLoHome/config/home.yaml`.
3. `delohome displays list-displays` should now show `paired: true`.
4. If a domain was previously reporting an error, `reload_domains` picks up the fix without
   restarting the server.
