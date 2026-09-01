#!/usr/bin/env python3
"""Momo's self-contained Trello board adapter (stdlib only — no uv/httpx).

This is the Trello twin of the pjangler `tp` adapter's providers/trello.sh, but
bundled INSIDE the momo skill so Momo carries its own board capability into ANY
repo — the repo needs only a `.project.json` (ticket_provider.type = "trello")
and, when its kanban columns are non-standard, a `.momo/config.json` lane map.
Nothing is installed per-repo; local parameters override shared behavior.

Implements the same normalized-op contract as `tp` so Momo's board-awareness
doctrine is provider-uniform:
    resolve                          -> {provider, board_id, board_url, me, list_map, board_lists}
    active_milestone                 -> {id, name, state}   (Trello has no cycles; board-as-milestone)
    list_issues                      -> [{id, key, title, state, state_type, list, url, ...}]
    get_issue <id|idShort>           -> {id, key, title, description, acceptance, state, list, comments}
    comment <card-reference> <body>  -> prints comment id
    transition <card-reference> <state|lane>
                                      -> move to a normalized state or literal lane

Credentials (env): TRELLO_API_KEY (or TRELLO_KEY) + TRELLO_TOKEN.
Board id: --board-id, else $TRELLO_BOARD_ID, else .project.json ticket_provider.board_id.
Lane map: <root>/.momo/config.json  "lanes" table (multi-lane per state). Falls back to
the STANDARD flow if absent. Fails loud (never guesses) on an unmapped/unknown target.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://api.trello.com/1"

# Normalized state -> Trello lane(s). Used when a repo has no .momo/config.json.
# Matches the pjangler trello.sh standard defaults. Non-standard boards supply a
# config; the FIRST lane per state is the canonical write target.
_STANDARD_LANES = {
    "backlog": ["Backlog"],
    "unstarted": ["To Do"],
    "started": ["In Progress"],
    "in_review": ["Review"],
    "completed": ["Done"],
    "cancelled": ["Cancelled"],
}
NORMALIZED_STATES = tuple(_STANDARD_LANES)


class ConfigError(ValueError):
    """Raised when a lane configuration cannot be interpreted safely."""


def die(msg: str, code: int = 2):
    sys.stderr.write(f"trello: {msg}\n")
    raise SystemExit(code)


def find_root(start: str) -> str:
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, ".project.json")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.abspath(start)
        d = parent


def load_project(root: str) -> dict:
    path = os.path.join(root, ".project.json")
    try:
        with open(path, encoding="utf-8") as stream:
            return json.load(stream)
    except Exception:
        return {}


def load_config(root: str) -> dict:
    path = os.path.join(root, ".momo", "config.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as stream:
            return json.load(stream)
    except Exception as e:
        die(f"invalid .momo/config.json: {e}")


def _exact_nonblank(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise ConfigError(f"{label} must be a non-blank exact string")
    return value


def _validated_lane_owners(lm: object) -> tuple[dict[str, list[str]], dict[str, str]]:
    if not isinstance(lm, dict):
        raise ConfigError("lanes must be an object of state -> [lane, ...]")
    unknown = sorted(
        (key for key in lm if key not in NORMALIZED_STATES),
        key=repr,
    )
    if unknown:
        raise ConfigError(f"unknown lane states: {unknown!r}")

    canonical: dict[str, list[str]] = {}
    owners: dict[str, str] = {}
    for state in NORMALIZED_STATES:
        values = lm.get(state)
        if not isinstance(values, list) or not values:
            raise ConfigError(f"lanes[{state!r}] must be a non-empty list")
        state_seen: set[str] = set()
        canonical[state] = []
        for index, value in enumerate(values):
            lane = _exact_nonblank(value, f"lanes[{state!r}][{index}]")
            folded = lane.casefold()
            if folded in state_seen:
                raise ConfigError(
                    f"lanes[{state!r}] contains duplicate lane {lane!r}"
                )
            if folded in owners:
                raise ConfigError(
                    f"lane {lane!r} belongs to both {owners[folded]!r} "
                    f"and {state!r}"
                )
            state_seen.add(folded)
            owners[folded] = state
            canonical[state].append(lane)
    return canonical, owners


def _validated_write_targets(
    config: object,
    lm: dict[str, list[str]],
) -> dict[str, str]:
    if not isinstance(config, dict):
        raise ConfigError("config must be a JSON object")
    if "write_targets" not in config:
        return {}
    raw = config["write_targets"]
    if not isinstance(raw, dict):
        raise ConfigError("write_targets must be an object of state -> lane")
    unknown = sorted(
        (key for key in raw if key not in NORMALIZED_STATES),
        key=repr,
    )
    if unknown:
        raise ConfigError(f"unknown write_target states: {unknown!r}")

    canonical: dict[str, str] = {}
    for state, value in raw.items():
        target = _exact_nonblank(value, f"write_targets[{state!r}]")
        matches = [lane for lane in lm[state] if lane.casefold() == target.casefold()]
        if len(matches) != 1:
            raise ConfigError(
                f"write_targets[{state!r}]={target!r} must name exactly one "
                f"lane in lanes[{state!r}]={lm[state]!r}"
            )
        canonical[state] = matches[0]
    return canonical


def validate_lane_config(
    config: object,
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Return a strict effective lane map and canonical configured write targets."""
    if not isinstance(config, dict):
        raise ConfigError("config must be a JSON object")
    if "lanes" in config:
        raw_lanes = config["lanes"]
        if not isinstance(raw_lanes, dict):
            raise ConfigError("lanes must be an object of state -> [lane, ...]")
    else:
        raw_lanes = {}
    unknown = sorted(
        (key for key in raw_lanes if key not in NORMALIZED_STATES),
        key=repr,
    )
    if unknown:
        raise ConfigError(f"unknown lane states: {unknown!r}")

    effective: dict[str, list[str]] = {
        state: list(values) for state, values in _STANDARD_LANES.items()
    }
    for state, values in raw_lanes.items():
        if not isinstance(values, list) or not values:
            raise ConfigError(f"lanes[{state!r}] must be a non-empty list")
        effective[state] = list(values)

    lm, _owners = _validated_lane_owners(effective)
    write_targets = _validated_write_targets(config, lm)
    return lm, write_targets


