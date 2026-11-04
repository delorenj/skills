#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["Telethon==1.42.0"]
# ///
"""Fixed-route Telegram user client. No gateway and no command execution."""
from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import getpass
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time
import uuid

CHAT_ID = -5422814811
BOT_USERNAME = "colrerererebot"
MAX_UNITS = 3500
SCAN_LIMIT = 100
LOGIN_NETWORK_TIMEOUT = 45
DEFAULT_ROOT = Path.home() / ".local/state/delegate-to-rere"


class Refusal(Exception):
    pass


class Flood(Exception):
    def __init__(self, seconds):
        self.seconds = max(1, int(seconds))


def request_uuid(value=None):
    try:
        return str(uuid.UUID(value)) if value else str(uuid.uuid4())
    except (ValueError, TypeError, AttributeError):
        raise Refusal("invalid_request_id") from None


def utf16_units(text):
    try:
        return len(text.encode("utf-16-le")) // 2
    except UnicodeError:
        raise Refusal("invalid_unicode") from None


SECRET_PATTERNS = [
    r"-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH PRIVATE KEY)-----",
    r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b",  # Telegram bot token
    r"\b(?:ops|opsa|ghp|github_pat|sk_live|sk_test|xox[baprs])[-_][A-Za-z0-9_.-]{12,}",
    r"\b(?:sk-|AKIA|ASIA)[A-Za-z0-9_-]{16,}",
    r"(?i)\b(?:api[_ -]?(?:key|hash)|password|passwd|secret|access[_ -]?token|refresh[_ -]?token|authorization|session_string|OP_SERVICE_ACCOUNT_TOKEN)\s*[:=]\s*\S+",
    r"(?i)\bBearer\s+[A-Za-z0-9_.-]{12,}",
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
]


def reject_secrets(text):
    if any(re.search(p, text) for p in SECRET_PATTERNS):
        raise Refusal("possible_secret_refused")


def label(value, field):
    if not value or len(value) > 100 or not re.fullmatch(r"[\w .:/@+-]+", value):
        raise Refusal("invalid_" + field)
    return value


def payload(task, agent, rid, project=None):
    agent = label(agent, "agent")
    if project:
        project = label(project, "project")
    if not task.strip():
        raise Refusal("empty_task")
    if len(task) > 14000:
        raise Refusal("message_too_long_3500_utf16_units")
    text = (f"[Delegated by Damian · agent {agent} · request {rid}]\n"
            "@colrerererebot\n"
            "On behalf of Damian; agent-generated request, not Damian-written.\n")
    if project:
        text += f"Project: {project}\n"
    text += "\n" + task.strip()
    reject_secrets(text)
    if utf16_units(text) > MAX_UNITS:
        raise Refusal("message_too_long_3500_utf16_units")
    return text


def private_file(path):
    if path.is_symlink():
        raise Refusal("unsafe_symlink")
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        raise Refusal("unsafe_file_owner_or_type")
    os.chmod(path, 0o600)


