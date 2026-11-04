#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["Telethon==1.42.0"]
# ///
"""Offline adapter contract tests against real pinned Telethon types. No API calls."""
import asyncio
import importlib.util
from pathlib import Path
import os
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

try:
    import telethon
    from telethon import types, functions, errors
except ImportError:
    telethon = None
    types = functions = errors = None

spec = importlib.util.spec_from_file_location("rere_adapter", Path(__file__).resolve().parents[1] / "scripts/delegate_to_rere.py")
assert spec is not None and spec.loader is not None
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


@unittest.skipIf(telethon is None, "Run with uv run --script tests/test_telethon_adapter.py for pinned adapter tests")
class AdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.tmp.cleanup)
        self.store = m.Store(self.tmp.name)
        self.store.prepare()
        self.client = AsyncMock()
        self.client.get_me.return_value = types.User(id=111, first_name="Damian")
        self.bot = types.User(id=222, bot=True, username=m.BOT_USERNAME)
        self.group = types.Chat(id=5422814811, title="Group", photo=types.ChatPhotoEmpty(),
                                participants_count=2, date=None, version=1)
        self.client.get_entity.return_value = self.bot
        self.set_dialogs([SimpleNamespace(id=m.CHAT_ID, entity=self.group)])
        with patch.dict(os.environ, {"RERE_TELEGRAM_API_ID": "12345", "RERE_TELEGRAM_API_HASH": "0" * 32}):
            with patch.object(telethon, "TelegramClient", return_value=self.client) as constructor:
                self.transport = m.Telegram(self.store)
        kwargs = constructor.call_args.kwargs
        self.assertEqual(kwargs["request_retries"], 0)
        self.assertEqual(kwargs["flood_sleep_threshold"], 0)
        self.assertFalse(kwargs["auto_reconnect"])

    def set_dialogs(self, dialogs):
        async def generate(**kwargs):
            assert kwargs["limit"] == 200
            for dialog in dialogs:
                yield dialog
        self.client.iter_dialogs = generate

    async def test_real_type_resolution_and_both_memberships(self):
        self.assertEqual(await self.transport.identities(), (111, 222))
        self.assertEqual(self.client.get_permissions.await_count, 2)
        self.assertIs(self.transport.chat, self.group)

    async def test_wrong_group_no_fallback(self):
        self.set_dialogs([SimpleNamespace(id=-999, entity=self.group)])
        with self.assertRaisesRegex(m.Refusal, "membership_not_verified"):
            await self.transport.identities()
        self.client.get_entity.assert_not_awaited()

    async def test_bot_identity_and_membership_required(self):
        self.client.get_entity.return_value = types.User(id=222, bot=False, username=m.BOT_USERNAME)
        with self.assertRaisesRegex(m.Refusal, "bot_not_verified"):
            await self.transport.identities()
        self.client.get_entity.return_value = self.bot
        self.client.get_permissions.side_effect = errors.UserNotParticipantError(None)
        with self.assertRaises(errors.UserNotParticipantError):
            await self.transport.identities()

    async def test_raw_send_request_fixed_peer_and_random_id(self):
        await self.transport.identities()
        self.client.return_value = types.UpdateShortSentMessage(id=10, pts=1, pts_count=1, date=None, out=True)
        self.assertEqual(await self.transport.send("safe task", 123), 10)
        request = self.client.call_args.args[0]
        self.assertIsInstance(request, functions.messages.SendMessageRequest)
        self.assertIs(request.peer, self.group)
        self.assertEqual(request.random_id, 123)
        self.assertTrue(request.no_webpage)

    async def test_update_message_id_and_flood_mapping(self):
        self.client.return_value = types.Updates(updates=[types.UpdateMessageID(id=44, random_id=123)],
                                                users=[], chats=[], date=None, seq=1)
        self.assertEqual(await self.transport.send("safe task", 123), 44)
        self.client.side_effect = errors.FloodWaitError(None, capture=900)
        with self.assertRaises(m.Flood) as raised:
            await self.transport.send("safe task", 123)
        self.assertEqual(raised.exception.seconds, 900)


if __name__ == "__main__":
    unittest.main()