def _validated_lane_context(
    config: object,
    lm: object,
) -> tuple[dict[str, list[str]], dict[str, str]]:
    configured_lm, write_targets = validate_lane_config(config)
    provided_lm, _owners = _validated_lane_owners(lm)
    if provided_lm != configured_lm:
        raise ConfigError("effective lane map does not match the supplied config")
    return configured_lm, write_targets


def lane_map(config: object) -> dict[str, list[str]]:
    try:
        lm, _write_targets = validate_lane_config(config)
        return lm
    except ConfigError as exc:
        die(f"invalid lane config: {exc}", 3)


def write_target(config: object, lm: object, state: str) -> str:
    try:
        if state not in NORMALIZED_STATES:
            raise ConfigError(f"unknown normalized state {state!r}")
        canonical_lm, configured = _validated_lane_context(config, lm)
        return configured.get(state, canonical_lm[state][0])
    except ConfigError as exc:
        die(f"invalid lane config: {exc}", 3)


def state_for_lane(lane: str, lm: object) -> str:
    try:
        lane_name = _exact_nonblank(lane, "lane")
        _canonical, owners = _validated_lane_owners(lm)
        return owners.get(lane_name.casefold(), "other")
    except ConfigError as exc:
        die(f"invalid lane config: {exc}", 3)


