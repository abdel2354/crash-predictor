"""
Multi-Account Manager - Orchestrates multiple FF bot accounts.
Controls all bots from one place, with Telegram integration.
Supports glory farming (guild join → squad → FS → wait → repeat).
"""

import os
import sys
import json
import asyncio
import logging
import random
import time
from datetime import datetime

from bot_worker import BotWorker
from xC4 import FS, DeCode_PackEt

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
        self.glory_running = False
        self.glory_task = None
        self.glory_stats = {
            "cycles": 0,
            "started_at": None,
            "guild_id": None,
            "squads_active": 0,
        }

    def load_accounts(self, region=None):
        """Load all accounts from BIGBULL-ERA/ACCOUNTS/."""
        accounts = []
        if not os.path.exists(self.accounts_dir):
            logger.error(f"Accounts directory not found: {self.accounts_dir}")
            return accounts

        for filename in sorted(os.listdir(self.accounts_dir)):
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
                # Start background listener for squad codes etc.
                bot._listener_task = asyncio.create_task(bot.online_listener())
                bot._keepalive_task = asyncio.create_task(bot.keep_alive_loop())
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
        """All online bots join a guild via TCP."""
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
        members = online_bots[:4]
        members = [b for b in members if b != leader]

        logger.info(f"Leader {leader.name} creating squad...")
        leader.squad_code = None
        await leader.create_squad()
        await asyncio.sleep(2)

        # Wait for online_listener to extract squad code
        retries = 0
        while not leader.squad_code and retries < 15:
            await asyncio.sleep(1)
            retries += 1

        if not leader.squad_code:
            return False, "Could not get squad code"

        code = leader.squad_code
        logger.info(f"Squad code: {code}")

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

    def _group_bots_by_region(self):
        """Group online bots by region (bots in same region can squad together)."""
        groups = {}
        for bot in self.bots:
            if bot.connected:
                region = getattr(bot, 'region', 'UNKNOWN')
                if region not in groups:
                    groups[region] = []
                groups[region].append(bot)
        return groups

    async def form_multi_squads(self):
        """Form multiple squads from available bots, grouped by region."""
        region_groups = self._group_bots_by_region()
        for region, bots in region_groups.items():
            logger.info(f"Region {region}: {len(bots)} bots")

        total_bots = sum(len(b) for b in region_groups.values())
        if total_bots < 2:
            return []

        squads = []
        for region, region_bots in region_groups.items():
            if len(region_bots) < 2:
                logger.info(f"Skipping region {region}: only {len(region_bots)} bot")
                continue

            for i in range(0, len(region_bots), 4):
                group = region_bots[i:i+4]
                if len(group) < 2:
                    break

                leader = group[0]
                members = group[1:]

                logger.info(f"Squad {len(squads)+1}: Leader={leader.name}, Members={[b.name for b in members]}")

                leader.squad_code = None
                await leader.create_squad()
                await asyncio.sleep(2)

                # Wait for online_listener to extract squad code
                retries = 0
                while not leader.squad_code and retries < 15:
                    await asyncio.sleep(1)
                    retries += 1

                if not leader.squad_code:
                    logger.warning(f"Squad {len(squads)+1} failed: no code")
                    continue

                code = leader.squad_code
                joined = []
                for m in members:
                    await m.join_squad(code)
                    joined.append(m.name)
                    await asyncio.sleep(1.5)

                squads.append({
                    "leader": leader,
                    "members": members,
                    "code": code,
                    "bot_names": [leader.name] + joined
                })
                await asyncio.sleep(2)

        logger.info(f"Formed {len(squads)} squads")
        return squads

    # ─── Match Cycles ────────────────────────────────────────────────

    async def start_match_cycle(self, cycles=1, wait_time=120):
        """Level-up cycle: form squad → start match → wait → repeat."""
        online_bots = [b for b in self.bots if b.connected]
        if len(online_bots) < 2:
            return "Need at least 2 connected bots"

        results = []
        for cycle in range(cycles):
            logger.info(f"=== Match Cycle {cycle+1}/{cycles} ===")

            ok, squad_info = await self.form_squad()
            if not ok:
                logger.error(f"Squad formation failed: {squad_info}")
                continue

            await asyncio.sleep(2)

            leader = online_bots[0]
            fs_pkt = await FS(leader.key, leader.iv)
            for _ in range(30):
                await leader.send_packet(fs_pkt)
                await asyncio.sleep(0.2)
            logger.info(f"FS spam done by {leader.name}")

            logger.info(f"Waiting {wait_time}s for match...")
            await asyncio.sleep(wait_time)

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

    # ─── Glory Farming System ────────────────────────────────────────

    async def start_glory_farming(self, guild_id, cycles=0, fs_duration=10,
                                   match_wait=120, cooldown=10, callback=None):
        """
        Start continuous glory farming loop.

        How it works (same as ffglory.in / guildglory.com):
        1. All bots join the target guild
        2. Bots form squads (4 per squad, multiple squads if 8+ bots)
        3. Each squad leader spams FS → server marks bots as INGAME
        4. Guild earns glory/dog tags while bots are "in match"
        5. Wait for match timer, leave squad, repeat

        Args:
            guild_id: Target guild ID
            cycles: Number of cycles (0 = infinite/24x7)
            fs_duration: Seconds to spam FS per cycle
            match_wait: Seconds to wait per match
            cooldown: Seconds between cycles
            callback: async function(msg) for progress updates
        """
        if self.glory_running:
            return {"error": "Glory farming already running"}

        self.glory_running = True
        self.glory_stats = {
            "cycles": 0,
            "started_at": datetime.now().isoformat(),
            "guild_id": guild_id,
            "squads_active": 0,
            "total_fs_sent": 0,
            "estimated_glory": 0,
        }

        async def _notify(msg):
            logger.info(msg)
            if callback:
                try:
                    await callback(msg)
                except Exception:
                    pass

        try:
            # Step 1: Join guild with all accounts
            await _notify(f"Step 1: Joining guild {guild_id}...")
            join_results = await self.guild_join_all_api(guild_id, delay=2)
            joined = sum(1 for r in join_results if r["success"])
            await _notify(f"Guild join: {joined}/{len(join_results)} accounts joined")

            if joined == 0:
                self.glory_running = False
                return {"error": "No accounts could join guild"}

            # Step 2: Login bots if not already
            online = [b for b in self.bots if b.connected]
            if len(online) < 2:
                await _notify("Logging in bots...")
                await self.login_all(delay_between=8)
                online = [b for b in self.bots if b.connected]

            if len(online) < 2:
                self.glory_running = False
                return {"error": f"Only {len(online)} bots online, need at least 2"}

            await _notify(f"Bots online: {len(online)}")

            # Step 3: Glory farming loop
            cycle_num = 0
            max_cycles = cycles if cycles > 0 else 999999

            while self.glory_running and cycle_num < max_cycles:
                cycle_num += 1
                self.glory_stats["cycles"] = cycle_num
                cycle_start = time.time()

                await _notify(f"=== Glory Cycle {cycle_num} ===")

                # Reconnect any disconnected bots
                online = [b for b in self.bots if b.connected]
                if len(online) < 2:
                    await _notify("Too few bots online, attempting reconnect...")
                    for bot in self.bots:
                        if not bot.connected:
                            try:
                                await bot.login()
                            except Exception:
                                pass
                            await asyncio.sleep(3)
                    online = [b for b in self.bots if b.connected]
                    if len(online) < 2:
                        await _notify("Cannot continue: less than 2 bots online")
                        break

                # Form squads (4 per squad)
                squads = await self.form_multi_squads()
                if not squads:
                    ok, info = await self.form_squad()
                    if ok:
                        leader_bot = [b for b in self.bots if b.connected][0]
                        squads = [{"leader": leader_bot, "members": [b for b in self.bots if b.connected and b != leader_bot][:3]}]
                    else:
                        await _notify(f"Squad formation failed, retrying in {cooldown}s...")
                        await asyncio.sleep(cooldown)
                        continue

                self.glory_stats["squads_active"] = len(squads)
                await _notify(f"Formed {len(squads)} squad(s)")

                # FS spam from all squad leaders
                fs_count = 0
                for sq in squads:
                    leader = sq["leader"]
                    fs_pkt = await FS(leader.key, leader.iv)

                    spam_end = time.time() + fs_duration
                    while time.time() < spam_end and self.glory_running:
                        await leader.send_packet(fs_pkt)
                        fs_count += 1
                        await asyncio.sleep(0.2)

                self.glory_stats["total_fs_sent"] += fs_count
                await _notify(f"FS spam done: {fs_count} packets from {len(squads)} leaders")

                # Drain server responses
                for b in self.bots:
                    if b.connected and b.online_reader:
                        try:
                            await asyncio.wait_for(b.online_reader.read(65536), timeout=1)
                        except (asyncio.TimeoutError, Exception):
                            pass

                # Wait for "match" (glory accumulates during this time)
                await _notify(f"Match in progress... waiting {match_wait}s")
                wait_start = time.time()
                while time.time() - wait_start < match_wait and self.glory_running:
                    await asyncio.sleep(5)

                # Leave all squads
                for b in self.bots:
                    if b.connected and b.in_squad:
                        try:
                            await b.leave_squad()
                        except Exception:
                            pass
                        await asyncio.sleep(0.3)

                # Estimate glory (roughly 15K-25K per squad per hour)
                cycle_time = time.time() - cycle_start
                glory_per_cycle = len(squads) * 500  # ~500 glory per squad per cycle
                self.glory_stats["estimated_glory"] += glory_per_cycle

                await _notify(
                    f"Cycle {cycle_num} done in {cycle_time:.0f}s | "
                    f"Squads: {len(squads)} | "
                    f"Est. glory: ~{self.glory_stats['estimated_glory']:,}"
                )

                # Cooldown
                if self.glory_running and cycle_num < max_cycles:
                    cd = random.uniform(cooldown * 0.8, cooldown * 1.2)
                    await asyncio.sleep(cd)

        except Exception as e:
            logger.error(f"Glory farming error: {e}")
            await _notify(f"Error: {e}")
        finally:
            self.glory_running = False

        return self.glory_stats

    def stop_glory_farming(self):
        """Stop the glory farming loop."""
        self.glory_running = False
        logger.info("Glory farming stop requested")
        return self.glory_stats

    def get_glory_stats(self):
        """Get current glory farming stats."""
        return {
            **self.glory_stats,
            "running": self.glory_running,
            "bots_online": sum(1 for b in self.bots if b.connected),
            "bots_total": len(self.bots),
        }

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
            except Exception:
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
        self.glory_running = False
        for bot in self.bots:
            await bot.disconnect()
        self.bots.clear()
        logger.info("All bots disconnected")

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
    print("  FF Multi-Account Manager + Glory Farming")
    print("=" * 50)
    print("\nCommands:")
    print("  login [region]     - Login all accounts")
    print("  status             - Show all bot statuses")
    print("  guildjoin <id>     - All bots join guild (API)")
    print("  guildleave <id>    - All bots leave guild")
    print("  squad              - Form squad(s)")
    print("  match [cycles]     - Start match cycles")
    print("  glory <guild_id> [cycles] - Start glory farming")
    print("  glorystop          - Stop glory farming")
    print("  glorystats         - Show glory stats")
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
                    icon = "+" if r["status"] == "online" else "-"
                    print(f"  {icon} {r['name']} (UID: {r['uid']}) — {r['status']}")

            elif action == "status":
                statuses = manager.get_all_status()
                if not statuses:
                    print("  No bots loaded")
                for s in statuses:
                    icon = "ON" if s["connected"] else "OFF"
                    print(f"  [{icon}] {s['name']} | UID: {s['uid']} | {s['status']}")

            elif action == "guildjoin" and len(cmd) > 1:
                results = await manager.guild_join_all_api(cmd[1])
                for r in results:
                    icon = "+" if r["success"] else "-"
                    print(f"  {icon} {r['name']}: {r['msg']}")

            elif action == "guildleave" and len(cmd) > 1:
                results = await manager.guild_leave_all(cmd[1])
                for r in results:
                    icon = "+" if r["success"] else "-"
                    print(f"  {icon} {r['name']}: {r['message']}")

            elif action == "squad":
                squads = await manager.form_multi_squads()
                if isinstance(squads, list):
                    for i, sq in enumerate(squads):
                        print(f"  Squad {i+1}: Leader={sq['leader'].name}, Code={sq['code']}")
                        print(f"    Members: {', '.join(sq['bot_names'])}")
                else:
                    ok, info = squads
                    if ok:
                        print(f"  Squad: Code={info['code']}, Leader={info['leader']}")
                    else:
                        print(f"  Failed: {info}")

            elif action == "match":
                cycles = int(cmd[1]) if len(cmd) > 1 else 1
                results = await manager.start_match_cycle(cycles=cycles)
                if isinstance(results, str):
                    print(f"  {results}")
                else:
                    for r in results:
                        print(f"  Cycle {r['cycle']}: {r['status']}")

            elif action == "glory" and len(cmd) > 1:
                guild_id = cmd[1]
                cycles = int(cmd[2]) if len(cmd) > 2 else 0
                print(f"  Starting glory farming for guild {guild_id}...")
                result = await manager.start_glory_farming(guild_id, cycles=cycles)
                print(f"  Result: {result}")

            elif action == "glorystop":
                stats = manager.stop_glory_farming()
                print(f"  Stopped. Stats: {stats}")

            elif action == "glorystats":
                stats = manager.get_glory_stats()
                print(f"  Running: {stats['running']}")
                print(f"  Cycles: {stats['cycles']}")
                print(f"  Squads: {stats['squads_active']}")
                print(f"  Est. Glory: ~{stats['estimated_glory']:,}")
                print(f"  Bots: {stats['bots_online']}/{stats['bots_total']}")

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
