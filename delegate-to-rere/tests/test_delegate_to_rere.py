#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Offline tests: no Telegram credentials, sessions, or network needed."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/delegate_to_rere.py"
spec = importlib.util.spec_from_file_location("delegate_to_rere", SCRIPT)
assert spec is not None and spec.loader is not None
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class Fake:
    def __init__(self):
        self.uid, self.bid = 111, 222
        self.calls = []
        self.messages = []
        self.failure: BaseException | None = None
        self.scans = 0

    async def identities(self):
        return self.uid, self.bid

    async def send(self, text, random_id):
        self.calls.append((text, random_id))
        if self.failure:
            raise self.failure
        return 10

    async def scan(self, limit):
        assert limit <= 100
        self.scans += 1
        return self.messages[:limit]


class CoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rere-test-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.tmp.cleanup)
        self.store = m.Store(Path(self.tmp.name) / "state")
        self.store.prepare()
        self.cfg = dict(enabled=True, chat_id=m.CHAT_ID, user_id=111, bot_id=222)
        self.store.write("config.json", self.cfg)
        self.fake = Fake()
        self.engine = m.Engine(self.store, self.fake, self.cfg)
        self.rid = str(uuid.uuid4())

    async def send(self):
        return await self.engine.send("Set up an approved 33GOD project integration.", "codex", self.rid)

    async def test_send_receipt_and_idempotent_retry(self):
        with self.store.lock():
            first = await self.send()
            second = await self.send()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "sent")
        self.assertEqual(first["chat_id"], m.CHAT_ID)
        self.assertEqual(len(self.fake.calls), 1)
        text = self.fake.calls[0][0]
        self.assertIn("On behalf of Damian; agent-generated request, not Damian-written", text)
        self.assertIn("@colrerererebot", text)
        self.assertIn(self.rid, text)

    async def test_uuid_minted(self):
        result = await self.engine.send("33GOD setup", "claude")
        self.assertEqual(str(uuid.UUID(result["request_id"])), result["request_id"])

    async def test_same_id_different_task_refused(self):
        await self.send()
        with self.assertRaisesRegex(m.Refusal, "payload_conflict"):
            await self.engine.send("Different task", "codex", self.rid)
        self.assertEqual(len(self.fake.calls), 1)

    async def test_identity_mismatch(self):
        for uid, bid in ((999, 222), (111, 333)):
            self.fake.uid, self.fake.bid = uid, bid
            with self.assertRaisesRegex(m.Refusal, "identity_mismatch"):
                await self.send()
        self.assertFalse(self.fake.calls)

    async def test_forbidden_route(self):
        self.cfg["chat_id"] = -999
        self.store.write("config.json", self.cfg)
        with self.assertRaisesRegex(m.Refusal, "forbidden_route"):
            self.store.config()
        with self.assertRaisesRegex(m.Refusal, "forbidden_route"):
            m.Engine(self.store, self.fake, self.cfg)

    async def test_secret_refusal(self):
        samples = ["-----BEGIN " + "PRIVATE" + " KEY-----", str(123456789) + ":" + "A" * 35,
                   "api_hash=abc123", "password: nope", "ops_" + "a" * 40,
                   "Bearer " + "z" * 30, "sk-" + "t" * 35]
        for sample in samples:
            with self.subTest(sample=sample[:12]):
                with self.assertRaisesRegex(m.Refusal, "possible_secret"):
                    await self.engine.send(sample, "agent")
        self.assertFalse(self.fake.calls)

    async def test_utf16_and_no_truncation(self):
        self.assertEqual(m.utf16_units("😀"), 2)
        overhead = m.utf16_units(m.payload("x", "agent", self.rid)) - 1
        self.assertEqual(m.utf16_units(m.payload("x" * (3500 - overhead), "agent", self.rid)), 3500)
        with self.assertRaisesRegex(m.Refusal, "too_long"):
            await self.engine.send("😀" * 1800, "agent")
        with self.assertRaisesRegex(m.Refusal, "too_long"):
            m.payload(" " * 14001 + "safe", "agent", self.rid)
        self.assertFalse(self.fake.calls)

    async def test_delivery_unknown_does_not_resend_reconciles_own_marker(self):
        self.fake.failure = ConnectionError("fake sensitive exception must never escape")
        result = await self.send()
        self.assertEqual(result["status"], "delivery_unknown")
        self.assertEqual((await self.send())["status"], "delivery_unknown")
        self.assertEqual(len(self.fake.calls), 1)
        text = self.fake.calls[0][0]
        self.fake.messages = [m.Message(9, m.CHAT_ID, 444, text, outgoing=True),
                              m.Message(8, -999, 111, text, outgoing=True)]
        self.assertEqual((await self.engine.read(self.rid))["status"], "delivery_unknown")
        self.fake.messages.append(m.Message(10, m.CHAT_ID, 111, text, outgoing=True))
        result = await self.engine.read(self.rid)
        self.assertEqual(result["message_id"], 10)
        self.assertEqual(result["status"], "waiting")
        self.assertEqual(len(self.fake.calls), 1)

    async def test_crash_persisted_uncertainty(self):
        self.fake.failure = asyncio.CancelledError()
        self.assertEqual((await self.send())["status"], "delivery_unknown")
        rec = self.store.receipt(self.rid)
        self.assertEqual(rec["status"], "delivery_unknown")
        self.assertGreater(rec["random_id"], 0)

    async def test_bot_reply_chain_only_no_incidental_group_content(self):
        await self.send()
        self.fake.messages = [m.Message(13, m.CHAT_ID, 222, "second", 12),
                              m.Message(12, m.CHAT_ID, 222, "first", 10),
                              m.Message(14, m.CHAT_ID, 999, "wrong sender", 10),
                              m.Message(15, -999, 222, "wrong chat", 10),
                              m.Message(16, m.CHAT_ID, 222, "uncorrelated complete " + self.rid),
                              m.Message(17, m.CHAT_ID, 222, "through wrong sender", 14)]
        result = await self.engine.read(self.rid)
        self.assertEqual(result["status"], "replied")
        self.assertEqual({r["text"] for r in result["responses"]}, {"first", "second"})
        self.assertEqual(result["completion_status"], "not_asserted_review_correlated_response")
        stored = (self.store.root / f"request-{self.rid}.json").read_text()
        for forbidden in ("wrong sender", "wrong chat", "uncorrelated complete", "through wrong sender"):
            self.assertNotIn(forbidden, stored)

    async def test_uncorrelated_text_is_waiting_not_success(self):
        await self.send()
        self.fake.messages = [m.Message(20, m.CHAT_ID, 222, "Completed " + self.rid)]
        result = await self.engine.read(self.rid)
        self.assertEqual(result["status"], "waiting")
        self.assertEqual(result["responses"], [])
        self.assertIn("no_correlated", result["correlation"])

    async def test_timeout_no_resend(self):
        await self.send()
        result = await self.engine.wait(self.rid, timeout=0.02, interval=0.005)
        self.assertEqual(result["wait_status"], "timeout")
        self.assertEqual(len(self.fake.calls), 1)
        self.assertGreater(self.fake.scans, 0)
        with self.assertRaises(m.Refusal):
            await self.engine.wait(self.rid, timeout=121)

    async def test_unknown_request_and_wrong_receipt_chat(self):
        with self.assertRaisesRegex(m.Refusal, "unknown_request"):
            await self.engine.read(self.rid)
        await self.send()
        rec = self.store.receipt(self.rid)
        rec["chat_id"] = -999
        self.store.save(rec)
        with self.assertRaisesRegex(m.Refusal, "invalid_receipt_route"):
            await self.engine.read(self.rid)

    async def test_receipt_account_mismatch(self):
        await self.send()
        self.cfg["user_id"] = 333
        with self.assertRaisesRegex(m.Refusal, "receipt_owner_mismatch"):
            await self.engine.read(self.rid)

    async def test_flood_wait_no_sleep_or_early_retry(self):
        self.fake.failure = m.Flood(600)
        result = await self.send()
        self.assertEqual(result["status"], "rate_limited")
        self.assertGreater(result["retry_after"], m.time.time() + 590)
        await self.send()
        self.assertEqual(len(self.fake.calls), 1)
        rec = self.store.receipt(self.rid)
        rec["retry_after"] = 0
        self.store.save(rec)
        self.fake.failure = None
        self.assertEqual((await self.send())["status"], "sent")
        self.assertEqual(self.fake.calls[0][1], self.fake.calls[1][1])

    async def test_permissions_and_symlink_refused(self):
        await self.send()
        self.assertEqual(self.store.root.stat().st_mode & 0o777, 0o700)
        for path in self.store.root.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        (self.store.root / "bad").symlink_to(self.store.root / "config.json")
        with self.assertRaisesRegex(m.Refusal, "symlink"):
            self.store.prepare()

    async def test_concurrent_same_request_process_blocked(self):
        child = ("import importlib.util,sys; "
                 "s=importlib.util.spec_from_file_location('cli',sys.argv[1]); "
                 "m=importlib.util.module_from_spec(s);sys.modules['cli']=m;s.loader.exec_module(m); "
                 "store=m.Store(sys.argv[2]); "
                 "exec('try:\\n with store.lock(): print(\\\"UNEXPECTED\\\")\\nexcept m.Refusal as e: print(str(e))')")
        with self.store.lock():
            await self.send()
            result = subprocess.run([sys.executable, "-c", child, str(SCRIPT), str(self.store.root)],
                                    text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("client_busy", result.stdout)
        self.assertEqual(len(self.fake.calls), 1)

    async def test_login_pins_only_after_owner_confirmation(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock
        me = SimpleNamespace(id=111, first_name="Damian", last_name=None, username="owner")
        bot = SimpleNamespace(id=222)
        group = SimpleNamespace(title="Intended group")
        transport = SimpleNamespace(client=SimpleNamespace(is_user_authorized=AsyncMock(return_value=True)),
                                    resolve=AsyncMock(return_value=(me, bot, group)))
        with patch.object(sys.stdin, "isatty", return_value=True), patch.object(sys.stdout, "isatty", return_value=True):
            with patch("builtins.input", return_value="no"):
                with self.assertRaisesRegex(m.Refusal, "confirmation_declined"):
                    await m.login(self.store, transport)
            self.assertFalse(self.store.read("config.json")["enabled"])
            with patch("builtins.input", return_value="ENABLE 111"):
                result = await m.login(self.store, transport)
        self.assertEqual(result["status"], "enabled")
        self.assertEqual(self.store.config(), self.cfg)
        self.assertNotIn("api_hash", self.store.read("config.json"))

    async def test_login_network_awaits_bounded_prompts_unbounded(self):
        # Accelerate only network deadlines; sleep longer than that at every owner prompt.
        original_wait_for = asyncio.wait_for
        deadlines = []

        async def short_network_deadline(coro, timeout):
            deadlines.append(timeout)
            self.assertEqual(timeout, 45)
            return await original_wait_for(coro, 0.01)

        def slow_prompt(label):
            time.sleep(0.025)
            return {"Owner phone number (hidden): ": "+15550000000",
                    "Telegram login code (hidden; enter locally only): ": "123456",
                    "Telegram 2FA password (hidden): ": "private-password"}[label]

        me = SimpleNamespace(id=111, first_name="Damian", last_name=None, username="owner")
        bot = SimpleNamespace(id=222)
        group = SimpleNamespace(title="Intended group")
        password_needed = type("PasswordNeeded", (Exception,), {})
        client = SimpleNamespace(is_user_authorized=AsyncMock(return_value=False),
                                 send_code_request=AsyncMock(return_value=SimpleNamespace(phone_code_hash="hash")),
                                 sign_in=AsyncMock(side_effect=[password_needed(), None]))
        transport = SimpleNamespace(client=client, errors=SimpleNamespace(SessionPasswordNeededError=password_needed),
                                    connect=AsyncMock(), close=AsyncMock(),
                                    resolve=AsyncMock(return_value=(me, bot, group)))
        self.store.write("credentials.json", {"api_id": 12345, "api_hash": "0" * 32})
        with patch.object(sys.stdin, "isatty", return_value=True), patch.object(sys.stdout, "isatty", return_value=True), patch.object(m, "Telegram", return_value=transport):
            with patch.object(m.asyncio, "wait_for", side_effect=short_network_deadline), patch.object(m.getpass, "getpass", side_effect=slow_prompt), patch("builtins.input", side_effect=lambda _: (time.sleep(0.025), "ENABLE 111")[1]):
                result = await m.network_command(SimpleNamespace(command="login"), self.store)
        self.assertEqual(result["status"], "enabled")
        self.assertEqual(deadlines, [45] * 7)  # connect, authorization, code, code sign-in, 2FA, resolve, close
        self.assertEqual(client.sign_in.await_args_list[1].kwargs, {"password": "private-password"})
        self.assertEqual(self.store.config(), self.cfg)

    async def test_login_network_timeout_sanitized_and_pin_disabled(self):
        original_wait_for = asyncio.wait_for

        async def short_network_deadline(coro, timeout):
            self.assertEqual(timeout, 45)
            return await original_wait_for(coro, 0.01)

        async def stalls(*args, **kwargs):
            await asyncio.sleep(1)

        me = SimpleNamespace(id=111, first_name="Damian", last_name=None, username="owner")
        for operation in ("connect", "is_user_authorized", "send_code_request", "sign_in", "resolve", "close"):
            with self.subTest(operation=operation):
                self.store.write("config.json", self.cfg)
                self.store.write("credentials.json", {"api_id": 12345, "api_hash": "0" * 32})
                client = SimpleNamespace(is_user_authorized=AsyncMock(return_value=False),
                                         send_code_request=AsyncMock(return_value=SimpleNamespace(phone_code_hash="hash")),
                                         sign_in=AsyncMock())
                transport = SimpleNamespace(client=client,
                                            errors=SimpleNamespace(FloodWaitError=type("FloodWait", (Exception,), {}),
                                                                   SessionPasswordNeededError=type("PasswordNeeded", (Exception,), {})),
                                            connect=AsyncMock(), close=AsyncMock(),
                                            resolve=AsyncMock(return_value=(me, SimpleNamespace(id=222), SimpleNamespace(title="Group"))))
                target = getattr(client, operation, None) or getattr(transport, operation)
                target.side_effect = stalls
                with patch.object(m, "Telegram", return_value=transport), patch.object(m.asyncio, "wait_for", side_effect=short_network_deadline), patch.object(sys.stdin, "isatty", return_value=True), patch.object(sys.stdout, "isatty", return_value=True), patch.object(m.getpass, "getpass", side_effect=["+15550000000", "123456"]), patch("builtins.input", return_value="ENABLE 111"):
                    with self.assertRaises(asyncio.TimeoutError):
                        await m.network_command(SimpleNamespace(command="login"), self.store)
                self.assertFalse(self.store.read("config.json")["enabled"])
                transport.close.assert_awaited()

    async def test_owner_credentials_prompt_written_private_only(self):
        from types import SimpleNamespace
        # Stop before creating a real client: test only the local prompt/persistence boundary.
        args = SimpleNamespace(command="login")
        api_hash = "0" * 32
        with patch.dict(os.environ, {}, clear=True), patch.object(sys.stdin, "isatty", return_value=True), patch.object(sys.stdout, "isatty", return_value=True):
            with patch.object(m.getpass, "getpass", side_effect=["12345", api_hash]), patch.object(m, "Telegram", side_effect=m.Refusal("test_transport_stop")):
                with self.assertRaisesRegex(m.Refusal, "test_transport_stop"):
                    await m.network_command(args, self.store)
        creds = self.store.read("credentials.json")
        self.assertEqual(creds, {"api_id": 12345, "api_hash": api_hash})
        self.assertEqual((self.store.root / "credentials.json").stat().st_mode & 0o777, 0o600)
        self.assertNotIn("api_hash", self.store.read("config.json"))

    async def test_disable_session_only_preserves_receipts_and_credentials(self):
        await self.send()
        self.store.write("credentials.json", {"api_id": 1, "api_hash": "0" * 32})
        (self.store.root / "session.session").write_bytes(b"test fixture, not a session")
        with patch.object(m, "DEFAULT_ROOT", self.store.root):
            # Store's default was bound at definition; replace only the constructor for this local test.
            with patch.object(m, "Store", return_value=self.store):
                self.assertEqual(m.main(["disable", "--delete-session"]), 0)
        self.assertFalse((self.store.root / "session.session").exists())
        self.assertFalse(self.store.read("config.json")["enabled"])
        self.assertTrue(self.store.receipt(self.rid))
        self.assertTrue(self.store.read("credentials.json"))

    async def test_missing_send_id_remains_unknown(self):
        from unittest.mock import AsyncMock
        self.fake.send = AsyncMock(return_value=None)
        result = await self.send()
        self.assertEqual(result["status"], "delivery_unknown")
        self.assertEqual((await self.send())["status"], "delivery_unknown")
        self.assertEqual(self.fake.send.await_count, 1)

    async def test_offline_cli_help_status_and_non_tty_login(self):
        env = dict(os.environ, HOME=self.tmp.name)
        env.pop("RERE_TELEGRAM_API_ID", None)
        env.pop("RERE_TELEGRAM_API_HASH", None)
        for command in (["--help"], ["status"]):
            p = subprocess.run([sys.executable, str(SCRIPT), *command], env=env,
                               text=True, capture_output=True, timeout=10)
            self.assertEqual(p.returncode, 0, p.stderr)
            if command == ["status"]:
                self.assertEqual(json.loads(p.stdout)["status"], "not_configured")
        p = subprocess.run([sys.executable, str(SCRIPT), "login"], input="",
                           env=env, text=True, capture_output=True, timeout=10)
        self.assertEqual(p.returncode, 2)
        self.assertIn("owner_local_interactive_tty", p.stdout)
        self.assertFalse((Path(self.tmp.name) / ".local/state/delegate-to-rere/session.session").exists())


class LoginMainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rere-login-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.tmp.cleanup)
        self.store = m.Store(Path(self.tmp.name) / "state")
        self.store.prepare()

    def test_main_login_does_not_wrap_prompts_in_global_deadline(self):
        async def login_command(args, store):
            self.assertEqual(args.command, "login")
            self.assertIs(store, self.store)
            return {"status": "enabled"}

        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with patch.object(m, "Store", return_value=self.store), patch.object(m, "network_command", side_effect=login_command), patch.object(m.asyncio, "wait_for", side_effect=AssertionError("global deadline")), redirect_stdout(output):
            self.assertEqual(m.main(["login"]), 0)
        self.assertEqual(json.loads(output.getvalue()), {"status": "enabled"})

    def test_main_network_timeout_hides_exception_and_credentials(self):
        from contextlib import redirect_stdout
        from io import StringIO
        self.store.write("credentials.json", {"api_id": 12345, "api_hash": "0" * 32})
        secret = "private-password-123456"

        async def stalls():
            await asyncio.sleep(1)

        transport = SimpleNamespace(connect=AsyncMock(side_effect=stalls), close=AsyncMock(),
                                    errors=SimpleNamespace(FloodWaitError=type("FloodWait", (Exception,), {})))
        original_wait_for = asyncio.wait_for

        async def short_network_deadline(coro, timeout):
            self.assertEqual(timeout, 45)
            return await original_wait_for(coro, 0.01)

        output = StringIO()
        with patch.object(m, "Store", return_value=self.store), patch.object(m, "Telegram", return_value=transport), patch.object(m.asyncio, "wait_for", side_effect=short_network_deadline), patch.object(sys.stdin, "isatty", return_value=True), redirect_stdout(output):
            with patch.object(sys.stdout, "isatty", return_value=True):
                self.assertEqual(m.main(["login"]), 1)
        self.assertEqual(json.loads(output.getvalue())["error"], "operation_failed_no_automatic_resend")
        self.assertNotIn(secret, output.getvalue())
        self.assertFalse(self.store.read("config.json")["enabled"])
        transport.close.assert_awaited_once()

    def test_main_network_exception_text_not_exposed(self):
        from contextlib import redirect_stdout
        from io import StringIO
        self.store.write("credentials.json", {"api_id": 12345, "api_hash": "a" * 32})
        secret = "private-api-hash-" + "a" * 32
        transport = SimpleNamespace(connect=AsyncMock(side_effect=RuntimeError(secret)), close=AsyncMock(),
                                    errors=SimpleNamespace(FloodWaitError=type("FloodWait", (Exception,), {})))
        output = StringIO()
        with patch.object(m, "Store", return_value=self.store), patch.object(m, "Telegram", return_value=transport), patch.object(sys.stdin, "isatty", return_value=True), redirect_stdout(output):
            with patch.object(sys.stdout, "isatty", return_value=True):
                self.assertEqual(m.main(["login"]), 1)
        self.assertEqual(json.loads(output.getvalue())["error"], "operation_failed_no_automatic_resend")
        self.assertNotIn(secret, output.getvalue())
        self.assertFalse(self.store.read("config.json")["enabled"])


if __name__ == "__main__":
    unittest.main()