def resolve_target_list(lists: object, lane: object) -> dict:
    """Resolve one live lane without silently collapsing duplicate names."""
    if not isinstance(lane, str) or not lane:
        die(f"invalid configured target lane {lane!r}", 3)
    if not isinstance(lists, list):
        die("board lists response is not an array", 4)

    by_name: dict[str, dict] = {}
    for item in lists:
        if not isinstance(item, dict):
            die("board lists response contains a non-object", 4)
        list_id = item.get("id")
        name = item.get("name")
        if not isinstance(list_id, str) or not list_id:
            die("board lists response contains a list without an id", 4)
        if not isinstance(name, str) or not name:
            die(f"board list {list_id!r} has no name", 4)
        folded = name.casefold()
        if folded in by_name:
            prior = by_name[folded]
            die(
                "duplicate live lanes are ambiguous: "
                f"{prior['name']!r} ({prior['id']}) and {name!r} ({list_id})",
                3,
            )
        by_name[folded] = {"id": list_id, "name": name}

    resolved = by_name.get(lane.casefold())
    if resolved is None:
        live_names = sorted(item["name"] for item in by_name.values())
        die(
            f"target lane {lane!r} is not on the board. Lanes: {live_names}. "
            "Fix .momo/config.json — not guessing.",
            3,
        )
    return resolved


def validate_card(
    payload: object,
    *,
    stage: str,
    expected_id: str | None = None,
    expected_board: str | None = None,
    expected_list: str | None = None,
) -> str:
    """Validate a Trello card response and return its canonical id."""
    if not isinstance(payload, dict):
        die(f"{stage} did not return a card object", 4)
    card_id = payload.get("id")
    if not isinstance(card_id, str) or not card_id:
        die(f"{stage} returned a card without an id", 4)
    if expected_id is not None and card_id != expected_id:
        die(
            f"{stage} returned different card {card_id!r}; expected {expected_id!r}",
            4,
        )
    if expected_board is not None:
        board_id = payload.get("idBoard")
        if not isinstance(board_id, str) or not board_id:
            die(f"{stage} returned a card without a valid idBoard", 4)
        if board_id != expected_board:
            die(
                f"{stage} returned card from different board {board_id!r}; "
                f"expected {expected_board!r}",
                4,
            )
    if expected_list is not None and payload.get("idList") != expected_list:
        die(
            f"{stage} returned list {payload.get('idList')!r}; "
            f"expected {expected_list!r}",
            4,
        )
    return card_id


def card_identities(payload: dict) -> set[str]:
    """Return every stable Trello identity exposed by a card object."""
    return {
        str(value)
        for value in (
            payload.get("id"),
            payload.get("idShort"),
            payload.get("shortLink"),
        )
        if value is not None and str(value)
    }


def resolve_card_id(
    trello: "Trello",
    board: str,
    reference: str,
    identifier: str | None = None,
) -> str:
    """Resolve one board-scoped alias to exactly one native Trello card id."""
    if (
        not isinstance(board, str)
        or not board
        or board != board.strip()
    ):
        die("configured Trello board id must be non-blank", 3)
    if (
        not isinstance(reference, str)
        or not reference
        or reference != reference.strip()
    ):
        die("card reference must be a non-blank exact value", 3)
    normalized_identifier: str | None = None
    if identifier is not None:
        if not isinstance(identifier, str):
            die("configured ticket-provider identifier must be a string", 3)
        stripped_identifier = identifier.strip()
        if stripped_identifier:
            if stripped_identifier != identifier:
                die(
                    "configured ticket-provider identifier must be an exact value",
                    3,
                )
            normalized_identifier = identifier

    cards = trello.get(
        f"boards/{board}/cards",
        {"fields": "id,idBoard,idShort,shortLink"},
    )
    if not isinstance(cards, list):
        die("board cards response is not an array", 4)

    aliases: dict[str, set[str]] = {}
    for card in cards:
        if not isinstance(card, dict):
            die("board cards response contains a non-object", 4)
        native_id = card.get("id")
        if (
            not isinstance(native_id, str)
            or not native_id
            or native_id != native_id.strip()
        ):
            die("board card has no valid native id", 4)
        board_id = card.get("idBoard")
        if not isinstance(board_id, str) or not board_id:
            die(f"board card {native_id!r} has no valid idBoard", 4)
        if board_id != board:
            die(
                f"board card {native_id!r} belongs to external board "
                f"{board_id!r}; expected {board!r}",
                4,
            )

        id_short = card.get("idShort")
        if isinstance(id_short, bool) or not isinstance(id_short, (int, str)):
            die(f"board card {native_id!r} has no valid idShort", 4)
        id_short_text = str(id_short)
        if not id_short_text or id_short_text != id_short_text.strip():
            die(f"board card {native_id!r} has an empty idShort alias", 4)

        short_link = card.get("shortLink")
        if (
            not isinstance(short_link, str)
            or not short_link
            or short_link != short_link.strip()
        ):
            die(f"board card {native_id!r} has an empty shortLink alias", 4)

        card_aliases = {native_id, id_short_text, short_link}
        if normalized_identifier is not None:
            card_aliases.add(f"{normalized_identifier}-{id_short_text}")
        for alias in card_aliases:
            aliases.setdefault(alias.casefold(), set()).add(native_id)

    ambiguous = sorted(
        (alias, native_ids)
        for alias, native_ids in aliases.items()
        if len(native_ids) > 1
    )
    if ambiguous:
        alias, native_ids = ambiguous[0]
        die(
            f"duplicate card alias {alias!r} maps to "
            f"{sorted(native_ids)!r}",
            3,
        )

    matches = aliases.get(reference.casefold(), set())
    if not matches:
        die(f"card reference {reference!r} is not on configured board {board!r}", 3)
    if len(matches) != 1:
        die(f"card reference {reference!r} is ambiguous", 3)
    return next(iter(matches))


