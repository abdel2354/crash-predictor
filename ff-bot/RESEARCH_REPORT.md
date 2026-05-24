# FF-Bot Full System Research Report

## What We Have (Inside the Code)

### 1. Connection & Authentication Flow (COMPLETE)
```
Guest Register → Token Grant → MajorLogin → GetLoginData → TCP Connect
```
- `GeNeRaTeAccEss()` — Get access_token + open_id from Garena OAuth
- `EncRypTMajoRLoGin()` — Build protobuf login payload 
- `MajorLogin()` — Authenticate and get JWT + server URL
- `GetLoginData()` — Get server IPs, ports, key, iv, clan data
- `xAuThSTarTuP()` — Build TCP auth packet
- `TcPOnLine()` — Connect to Online server (game state, emotes, squads)
- `TcPChaT()` — Connect to Chat server (messages, commands)

### 2. Packet System (xC4.py - COMPLETE)
```python
CrEaTe_ProTo(fields)    # Build protobuf from dict
GeneRaTePk(Pk, N, K, V) # Encrypt + add header
EnC_PacKeT(HeX, K, V)   # AES-CBC encrypt
DEc_PacKeT(HeX, K, V)   # AES-CBC decrypt
```

### 3. Squad/Team Packets (COMPLETE)
| Function | Packet Type | Description |
|----------|------------|-------------|
| `OpEnSq(K,V,region)` | type=1 | Create new squad |
| `GenJoinSquadsPacket(code,K,V)` | type=4 | Join squad by code |
| `ExiT(idT,K,V)` | type=7 | Leave squad |
| `FS(K,V)` | type=9 | Start match (fire start) |
| `SEnd_InV(Nu,Uid,K,V,region)` | type=2 | Send squad invite |
| `cHSq(Nu,Uid,K,V,region)` | type=17 | Change squad settings |
| `LagSquad(K,V)` | type=4 | Lag squad packet |

### 4. Game Action Packets (AVAILABLE)
| Function | Description |
|----------|-------------|
| `Emote_k(target,emoteId,K,V,region)` | Send emote to player |
| `Send_Entry_Emote(uid,K,V)` | Entry/arrival animation |
| `start_match(key,iv,region)` | Start BR match |
| `create_training_start_packet()` | Enter training mode |
| `join_custom_room(room_id,pw,K,V,region)` | Join custom room |
| `create_custom_room(name,pw,max,K,V,region)` | Create custom room |

### 5. APIs (COMPLETE)
| API | URL | Purpose |
|-----|-----|---------|
| Guild Info | `danger-guild-management-web.vercel.app/guild` | Get guild details |
| Guild Join | `danger-guild-management-web.vercel.app/join` | Join guild with UID+PW |
| Guild Leave | `danger-guild-management-web.vercel.app/leave` | Leave guild |
| Add Friend | `mafuuuuu-add.vercel.app/mafu-add_friend` | Add friend |
| Remove Friend | `mafuuuuu-add.vercel.app/mafu-remove_friend` | Remove friend |
| Send Likes | Multiple endpoints (get_player_add_1..102) | Mass like a UID |
| Player Info | `client.ind.freefiremobile.com/GetPlayerPersonalShow` | Get player data |
| Level Info | `danger-level-info.vercel.app/level/{uid}` | Get level/XP info |
| Ban Check | `banchack.vercel.app/bancheck` | Check if UID banned |

### 6. Level-Up System (EXISTS but basic)
```python
level_up_loop(team_code, target_uid, key, iv, region, chat_type, chat_id)
```
Flow: Join team → Start match → Wait → Leave → Repeat
**LIMITATION:** Only uses ONE bot connection, doesn't manage multiple bots

### 7. Multi-Region Support
Regions with full URLs: IND, BD, PK, NA, LK, ID, TH, VN, BR, ME

---

## What's MISSING (Need to Build)

### A. Multi-Account TCP Manager
**Problem:** `main.py` only connects ONE account at a time.
**Need:** System to connect 10+ accounts simultaneously, each with its own TCP connection.