class Store:
    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root)

    def prepare(self):
        if self.root.is_symlink():
            raise Refusal("unsafe_state_directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        st = self.root.stat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid():
            raise Refusal("unsafe_state_directory")
        os.chmod(self.root, 0o700)
        for path in self.root.iterdir():
            private_file(path)

    @contextmanager
    def lock(self):
        self.prepare()
        path = self.root / "lock"
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refusal("client_busy_retry_later") from None
            yield
        finally:
            os.close(fd)

    def read(self, name, default=None):
        path = self.root / name
        if not path.exists():
            return default
        private_file(path)
        try:
            return json.loads(path.read_text())
        except (ValueError, OSError):
            raise Refusal("invalid_local_state") from None

    def write(self, name, data):
        path = self.root / name
        tmp = self.root / (name + ".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, ensure_ascii=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        dfd = os.open(self.root, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)

    def config(self):
        cfg = self.read("config.json")
        if not cfg or not cfg.get("enabled"):
            raise Refusal("owner_local_login_required")
        if cfg.get("chat_id") != CHAT_ID:
            raise Refusal("forbidden_route")
        if (not isinstance(cfg.get("user_id"), int) or cfg["user_id"] <= 0
                or not isinstance(cfg.get("bot_id"), int) or cfg["bot_id"] <= 0):
            raise Refusal("invalid_identity_pins")
        return cfg

    def receipt(self, rid):
        rid = request_uuid(rid)
        rec = self.read(f"request-{rid}.json")
        if rec is None:
            raise Refusal("unknown_request")
        if rec.get("request_id") != rid or rec.get("chat_id") != CHAT_ID:
            raise Refusal("invalid_receipt_route")
        return rec

    def save(self, rec):
        self.write(f"request-{request_uuid(rec['request_id'])}.json", rec)


@dataclass
class Message:
    id: int
    chat_id: int
    sender_id: int
    text: str
    reply_to: int | None = None
    outgoing: bool = False


def public_receipt(rec):
    return {k: rec[k] for k in ("request_id", "chat_id", "message_id", "status", "retry_after") if k in rec}


class Engine:
    """Caller holds Store.lock throughout each operation, including network calls."""
    def __init__(self, store, transport, cfg):
        self.store, self.transport, self.cfg = store, transport, cfg
        if cfg.get("chat_id") != CHAT_ID:
            raise Refusal("forbidden_route")

    async def verify(self):
        uid, bid = await self.transport.identities()
        if uid != self.cfg["user_id"] or bid != self.cfg["bot_id"]:
            raise Refusal("identity_mismatch_owner_login_required")

    async def send(self, task, agent, rid=None, project=None):
        rid = request_uuid(rid)
        text = payload(task, agent, rid, project)
        digest = hashlib.sha256(text.encode()).hexdigest()
        old = self.store.read(f"request-{rid}.json")
        if old:
            rec = self.store.receipt(rid)
            if rec.get("user_id") != self.cfg["user_id"] or rec.get("bot_id") != self.cfg["bot_id"]:
                raise Refusal("receipt_owner_mismatch")
            if rec["digest"] != digest:
                raise Refusal("request_id_payload_conflict")
            if rec["status"] != "rate_limited":
                return public_receipt(rec)
            if rec["retry_after"] > time.time():
                return public_receipt(rec)
        else:
            rec = dict(request_id=rid, chat_id=CHAT_ID, message_id=None,
                       status="pending", user_id=self.cfg["user_id"], bot_id=self.cfg["bot_id"],
                       random_id=secrets.randbits(63) or 1,
                       digest=digest, text=text, responses=[], created_at=time.time())
        await self.verify()
        # Persist uncertainty BEFORE dispatch: interruption or process death cannot cause a resend.
        rec["status"] = "delivery_unknown"
        self.store.save(rec)
        try:
            mid = await self.transport.send(text, rec["random_id"])
            if not isinstance(mid, int) or mid <= 0:
                raise Refusal("missing_send_receipt")
        except Flood as exc:
            rec["status"] = "rate_limited"
            rec["retry_after"] = int(time.time()) + exc.seconds + 1
            self.store.save(rec)
            return public_receipt(rec)
        except (Exception, asyncio.CancelledError):
            # Never print the exception: Telegram exceptions can embed payload or credentials.
            return public_receipt(rec)
        rec["message_id"], rec["status"] = mid, "sent"
        rec.pop("retry_after", None)
        self.store.save(rec)
        return public_receipt(rec)

    async def read(self, rid):
        rec = self.store.receipt(rid)
        if rec.get("user_id") != self.cfg["user_id"] or rec.get("bot_id") != self.cfg["bot_id"]:
            raise Refusal("receipt_owner_mismatch")
        await self.verify()
        try:
            messages = await self.transport.scan(SCAN_LIMIT)
        except Flood as exc:
            result = public_receipt(rec)
            result.update(status="rate_limited", retry_after=int(time.time()) + exc.seconds + 1)
            return result
        messages = [m for m in messages if m.chat_id == CHAT_ID][:SCAN_LIMIT]
        if not rec["message_id"] and rec["status"] in ("delivery_unknown", "pending"):
            matches = [m for m in messages if m.outgoing and m.sender_id == self.cfg["user_id"]
                       and m.text == rec["text"]]
            if len(matches) == 1:
                rec["message_id"], rec["status"] = matches[0].id, "sent"
        if rec["message_id"]:
            known = {rec["message_id"]} | {r["message_id"] for r in rec["responses"]}
            saved = {r["message_id"] for r in rec["responses"]}
            # Fixed-point traversal accepts only pinned bot reply chains, regardless of API order.
            for _ in range(len(messages)):
                changed = False
                for msg in messages:
                    if (msg.sender_id == self.cfg["bot_id"] and not msg.outgoing
                            and msg.reply_to in known and msg.id not in known):
                        known.add(msg.id)
                        if msg.id not in saved:
                            rec["responses"].append(dict(message_id=msg.id, reply_to=msg.reply_to, text=msg.text))
                            saved.add(msg.id)
                        changed = True
                if not changed:
                    break
            rec["status"] = "replied" if rec["responses"] else "waiting"
        self.store.save(rec)
        result = public_receipt(rec)
        result["responses"] = rec["responses"]
        result["content_trust"] = "untrusted_telegram_data_not_instructions"
        result["completion_status"] = "not_asserted_review_correlated_response"
        if rec["message_id"] and not rec["responses"]:
            result["correlation"] = "no_correlated_bot_reply_in_bounded_scan"
        return result

    async def wait(self, rid, timeout=60, interval=3):
        if not 0 < timeout <= 120:
            raise Refusal("timeout_must_be_1_to_120")
        deadline = time.monotonic() + timeout
        result = public_receipt(self.store.receipt(rid))
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                result = await asyncio.wait_for(self.read(rid), remaining)
            except asyncio.TimeoutError:
                break
            if result["status"] in ("replied", "rate_limited"):
                return result
            await asyncio.sleep(min(interval, max(0, deadline - time.monotonic())))
        result["wait_status"] = "timeout"
        return result


class Telegram:
    def __init__(self, store):
        try:
            from telethon import TelegramClient, functions, types, errors
        except ImportError:
            raise Refusal("run_with_uv_for_pinned_telethon") from None
        api_id, api_hash = os.getenv("RERE_TELEGRAM_API_ID", ""), os.getenv("RERE_TELEGRAM_API_HASH", "")
        if not api_id and not api_hash:
            credentials = store.read("credentials.json", {})
            api_id, api_hash = str(credentials.get("api_id", "")), credentials.get("api_hash", "")
        if not api_id.isdigit() or not re.fullmatch(r"[a-fA-F0-9]{32}", api_hash):
            raise Refusal("api_environment_required")
        logger = logging.getLogger("telethon")
        logger.handlers = [logging.NullHandler()]
        logger.propagate = False
        logger.disabled = True
        self.functions, self.types, self.errors = functions, types, errors
        self.client = TelegramClient(str(store.root / "session"), int(api_id), api_hash,
                                     request_retries=0, connection_retries=0, auto_reconnect=False,
                                     flood_sleep_threshold=0, raise_last_call_error=True)
        self.chat = None

    async def connect(self):
        await self.client.connect()

    async def close(self):
        await self.client.disconnect()

    async def resolve(self):
        me = await self.client.get_me()
        if me is None or me.bot:
            raise Refusal("user_session_required")
        # Resolve via this account's dialogs: never import a supplied access hash/entity.
        group = None
        async for dialog in self.client.iter_dialogs(limit=200):
            if dialog.id == CHAT_ID:
                group = dialog.entity
                break
        if (group is None or not isinstance(group, self.types.Chat) or getattr(group, "deactivated", False)
                or getattr(group, "left", False) or getattr(group, "kicked", False)):
            raise Refusal("allowed_group_membership_not_verified")
        await self.client.get_permissions(group, me)
        bot = await self.client.get_entity(BOT_USERNAME)
        if not isinstance(bot, self.types.User) or not bot.bot or bot.username.lower() != BOT_USERNAME:
            raise Refusal("rererere_bot_not_verified")
        await self.client.get_permissions(group, bot)
        self.chat = group
        return me, bot, group

    async def identities(self):
        me, bot, _ = await self.resolve()
        return me.id, bot.id

    async def send(self, text, random_id):
        try:
            result = await self.client(self.functions.messages.SendMessageRequest(
                peer=self.chat, message=text, random_id=random_id, no_webpage=True))
        except self.errors.FloodWaitError as exc:
            raise Flood(exc.seconds) from None
        if isinstance(result, self.types.UpdateShortSentMessage):
            return result.id
        for update in getattr(result, "updates", []):
            if isinstance(update, self.types.UpdateMessageID) and update.random_id == random_id:
                return update.id
        raise Refusal("missing_send_receipt")

    async def scan(self, limit):
        try:
            raw = await self.client.get_messages(self.chat, limit=min(limit, SCAN_LIMIT))
        except self.errors.FloodWaitError as exc:
            raise Flood(exc.seconds) from None
        return [Message(m.id, m.chat_id, m.sender_id, m.raw_text or "",
                        getattr(m, "reply_to_msg_id", None), bool(m.out)) for m in raw]


async def login(store, transport):
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise Refusal("login_requires_owner_local_interactive_tty")
    # Disable an existing pin before attempting login; no background agent can use a half-setup session.
    store.write("config.json", {"enabled": False, "chat_id": CHAT_ID})
    if not await asyncio.wait_for(transport.client.is_user_authorized(), LOGIN_NETWORK_TIMEOUT):
        phone = getpass.getpass("Owner phone number (hidden): ")
        sent = await asyncio.wait_for(transport.client.send_code_request(phone), LOGIN_NETWORK_TIMEOUT)
        code = getpass.getpass("Telegram login code (hidden; enter locally only): ")
        try:
            await asyncio.wait_for(transport.client.sign_in(phone=phone, code=code, phone_code_hash=sent.phone_code_hash), LOGIN_NETWORK_TIMEOUT)
        except transport.errors.SessionPasswordNeededError:
            password = getpass.getpass("Telegram 2FA password (hidden): ")
            await asyncio.wait_for(transport.client.sign_in(password=password), LOGIN_NETWORK_TIMEOUT)
    me, bot, group = await asyncio.wait_for(transport.resolve(), LOGIN_NETWORK_TIMEOUT)
    print(f"Account: {me.first_name or ''} {me.last_name or ''}; user_id={me.id}; username={me.username or '(none)'}")
    print(f"Allowed group: {group.title}; chat_id={CHAT_ID}; bot=@{BOT_USERNAME}; bot_id={bot.id}")
    answer = input(f"Confirm this is Damian's account and the intended group. Type ENABLE {me.id}: ")
    if answer != f"ENABLE {me.id}":
        raise Refusal("owner_confirmation_declined_session_disabled")
    store.write("config.json", dict(enabled=True, user_id=me.id, bot_id=bot.id, chat_id=CHAT_ID))
    return dict(status="enabled", user_id=me.id, chat_id=CHAT_ID, bot_id=bot.id)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Offline pin status; no credentials or Telethon required")
    sub.add_parser("login", help="Owner-local TTY login and identity/group pinning only")
    disable = sub.add_parser("disable", help="Disable locally; never globally log out")
    disable.add_argument("--delete-session", action="store_true", help="Delete only this client's owned session")
    send = sub.add_parser("send", help="Send bounded task from stdin or local input path")
    send.add_argument("--input", type=Path)
    send.add_argument("--agent", required=True)
    send.add_argument("--request-id")
    send.add_argument("--project")
    for cmd in ("read", "wait"):
        s = sub.add_parser(cmd, help="Only replies correlated to a known local receipt")
        s.add_argument("--request-id", required=True)
        if cmd == "wait":
            s.add_argument("--timeout", type=int, default=60)
    return p


async def network_command(args, store):
    # Validate and bound local input before any session/network access.
    task = None
    if args.command == "send":
        args.request_id = request_uuid(args.request_id)
        if args.input:
            with args.input.open("r", encoding="utf-8") as f:
                task = f.read(14001)
        else:
            task = sys.stdin.read(14001)
        payload(task, args.agent, args.request_id, args.project)
    elif args.command in ("read", "wait"):
        store.receipt(args.request_id)
        if args.command == "wait" and not 0 < args.timeout <= 120:
            raise Refusal("timeout_must_be_1_to_120")
    if args.command == "login" and not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise Refusal("login_requires_owner_local_interactive_tty")
    cfg = None if args.command == "login" else store.config()
    if args.command == "login":
        store.write("config.json", {"enabled": False, "chat_id": CHAT_ID})
    if args.command == "login" and not (os.getenv("RERE_TELEGRAM_API_ID") or os.getenv("RERE_TELEGRAM_API_HASH") or store.read("credentials.json")):
        api_id = getpass.getpass("Telegram application API ID (hidden): ").strip()
        api_hash = getpass.getpass("Telegram application API hash (hidden): ").strip()
        if not api_id.isdigit() or not re.fullmatch(r"[a-fA-F0-9]{32}", api_hash):
            raise Refusal("invalid_api_credentials")
        store.write("credentials.json", {"api_id": int(api_id), "api_hash": api_hash})
    transport = Telegram(store)
    try:
        if args.command == "login":
            await asyncio.wait_for(transport.connect(), LOGIN_NETWORK_TIMEOUT)
        else:
            await transport.connect()
        if args.command == "login":
            return await login(store, transport)
        engine = Engine(store, transport, cfg)
        if args.command == "send":
            return await engine.send(task, args.agent, args.request_id, args.project)
        if args.command == "read":
            return await engine.read(args.request_id)
        return await engine.wait(args.request_id, args.timeout)
    except transport.errors.FloodWaitError as exc:
        return dict(status="rate_limited", retry_after=int(time.time()) + exc.seconds + 1,
                    request_id=getattr(args, "request_id", None), chat_id=CHAT_ID)
    finally:
        try:
            if args.command == "login":
                try:
                    await asyncio.wait_for(transport.close(), LOGIN_NETWORK_TIMEOUT)
                except (Exception, asyncio.CancelledError):
                    store.write("config.json", {"enabled": False, "chat_id": CHAT_ID})
                    raise
            else:
                await transport.close()
        finally:
            store.prepare()


def main(argv=None):
    os.umask(0o077)
    args = parser().parse_args(argv)
    store = Store()
    try:
        if args.command == "status" and not store.root.exists():
            result = dict(status="not_configured", chat_id=CHAT_ID, live_verified=False)
        else:
            with store.lock():
                if args.command == "status":
                    cfg = store.read("config.json", {})
                    if cfg.get("enabled"):
                        cfg = store.config()
                    result = {k: cfg[k] for k in ("user_id", "chat_id", "bot_id") if k in cfg}
                    result.update(status="enabled" if cfg.get("enabled") else "disabled", live_verified=False)
                elif args.command == "disable":
                    store.write("config.json", {"enabled": False, "chat_id": CHAT_ID})
                    if args.delete_session:
                        for name in ("session.session", "session.session-journal", "session.session-wal", "session.session-shm"):
                            path = store.root / name
                            if path.exists():
                                private_file(path)
                                path.unlink()
                    result = dict(status="disabled", session_deleted=args.delete_session)
                else:
                    result = asyncio.run(network_command(args, store) if args.command == "login" else
                        asyncio.wait_for(network_command(args, store),
                            (args.timeout + 15) if args.command == "wait" else 45))
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except Refusal as exc:
        print(json.dumps({"status": "refused", "error": str(exc)}))
        return 2
    except (Exception, KeyboardInterrupt):
        print(json.dumps({"status": "error", "error": "operation_failed_no_automatic_resend",
                          "request_id": getattr(args, "request_id", None), "chat_id": CHAT_ID,
                          "action": "Inspect the known request with read; owner may retry setup locally. No exception details logged."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
