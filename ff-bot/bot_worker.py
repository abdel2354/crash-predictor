"""
FF Bot Worker - Single account bot instance.
Runs inside a Docker container. Receives commands via Redis pub/sub.
Connects one FF account to the game server via TCP.
"""

import os
import sys
import json
import time
import asyncio
import logging
import aiohttp
import random

from xC4 import (
    CrEaTe_ProTo, GeneRaTePk, EnC_PacKeT, DEc_PacKeT,
    OpEnSq, GenJoinSquadsPacket, ExiT, FS, Emote_k,
    SEnd_InV, EnC_AEs, DEc_AEs, EnC_Uid, Ua, DeCode_PackEt,
    AutH_Chat, GeTSQDaTa, DecodE_HeX
)

from Pb2 import MajoRLoGinrEq_pb2, MajoRLoGinrEs_pb2
from Pb2 import PorTs_pb2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(os.environ.get('BOT_NAME', 'worker'))

# AES keys
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])


async def xAuThSTarTuP(TarGeT, token, timestamp, key, iv):
    """Build TCP authentication packet."""
    uid_hex = hex(TarGeT)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await DecodE_HeX(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await EnC_PacKeT(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]
    if uid_length == 9: headers = '0000000'
    elif uid_length == 8: headers = '00000000'
    elif uid_length == 10: headers = '000000'
    elif uid_length == 7: headers = '000000000'
    else: headers = '0000000'
    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"


class BotWorker:
    """Single FF account bot that connects to the game server."""

    def __init__(self, uid, password, region="ME", name="M3SBIOS"):
        self.uid = uid
        self.password = password
        self.region = region
        self.name = name
        self.status = "idle"

        # Auth data (populated after login)
        self.open_id = None
        self.access_token = None
        self.jwt_token = None
        self.account_uid = None
        self.key = None
        self.iv = None
        self.timestamp = None
        self.server_url = None

        # TCP connections
        self.online_writer = None
        self.online_reader = None
        self.whisper_writer = None
        self.whisper_reader = None

        # Server IPs
        self.online_ip = None
        self.online_port = None
        self.chat_ip = None
        self.chat_port = None

        # State
        self.in_squad = False
        self.squad_code = None
        self.in_match = False
        self.connected = False
        self.clan_id = None

        # Command queue
        self.command_queue = asyncio.Queue()

    # ─── Authentication ─────────────────────────────────────────────

    async def get_access_token(self):
        """Step 1: Get access_token + open_id from Garena OAuth."""
        url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        headers = {
            "Host": "100067.connect.garena.com",
            "User-Agent": await Ua(),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close"
        }
        data = {
            "uid": self.uid,
            "password": self.password,
            "response_type": "token",
            "client_type": "2",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_id": "100067"
        }

        token_urls = [
            "https://100067.connect.garena.com/oauth/guest/token/grant",
            "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant",
        ]

        for attempt, url in enumerate(token_urls * 2):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, data=data, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            self.open_id = result.get("open_id")
                            self.access_token = result.get("access_token")
                            if self.open_id and self.access_token:
                                logger.info(f"Token OK: open_id={self.open_id[:10]}...")
                                return True
                        elif resp.status == 429:
                            wait = random.uniform(5, 15)
                            logger.warning(f"Token 429, waiting {wait:.0f}s...")
                            await asyncio.sleep(wait)
                        else:
                            logger.warning(f"Token failed: HTTP {resp.status}")
            except Exception as e:
                logger.error(f"Token error: {e}")
                await asyncio.sleep(2)

        return False

    async def _build_major_login_payload(self):
        """Build the encrypted MajorLogin protobuf payload."""
        from Crypto.Cipher import AES as AES_Crypto
        from Crypto.Util.Padding import pad

        ml = MajoRLoGinrEq_pb2.MajorLogin()
        ml.event_time = time.strftime('%Y-%m-%d %H:%M:%S')
        ml.game_name = "free fire"
        ml.platform_id = 1
        ml.client_version = "1.123.1"
        ml.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
        ml.system_hardware = "Handheld"
        ml.telecom_operator = "Verizon"
        ml.network_type = "WIFI"
        ml.screen_width = 1920
        ml.screen_height = 1080
        ml.screen_dpi = "280"
        ml.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
        ml.memory = 3003
        ml.gpu_renderer = "Adreno (TM) 640"
        ml.gpu_version = "OpenGL ES 3.1 v1.46"
        ml.unique_device_id = f"Google|{random.randint(10000000,99999999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(100000000000,999999999999)}"
        ml.client_ip = f"{random.randint(100,223)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        ml.language = "en"
        ml.open_id = self.open_id
        ml.open_id_type = "4"
        ml.device_type = "Handheld"
        ml.access_token = self.access_token
        ml.platform_sdk_id = 1
        ml.network_operator_a = "Verizon"
        ml.network_type_a = "WIFI"
        ml.client_using_version = "7428b253defc164018c604a1ebbfebdf"
        ml.external_storage_total = 36235
        ml.external_storage_available = 31335
        ml.internal_storage_total = 2519
        ml.internal_storage_available = 703
        ml.game_disk_storage_available = 25010
        ml.game_disk_storage_total = 26628
        ml.external_sdcard_avail_storage = 32992
        ml.external_sdcard_total_storage = 36235
        ml.login_by = 3
        ml.library_path = "/data/app/com.dts.freefireth-1/lib/arm"
        ml.reg_avatar = 1
        ml.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-1/base.apk"
        ml.channel_type = 3
        ml.cpu_type = 2
        ml.cpu_architecture = "64"
        ml.client_version_code = "2019118695"
        ml.graphics_api = "OpenGLES2"
        ml.supported_astc_bitset = 16383
        ml.login_open_id_type = 4
        ml.loading_time = random.randint(10000, 15000)
        ml.release_channel = "android"
        ml.android_engine_init_flag = 110009
        ml.if_push = 1
        ml.is_vpn = 1
        ml.origin_platform_type = "4"
        ml.primary_platform_type = "4"

        raw_bytes = ml.SerializeToString()
        cipher = AES_Crypto.new(AES_KEY, AES_Crypto.MODE_CBC, AES_IV)
        encrypted = cipher.encrypt(pad(raw_bytes, AES_Crypto.block_size))
        return encrypted

    async def major_login(self):
        """Step 2: MajorLogin to get JWT, key, iv, server URL."""
        if not self.open_id or not self.access_token:
            return False

        self._login_payload = await self._build_major_login_payload()

        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/x-www-form-urlencoded",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB53",
        }

        login_urls = [
            "https://loginbp.ggblueshark.com/MajorLogin",
            "https://loginbp.common.ggbluefox.com/MajorLogin",
            "https://loginbp.ggpolarbear.com/MajorLogin",
        ]

        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        for url in login_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, data=self._login_payload,
                                            ssl=ssl_ctx, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 200:
                            response_data = await resp.read()
                            if response_data and len(response_data) > 0:
                                return self._parse_major_login(response_data)
                        else:
                            logger.warning(f"MajorLogin {url}: HTTP {resp.status}")
            except Exception as e:
                logger.warning(f"MajorLogin {url} error: {e}")

        logger.error("All MajorLogin URLs failed")
        return False

    def _parse_major_login(self, response_data):
        """Parse MajorLogin response (protobuf, no decryption needed)."""
        try:
            login_res = MajoRLoGinrEs_pb2.MajorLoginRes()
            login_res.ParseFromString(response_data)

            self.jwt_token = login_res.token
            self.server_url = login_res.url
            self.account_uid = login_res.account_uid

            if login_res.key:
                self.key = login_res.key
            if login_res.iv:
                self.iv = login_res.iv
            self.timestamp = login_res.timestamp
            self.region = login_res.region or self.region

            if self.jwt_token:
                logger.info(f"MajorLogin OK: UID={self.account_uid}, JWT={self.jwt_token[:20]}...")
                return True
            logger.error("No JWT token in MajorLogin response")
            return False
        except Exception as e:
            logger.error(f"Parse MajorLogin error: {e}")
            return False

    async def get_login_data(self):
        """Step 3: GetLoginData to get server IPs and ports."""
        if not self.jwt_token or not self.server_url:
            return False

        url = f"{self.server_url}/GetLoginData"

        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/x-www-form-urlencoded",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB53",
            'Authorization': f"Bearer {self.jwt_token}",
        }

        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=self._login_payload,
                                        ssl=ssl_ctx, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return self._parse_login_data(data)
                    else:
                        logger.error(f"GetLoginData failed: HTTP {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"GetLoginData error: {e}")
            return False

    def _parse_login_data(self, data):
        """Parse GetLoginData response (protobuf, no decryption)."""
        try:
            login_data = PorTs_pb2.GetLoginData()
            login_data.ParseFromString(data)

            online_ports = login_data.Online_IP_Port
            chat_ports = login_data.AccountIP_Port

            if online_ports:
                parts = str(online_ports).split(":")
                self.online_ip = parts[0]
                self.online_port = int(parts[1])

            if chat_ports:
                parts = str(chat_ports).split(":")
                self.chat_ip = parts[0]
                self.chat_port = int(parts[1])

            self.clan_id = login_data.Clan_ID if login_data.Clan_ID else None

            logger.info(f"Servers: Online={self.online_ip}:{self.online_port}, Chat={self.chat_ip}:{self.chat_port}")
            return True
        except Exception as e:
            logger.error(f"Parse LoginData error: {e}")
            return False

    # ─── TCP Connection ─────────────────────────────────────────────

    async def connect_tcp(self):
        """Step 4: Connect to both TCP servers (Online + Chat)."""
        if not self.online_ip or not self.chat_ip:
            return False

        auth_token = await xAuThSTarTuP(
            int(self.account_uid), self.jwt_token, int(self.timestamp),
            self.key, self.iv
        )

        try:
            # Online connection
            self.online_reader, self.online_writer = await asyncio.open_connection(
                self.online_ip, self.online_port
            )
            self.online_writer.write(bytes.fromhex(auth_token) if isinstance(auth_token, str) else auth_token)
            await self.online_writer.drain()
            logger.info("Online TCP connected")

            # Chat connection
            self.whisper_reader, self.whisper_writer = await asyncio.open_connection(
                self.chat_ip, self.chat_port
            )
            self.whisper_writer.write(bytes.fromhex(auth_token) if isinstance(auth_token, str) else auth_token)
            await self.whisper_writer.drain()
            logger.info("Chat TCP connected")

            self.connected = True
            self.status = "online"
            return True

        except Exception as e:
            logger.error(f"TCP connect error: {e}")
            return False

    # ─── Full Login Flow ────────────────────────────────────────────

    async def login(self):
        """Complete login flow: Token → MajorLogin → GetLoginData → TCP."""
        logger.info(f"Logging in {self.name} (UID: {self.uid}, Region: {self.region})...")

        if not await self.get_access_token():
            self.status = "token_failed"
            return False

        await asyncio.sleep(random.uniform(1, 3))

        if not await self.major_login():
            self.status = "login_failed"
            return False

        await asyncio.sleep(random.uniform(1, 2))

        if not await self.get_login_data():
            self.status = "data_failed"
            return False

        await asyncio.sleep(random.uniform(0.5, 1))

        if not await self.connect_tcp():
            self.status = "tcp_failed"
            return False

        self.status = "online"
        logger.info(f"{self.name} is ONLINE!")
        return True

    # ─── Game Actions ───────────────────────────────────────────────

    async def send_packet(self, packet):
        """Send packet via Online TCP connection."""
        if self.online_writer and not self.online_writer.is_closing():
            try:
                if isinstance(packet, str):
                    packet = bytes.fromhex(packet)
                self.online_writer.write(packet)
                await self.online_writer.drain()
                return True
            except Exception as e:
                logger.error(f"Send packet error: {e}")
                self.connected = False
                return False
        return False

    async def create_squad(self):
        """Create a new squad (become leader)."""
        packet = await OpEnSq(self.key, self.iv, self.region)
        if await self.send_packet(packet):
            self.in_squad = True
            self.status = "squad_leader"
            logger.info(f"{self.name} created squad")
            return True
        return False

    async def join_squad(self, squad_code):
        """Join an existing squad by code."""
        packet = await GenJoinSquadsPacket(squad_code, self.key, self.iv)
        if await self.send_packet(packet):
            self.in_squad = True
            self.squad_code = squad_code
            self.status = "in_squad"
            logger.info(f"{self.name} joined squad {squad_code}")
            return True
        return False

    async def leave_squad(self):
        """Leave current squad."""
        packet = await ExiT(None, self.key, self.iv)
        if await self.send_packet(packet):
            self.in_squad = False
            self.squad_code = None
            self.status = "online"
            logger.info(f"{self.name} left squad")
            return True
        return False

    async def start_match(self):
        """Start a match (must be squad leader)."""
        packet = await FS(self.key, self.iv)
        if await self.send_packet(packet):
            self.in_match = True
            self.status = "in_match"
            logger.info(f"{self.name} started match")
            return True
        return False

    async def send_emote(self, target_uid, emote_id):
        """Send emote to a player."""
        packet = await Emote_k(int(target_uid), int(emote_id), self.key, self.iv, self.region)
        return await self.send_packet(packet)

    async def send_invite(self, target_uid):
        """Send squad invite to a player."""
        packet = await SEnd_InV(target_uid, self.account_uid, self.key, self.iv, self.region)
        return await self.send_packet(packet)

    # ─── Guild Operations (API-based, no TCP needed) ────────────────

    async def guild_join(self, guild_id):
        """Join a guild via API."""
        url = f"https://danger-guild-management-web.vercel.app/join?guild_id={guild_id}&uid={self.uid}&password={self.password}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        result = await resp.text()
                        logger.info(f"{self.name} joined guild {guild_id}: {result[:50]}")
                        return True, result
                    return False, f"HTTP {resp.status}"
        except Exception as e:
            return False, str(e)

    async def guild_leave(self, guild_id):
        """Leave a guild via API."""
        url = f"https://danger-guild-management-web.vercel.app/leave?guild_id={guild_id}&uid={self.uid}&password={self.password}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        result = await resp.text()
                        logger.info(f"{self.name} left guild {guild_id}")
                        return True, result
                    return False, f"HTTP {resp.status}"
        except Exception as e:
            return False, str(e)

    # ─── Status ─────────────────────────────────────────────────────

    def get_status(self):
        return {
            "name": self.name,
            "uid": self.uid,
            "account_uid": self.account_uid,
            "region": self.region,
            "status": self.status,
            "connected": self.connected,
            "in_squad": self.in_squad,
            "in_match": self.in_match,
        }

    # ─── Disconnect ─────────────────────────────────────────────────

    async def disconnect(self):
        """Disconnect from game servers."""
        if self.in_squad:
            await self.leave_squad()

        for writer in [self.online_writer, self.whisper_writer]:
            if writer and not writer.is_closing():
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass

        self.connected = False
        self.status = "offline"
        logger.info(f"{self.name} disconnected")

    # ─── Keep-Alive Loop ────────────────────────────────────────────

    async def keep_alive_loop(self):
        """Send periodic keep-alive packets to maintain connection."""
        while self.connected:
            try:
                await asyncio.sleep(30)
                if self.online_writer and not self.online_writer.is_closing():
                    # Simple ping packet
                    fields = {1: 99, 2: {1: int(time.time())}}
                    packet = await GeneRaTePk(
                        (await CrEaTe_ProTo(fields)).hex(),
                        '0515' if self.region not in ('IND', 'BD') else ('0514' if self.region == 'IND' else '0519'),
                        self.key, self.iv
                    )
                    await self.send_packet(packet)
            except Exception as e:
                logger.warning(f"Keep-alive error: {e}")
                break

    # ─── Online Listener ────────────────────────────────────────────

    async def online_listener(self):
        """Listen for packets on the Online TCP connection."""
        while self.connected and self.online_reader:
            try:
                data = await self.online_reader.read(9999)
                if not data:
                    logger.warning("Online connection closed by server")
                    self.connected = False
                    break

                data_hex = data.hex()

                # Detect squad data
                if data_hex.startswith("0500"):
                    try:
                        decrypted = await DEc_PacKeT(data_hex[10:], self.key, self.iv)
                        packet = await DeCode_PackEt(decrypted)
                        packet_json = json.loads(packet)

                        # Extract squad code if available
                        if '5' in packet_json and 'data' in packet_json['5']:
                            sq_data = packet_json['5']['data']
                            if '31' in sq_data:
                                self.squad_code = sq_data['31'].get('data')
                                logger.info(f"Squad code detected: {self.squad_code}")
                    except:
                        pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Online listener error: {e}")
                await asyncio.sleep(1)

    # ─── Main Run Loop ──────────────────────────────────────────────

    async def run(self):
        """Main bot loop: login, listen, process commands."""
        if not await self.login():
            logger.error(f"Login failed for {self.name}")
            return

        # Start background tasks
        tasks = [
            asyncio.create_task(self.keep_alive_loop()),
            asyncio.create_task(self.online_listener()),
            asyncio.create_task(self.command_processor()),
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            await self.disconnect()

    async def command_processor(self):
        """Process commands from the command queue."""
        while self.connected:
            try:
                cmd = await asyncio.wait_for(self.command_queue.get(), timeout=5)
                action = cmd.get("action")

                if action == "create_squad":
                    await self.create_squad()
                elif action == "join_squad":
                    await self.join_squad(cmd["code"])
                elif action == "leave_squad":
                    await self.leave_squad()
                elif action == "start_match":
                    await self.start_match()
                elif action == "guild_join":
                    await self.guild_join(cmd["guild_id"])
                elif action == "guild_leave":
                    await self.guild_leave(cmd["guild_id"])
                elif action == "emote":
                    await self.send_emote(cmd["target"], cmd["emote_id"])
                elif action == "disconnect":
                    await self.disconnect()
                    break

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Command error: {e}")


# ─── Standalone Mode ────────────────────────────────────────────────

async def main():
    """Run as standalone worker (reads config from env or file)."""
    uid = os.environ.get("BOT_UID")
    password = os.environ.get("BOT_PASSWORD")
    region = os.environ.get("BOT_REGION", "ME")
    name = os.environ.get("BOT_NAME", "M3SBIOS")

    if not uid or not password:
        # Try loading from accounts file
        accounts_file = os.environ.get("ACCOUNTS_FILE", "BIGBULL-ERA/ACCOUNTS/accounts-ME.json")
        bot_index = int(os.environ.get("BOT_INDEX", "0"))

        if os.path.exists(accounts_file):
            with open(accounts_file, 'r') as f:
                accounts = json.load(f)
            if bot_index < len(accounts):
                acc = accounts[bot_index]
                uid = acc["uid"]
                password = acc["password"]
                name = acc.get("name", f"M3SBIOS-{bot_index}")
                region = acc.get("region", "ME")
            else:
                logger.error(f"Bot index {bot_index} out of range (have {len(accounts)} accounts)")
                return
        else:
            logger.error("No credentials provided and no accounts file found")
            return

    worker = BotWorker(uid=uid, password=password, region=region, name=name)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