**Required Components:**
```python
class BotAccount:
    uid: str
    password: str
    key: bytes         # From MajorLogin
    iv: bytes          # From MajorLogin
    token: str         # JWT
    online_writer: StreamWriter  # TCP Online connection
    whisper_writer: StreamWriter # TCP Chat connection
    region: str
    status: str        # 'idle', 'in_squad', 'in_match'

class MultiAccountManager:
    accounts: List[BotAccount]
    
    async def login_account(uid, pw, region) -> BotAccount
    async def login_all_accounts(accounts_list)
    async def get_idle_accounts() -> List[BotAccount]
    async def send_packet_to_account(account, packet)
    async def send_packet_to_all(packet_func, *args)
```

### B. Guild Mass-Join System
**Have:** `api_guild_join(guild_id, uid, pw)` API
**Need:** Telegram command that takes guild_id and joins ALL bot accounts

```
/guildjoin_all <guild_id>
→ For each M3SBIOS account:
  → Call api_guild_join(guild_id, uid, password)
  → Report success/failure
```

### C. Squad Formation System
**Have:** `OpEnSq`, `GenJoinSquadsPacket`, `SEnd_InV`
**Need:** Leader creates squad → sends code → all bots join

```
Flow:
1. Leader account calls OpEnSq() → creates squad → gets squad_code
2. All other bot accounts call GenJoinSquadsPacket(squad_code)
3. Leader calls FS() → starts match
```
**Challenge:** Each bot needs its own TCP connection with key/iv

### D. In-Match Gameplay Simulation
**MISSING from codebase.** No movement/shoot/action packets found.

**What exists:**
- `FS(K,V)` — Start match packet
- `create_training_start_packet()` — Enter training

**What's needed for realistic gameplay:**
```
MOVEMENT PACKETS (not in code - need to reverse engineer):
- Position update (x, y, z coordinates)
- Movement direction/speed
- Jump/crouch state
- Weapon switch
- Fire/shoot packet
- Pickup item
- Use medkit/gloo wall
- Vehicle enter/exit
```

**Reality check:** In-match gameplay packets are the hardest part.
The game server validates game state. Without proper game client
simulation, the server will likely detect and kick the bot.

**Alternatives for Glory/XP:**
1. **Custom Room approach:** Create private custom room, all bots join,
   one bot wins. Custom rooms may give less XP but are more controlled.
2. **AFK Match approach:** Bots join match but AFK in safe zone.
   Still gets survival XP (less than active play but simpler).
3. **Training Mode:** `create_training_start_packet()` exists but
   training mode doesn't give XP/Glory.

---

## Recommended Build Plan

### Phase 1: Multi-Account Manager + Telegram Control
- Create `multi_account_manager.py` with BotAccount class
- Load accounts from BIGBULL-ERA/ACCOUNTS/
- Login each account → get JWT, key, iv
- Connect TCP for each account
- Add Telegram commands: `/status_all`, `/login_all`, `/disconnect_all`

### Phase 2: Guild Mass Operations
- `/guildjoin_all <guild_id>` → all accounts join guild
- `/guildleave_all <guild_id>` → all accounts leave guild  
- Uses existing API (no TCP needed)

### Phase 3: Squad + Match System
- Leader bot creates squad → gets code
- All other bots join via code
- Leader starts match
- Bots AFK in match (survival XP = glory for guild)
- After match ends → repeat

### Phase 4: Gameplay Simulation (Advanced)
- Position update packets (if available from protocol analysis)
- Random movement within safe zone
- Occasional shots for kill XP
- 60% win rate through strategic positioning

---

## Key Files Reference
| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 11,230 | TCP bot, all game logic |
| `xC4.py` | 562 | Packet creation/encryption |
| `xHeaders.py` | ~300 | HTTP headers generation |
| `bbcXgen.py` | 1,060 | Guest account generator |
| `telegram_bot.py` | 1,270 | Telegram bot interface |
| `anti-septic-activator.py` | 948 | Multi-region account activation |
| `Pb2/*.py` | ~20 files | Protobuf definitions |