def validate_comment_response(payload: object, expected_cards: set[str]) -> str:
    """Prove a comment action id and its requested-card identity."""
    if not isinstance(payload, dict):
        die("comment response did not return an action object", 4)

    action_id = payload.get("id")
    if not isinstance(action_id, str) or not action_id.strip():
        die("comment response returned no action id", 4)

    action_type = payload.get("type")
    if action_type is not None and action_type != "commentCard":
        die(f"comment response returned unexpected action type {action_type!r}", 4)

    exposed_cards: set[str] = set()
    identity_envelopes = 0

    top_id_card = payload.get("idCard")
    if top_id_card is not None:
        identity_envelopes += 1
        exposed_cards.add(str(top_id_card))

    top_card = payload.get("card")
    if top_card is not None:
        identity_envelopes += 1
        if not isinstance(top_card, dict):
            die("comment response card envelope is malformed", 4)
        identities = card_identities(top_card)
        if not identities:
            die("comment response card envelope has no identity", 4)
        exposed_cards.update(identities)

    data = payload.get("data")
    if data is not None:
        if not isinstance(data, dict):
            die("comment response data envelope is malformed", 4)
        data_id_card = data.get("idCard")
        if data_id_card is not None:
            identity_envelopes += 1
            exposed_cards.add(str(data_id_card))
        data_card = data.get("card")
        if data_card is not None:
            identity_envelopes += 1
            if not isinstance(data_card, dict):
                die("comment response data.card envelope is malformed", 4)
            identities = card_identities(data_card)
            if not identities:
                die("comment response data.card envelope has no identity", 4)
            exposed_cards.update(identities)

    if not identity_envelopes:
        die("comment response exposed no card identity", 4)
    if not exposed_cards.issubset(expected_cards):
        die(
            "comment response belongs to a different card: "
            f"got {sorted(exposed_cards)!r}, expected one of "
            f"{sorted(expected_cards)!r}",
            4,
        )
    return action_id.strip()


def comment_card(
    trello: "Trello",
    board: str,
    card_ref: str,
    body: str,
    identifier: str | None = None,
) -> str:
    """Create one comment and return its proven Trello action id."""
    native_id = resolve_card_id(trello, board, card_ref, identifier)
    card_fields = {"fields": "id,idBoard,shortLink,idShort"}
    card = trello.get(f"cards/{native_id}", card_fields)
    card_id = validate_card(
        card,
        stage="comment card lookup",
        expected_id=native_id,
        expected_board=board,
    )
    expected_cards = card_identities(card)
    response = trello.post(
        f"cards/{card_id}/actions/comments",
        {"text": body},
    )
    return validate_comment_response(response, expected_cards)


