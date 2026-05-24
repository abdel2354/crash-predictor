"""
Multi-Account Manager - Orchestrates multiple FF bot accounts.
Controls all bots from one place, with Telegram integration.
"""

import os
import sys
import json
import asyncio
import logging
import random
import time

from bot_worker import BotWorker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [Manager] %(levelname)s: %(message)s'
)
logger = logging.getLogger('manager')


class MultiAccountManager:
    """Manages multiple BotWorker instances."""

    def __init__(self):
        self.bots = []
        self.bot_tasks = []
        self.accounts_dir = "BIGBULL-ERA/ACCOUNTS"
        self.tokens_dir = "BIGBULL-ERA/TOKENS-JWT"

    def load_accounts(self, region=None):
        """Load all accounts from BIGBULL-ERA/ACCOUNTS/."""
        accounts = []
        if not os.path.exists(self.accounts_dir):
            logger.error(f"Accounts directory not found: {self.accounts_dir}")
            return accounts

        for filename in os.listdir(self.accounts_dir):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(self.accounts_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for acc in data:
                    acc_region = acc.get('region', 'ME')
                    if region and acc_region != region:
                        continue
                    accounts.append(acc)
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")

        logger.info(f"Loaded {len(accounts)} accounts")
        return accounts

    async def login_all(self, region=None, max_concurrent=3, delay_between=5):
        """Login all accounts with rate limiting."""
        accounts = self.load_accounts(region)
        if not accounts:
            logger.error("No accounts to login")
            return []

        results = []
        for i, acc in enumerate(accounts):
            uid = acc['uid']
            password = acc['password']
            name = acc.get('name', f'Bot-{i}')
            acc_region = acc.get('region', 'ME')

            logger.info(f"[{i+1}/{len(accounts)}] Logging in {name} (UID: {uid})...")

            bot = BotWorker(uid=uid, password=password, region=acc_region, name=name)

            success = await bot.login()
            if success:
                self.bots.append(bot)
                results.append({"name": name, "uid": uid, "status": "online"})
                logger.info(f"{name} logged in successfully!")
            else:
                results.append({"name": name, "uid": uid, "status": bot.status})
                logger.error(f"{name} login failed: {bot.status}")

            if i < len(accounts) - 1:
                wait = random.uniform(delay_between * 0.8, delay_between * 1.2)
                logger.info(f"Waiting {wait:.1f}s before next login...")
                await asyncio.sleep(wait)

        logger.info(f"Login complete: {len(self.bots)}/{len(accounts)} online")
        return results

    async def login_single(self, uid, password, region="ME", name="M3SBIOS"):
        """Login a single account."""
        bot = BotWorker(uid=uid, password=password, region=region, name=name)
        if await bot.login():
            self.bots.append(bot)
            return bot
        return None

    # ─── Guild Operations ───────────────────────────────────────────

    async def guild_join_all(self, guild_id, delay=2):
        """All bots join a guild."""
        results = []
        for i, bot in enumerate(self.bots):
            ok, msg = await bot.guild_join(guild_id)
            results.append({"name": bot.name, "success": ok, "message": msg[:50] if msg else ""})
            if i < len(self.bots) - 1:
                await asyncio.sleep(delay)
        return results

    async def guild_leave_all(self, guild_id, delay=2):
        """All bots leave a guild."""
        results = []
        for i, bot in enumerate(self.bots):
            ok, msg = await bot.guild_leave(guild_id)
            results.append({"name": bot.name, "success": ok, "message": msg[:50] if msg else ""})
            if i < len(self.bots) - 1:
                await asyncio.sleep(delay)
        return results

    async def guild_join_all_api(self, guild_id, delay=2):
        """All accounts join guild using API (no TCP needed)."""
        import aiohttp
        accounts = self.load_accounts()
        results = []
        for i, acc in enumerate(accounts):
            uid = acc['uid']
            pw = acc['password']
            name = acc.get('name', f'Bot-{i}')
            url = f"https://danger-guild-management-web.vercel.app/join?guild_id={guild_id}&uid={uid}&password={pw}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            result = await resp.text()
                            results.append({"name": name, "uid": uid, "success": True, "msg": result[:80]})
                            logger.info(f"{name} joined guild {guild_id}")
                        else:
                            results.append({"name": name, "uid": uid, "success": False, "msg": f"HTTP {resp.status}"})
            except Exception as e:
                results.append({"name": name, "uid": uid, "success": False, "msg": str(e)[:50]})

            if i < len(accounts) - 1:
                await asyncio.sleep(delay)

        success = sum(1 for r in results if r["success"])
        logger.info(f"Guild join: {success}/{len(results)} succeeded")
        return results

    # ─── Squad Operations ───────────────────────────────────────────

    async def form_squad(self, leader_index=0):
        """Form a squad: leader creates, others join."""
        if len(self.bots) < 2:
            return False, "Need at least 2 online bots"

        online_bots = [b for b in self.bots if b.connected]
        if len(online_bots) < 2:
            return False, "Need at least 2 connected bots"

        leader = online_bots[leader_index]
        members = online_bots[:4]  # Max 4 in squad
        members.remove(leader)

        # Leader creates squad
        logger.info(f"Leader {leader.name} creating squad...")
        await leader.create_squad()
        await asyncio.sleep(2)

        # Wait for squad code
        retries = 0
        while not leader.squad_code and retries < 10:
            await asyncio.sleep(1)
            retries += 1

        if not leader.squad_code:
            return False, "Could not get squad code"

        code = leader.squad_code
        logger.info(f"Squad code: {code}")

        # Members join
        joined = []
        for bot in members:
            logger.info(f"{bot.name} joining squad {code}...")
            await bot.join_squad(code)
            joined.append(bot.name)
            await asyncio.sleep(1.5)

        return True, {
            "leader": leader.name,
            "code": code,
            "members": joined,
            "total": len(joined) + 1
        }

    async def start_match_cycle(self, cycles=1, wait_time=120):
        """Level-up cycle: form squad → start match → wait → repeat."""
        online_bots = [b for b in self.bots if b.connected]
        if len(online_bots) < 2:
            return "Need at least 2 connected bots"

        results = []
        for cycle in range(cycles):
            logger.info(f"=== Match Cycle {cycle+1}/{cycles} ===")

            # Form squad
            ok, squad_info = await self.form_squad()
            if not ok:
                logger.error(f"Squad formation failed: {squad_info}")
                continue

            await asyncio.sleep(2)

            # Leader starts match
            leader = online_bots[0]
            await leader.start_match()
            logger.info(f"Match started by {leader.name}")

            # Wait for match to complete
            logger.info(f"Waiting {wait_time}s for match...")
            await asyncio.sleep(wait_time)

            # Leave squad
            for bot in online_bots[:4]:
                await bot.leave_squad()
                await asyncio.sleep(0.5)

            results.append({
                "cycle": cycle + 1,
                "leader": leader.name,
                "members": squad_info.get("members", []),
                "status": "completed"
            })

            if cycle < cycles - 1:
                cooldown = random.uniform(5, 15)
                logger.info(f"Cooldown {cooldown:.0f}s...")
                await asyncio.sleep(cooldown)

        return results

    # ─── Mass Likes ─────────────────────────────────────────────────

    async def mass_likes(self, target_uid, delay=1):
        """All accounts send likes to a target UID."""
        import aiohttp
        accounts = self.load_accounts()
        like_urls = [
            f"https://likes-api-1.vercel.app/like?uid={target_uid}",
            f"https://likes-api-2.vercel.app/like?uid={target_uid}",
        ]
        success = 0
        for i, acc in enumerate(accounts):
            try:
                url = like_urls[i % len(like_urls)]
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            success += 1
            except:
                pass
            await asyncio.sleep(delay)
        return {"target": target_uid, "sent": len(accounts), "success": success}

    # ─── Status ─────────────────────────────────────────────────────

    def get_all_status(self):
        """Get status of all bots."""
        return [bot.get_status() for bot in self.bots]

    def get_online_count(self):
        return sum(1 for b in self.bots if b.connected)

    async def disconnect_all(self):
        """Disconnect all bots."""
        for bot in self.bots:
            await bot.disconnect()
        self.bots.clear()
        logger.info("All bots disconnected")

    # ─── Run Background Tasks ───────────────────────────────────────

    async def start_all_listeners(self):
        """Start keep-alive and listeners for all connected bots."""
        tasks = []
        for bot in self.bots:
            if bot.connected:
                tasks.append(asyncio.create_task(bot.keep_alive_loop()))
                tasks.append(asyncio.create_task(bot.online_listener()))
        if tasks:
            self.bot_tasks = tasks
            logger.info(f"Started {len(tasks)} background tasks for {len(self.bots)} bots")


# ─── CLI Mode ───────────────────────────────────────────────────────

async def cli_main():
    """Interactive CLI for testing."""
    manager = MultiAccountManager()

    print("=" * 50)
    print("  FF Multi-Account Manager")
    print("=" * 50)
    print("\nCommands:")
    print("  login [region]     - Login all accounts")
    print("  status             - Show all bot statuses")
    print("  guildjoin <id>     - All bots join guild")
    print("  guildleave <id>    - All bots leave guild")
    print("  guildjoin_api <id> - Join guild via API (no TCP)")
    print("  squad              - Form squad")
    print("  match [cycles]     - Start match cycles")
    print("  disconnect         - Disconnect all")
    print("  quit               - Exit")
    print()

    while True:
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue

            action = cmd[0].lower()

            if action == "login":
                region = cmd[1] if len(cmd) > 1 else None
                results = await manager.login_all(region=region)
                for r in results:
                    status_icon = "✅" if r["status"] == "online" else "❌"
                    print(f"  {status_icon} {r['name']} (UID: {r['uid']}) — {r['status']}")

            elif action == "status":
                statuses = manager.get_all_status()
                if not statuses:
                    print("  No bots loaded")
                for s in statuses:
                    icon = "🟢" if s["connected"] else "🔴"
                    print(f"  {icon} {s['name']} | UID: {s['uid']} | {s['status']}")

            elif action == "guildjoin" and len(cmd) > 1:
                results = await manager.guild_join_all(cmd[1])
                for r in results:
                    icon = "✅" if r["success"] else "❌"
                    print(f"  {icon} {r['name']}: {r['message']}")

            elif action == "guildjoin_api" and len(cmd) > 1:
                results = await manager.guild_join_all_api(cmd[1])
                for r in results:
                    icon = "✅" if r["success"] else "❌"
                    print(f"  {icon} {r['name']}: {r['msg']}")

            elif action == "guildleave" and len(cmd) > 1:
                results = await manager.guild_leave_all(cmd[1])
                for r in results:
                    icon = "✅" if r["success"] else "❌"
                    print(f"  {icon} {r['name']}: {r['message']}")

            elif action == "squad":
                ok, info = await manager.form_squad()
                if ok:
                    print(f"  ✅ Squad formed! Code: {info['code']}")
                    print(f"  Leader: {info['leader']}")
                    print(f"  Members: {', '.join(info['members'])}")
                else:
                    print(f"  ❌ Failed: {info}")

            elif action == "match":
                cycles = int(cmd[1]) if len(cmd) > 1 else 1
                results = await manager.start_match_cycle(cycles=cycles)
                for r in results:
                    print(f"  ✅ Cycle {r['cycle']}: {r['status']}")

            elif action == "disconnect":
                await manager.disconnect_all()
                print("  All bots disconnected")

            elif action in ("quit", "exit"):
                await manager.disconnect_all()
                break

            else:
                print(f"  Unknown command: {action}")

        except KeyboardInterrupt:
            await manager.disconnect_all()
            break
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    asyncio.run(cli_main())