def transition_card(
    trello: "Trello",
    board: str,
    card_ref: str,
    target: str,
    config: dict,
    lm: dict,
    identifier: str | None = None,
) -> dict:
    """Move one card once, then prove the exact card and list via live readback."""
    normalized_target = target in NORMALIZED_STATES
    if normalized_target:
        configured_lane = write_target(config, lm, target)
    else:
        try:
            _validated_lane_context(config, lm)
        except ConfigError as exc:
            die(f"invalid lane config: {exc}", 3)
        configured_lane = target

    native_id = resolve_card_id(trello, board, card_ref, identifier)
    card_fields = {"fields": "id,idBoard,idList,shortLink,idShort"}
    before = trello.get(f"cards/{native_id}", card_fields)
    card_id = validate_card(
        before,
        stage="card lookup",
        expected_id=native_id,
        expected_board=board,
    )

    live_lists = trello.get(f"boards/{board}/lists", {"fields": "name"})
    target_list = resolve_target_list(live_lists, configured_lane)
    resolved_state = state_for_lane(target_list["name"], lm)
    if normalized_target and resolved_state != target:
        die(
            f"normalized target {target!r} resolved to lane "
            f"{target_list['name']!r} classified as {resolved_state!r}",
            3,
        )

    updated = trello.put(f"cards/{card_id}", {"idList": target_list["id"]})
    validate_card(
        updated,
        stage="PUT response",
        expected_id=card_id,
        expected_board=board,
        expected_list=target_list["id"],
    )

    readback = trello.get(f"cards/{card_id}", card_fields)
    validate_card(
        readback,
        stage="GET readback",
        expected_id=card_id,
        expected_board=board,
        expected_list=target_list["id"],
    )

    lane = target_list["name"]
    readback_state = state_for_lane(lane, lm)
    if normalized_target and readback_state != target:
        die(
            f"normalized target {target!r} read back lane {lane!r} "
            f"classified as {readback_state!r}",
            4,
        )
    return {
        "ok": True,
        "card": card_id,
        "requested_card": card_ref,
        "target": target,
        "moved_to": lane,
        "state": readback_state,
    }


class Trello:
    def __init__(self, key: str, token: str):
        self.key, self.token = key, token

    def _url(self, path: str, extra: dict | None = None) -> str:
        q = {"key": self.key, "token": self.token, **(extra or {})}
        return f"{API}/{path}?{urllib.parse.urlencode(q)}"

    def _req(self, method: str, path: str, extra: dict | None = None):
        req = urllib.request.Request(self._url(path, extra), method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            die(f"{method} {path} -> HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}", 4)
        except Exception as e:
            die(f"{method} {path} -> {e}", 4)
        return json.loads(body) if body.strip() else {}

    def get(self, path, extra=None):
        return self._req("GET", path, extra)

    def put(self, path, extra=None):
        return self._req("PUT", path, extra)

    def post(self, path, extra=None):
        return self._req("POST", path, extra)


def creds() -> tuple[str, str]:
    key = os.environ.get("TRELLO_API_KEY") or os.environ.get("TRELLO_KEY")
    token = os.environ.get("TRELLO_TOKEN")
    if not key or not token:
        die("TRELLO_API_KEY (or TRELLO_KEY) and TRELLO_TOKEN must be set", 2)
    return key, token


def emit(obj):
    print(json.dumps(obj, indent=2))


def main() -> int:
    argv = sys.argv[1:]
    root = os.getcwd()
    board_override = None
    # Pull out --root / --board-id anywhere in argv.
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--root" and i + 1 < len(argv):
            root = argv[i + 1]; i += 2; continue
        if argv[i] == "--board-id" and i + 1 < len(argv):
            board_override = argv[i + 1]; i += 2; continue
        rest.append(argv[i]); i += 1
    if not rest:
        sys.stderr.write(__doc__ or "")
        return 2

    root = find_root(root)
    project = load_project(root)
    config = load_config(root)
    lm = lane_map(config)
    tp = (project.get("ticket_provider") or {}) if isinstance(project, dict) else {}
    board = board_override or os.environ.get("TRELLO_BOARD_ID") or tp.get("board_id")
    identifier = tp.get("identifier")
    if not board:
        die("no board id (--board-id, $TRELLO_BOARD_ID, or .project.json ticket_provider.board_id)", 2)

    key, token = creds()
    t = Trello(key, token)
    op, args = rest[0], rest[1:]

    if op == "resolve":
        b = t.get(f"boards/{board}", {"fields": "name,url"})
        me = t.get("members/me", {"fields": "username,fullName"})
        lists = t.get(f"boards/{board}/lists", {"fields": "name"})
        emit({
            "provider": "trello",
            "board_id": b.get("id", board),
            "board_url": b.get("url", ""),
            "board_name": b.get("name", ""),
            "me": {"id": me.get("id", ""), "username": me.get("username", ""), "full_name": me.get("fullName", "")},
            "list_map": lm,
            "config_present": bool(config),
            "board_lists": [l.get("name", "") for l in lists],
        })
    elif op == "active_milestone":
        b = t.get(f"boards/{board}", {"fields": "name"})
        emit({"id": b.get("id", board), "name": b.get("name", ""), "state": "active"})
    elif op == "list_issues":
        lists = {l["id"]: l.get("name", "") for l in t.get(f"boards/{board}/lists", {"fields": "name"})}
        cards = t.get(f"boards/{board}/cards", {"fields": "name,idList,dateLastActivity,url,shortLink,idMembers"})
        rows = []
        for c in cards:
            lane = lists.get(c.get("idList", ""), "?")
            state = state_for_lane(lane, lm)
            rows.append({
                "id": c.get("id", ""), "key": c.get("shortLink", ""), "title": c.get("name", ""),
                "state": state, "state_type": state, "list": lane,
                "updated_at": c.get("dateLastActivity", ""), "assignee": c.get("idMembers", []),
                "url": c.get("url", ""),
            })
        order = {
            "started": 0,
            "in_review": 1,
            "unstarted": 2,
            "backlog": 3,
            "completed": 4,
            "cancelled": 5,
            "other": 6,
        }
        rows.sort(key=lambda r: (order.get(r["state"], 9), r["list"], r["title"]))
        emit(rows)
    elif op == "get_issue":
        if not args:
            die("get_issue needs <id|idShort>")
        c = t.get(f"cards/{args[0]}", {"fields": "name,desc,idList,shortLink,url,idShort"})
        lists = {l["id"]: l.get("name", "") for l in t.get(f"boards/{board}/lists", {"fields": "name"})}
        lane = lists.get(c.get("idList", ""), "?")
        acts = t.get(f"cards/{args[0]}/actions", {"filter": "commentCard", "limit": "50"})
        emit({
            "id": c.get("id", ""), "key": c.get("shortLink", ""), "title": c.get("name", ""),
            "description": c.get("desc", ""), "acceptance": c.get("desc", ""),
            "state": state_for_lane(lane, lm), "state_type": state_for_lane(lane, lm), "list": lane,
            "url": c.get("url", ""),
            "comments": [
                {"id": a.get("id", ""), "author": (a.get("memberCreator") or {}).get("username", ""),
                 "date": a.get("date", ""), "body": (a.get("data") or {}).get("text", "")}
                for a in acts
            ],
        })
    elif op == "comment":
        if len(args) < 2:
            die("comment needs <card-reference> <body>")
        print(comment_card(
            t,
            board,
            args[0],
            " ".join(args[1:]),
            identifier,
        ))
    elif op == "transition":
        if len(args) < 2:
            die("transition needs <card-reference> <state|lane>")
        card_ref, target = args[0], args[1]
        emit(transition_card(
            t,
            board,
            card_ref,
            target,
            config,
            lm,
            identifier,
        ))
    else:
        die(f"unknown op {op!r}. Ops: resolve|active_milestone|list_issues|get_issue|comment|transition")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
