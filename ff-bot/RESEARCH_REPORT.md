# FF-Bot Research Report — Guild Glory Farming System

## How Glory Bot Services Work (ffglory.in, guildglory.com)

After researching commercial glory bot services, here's how they operate:

### The Glory Farming Method
1. **Bot accounts join target guild** via Guild Join API
2. **Bots form squads** (4 per squad, all guild members)
3. **Squad leaders spam FS** (match start) → server marks bots as INGAME (status 5)
4. **Guild earns glory + dog tags** while members are "in match"
5. **Bots leave squad, repeat** the cycle continuously (24/7)

**Key insight:** Bots do NOT need to actually play or appear in-game. 
Just being in "INGAME" status earns glory for the guild.

### Commercial Pricing (reference)
| Plan | Squads | Glory | Price | Time |
|------|--------|-------|-------|------|
| Basic | 1 (4 bots) | 120K-200K | ₹399 | 8 hrs |
| Standard | 2 (8 bots) | 200K-400K | ₹779 | 8 hrs |
| Premium | 3 (12 bots) | 300K-600K | ₹1,149 | 8 hrs |
| Pro | 4 (16 bots) | 400K-800K | ₹1,499 | 8 hrs |

---

## System Architecture

### Connection Flow
```
Guest Register → Token Grant → MajorLogin → GetLoginData → TCP Connect
```

### Protocol Stack
- **TCP Lobby** (port 39699) — Squad management, social features, matchmaking trigger
- **TCP Chat** (port 39801) — Messages, commands
- **UDP Game** (unknown port) — Actual gameplay (movement, shooting) — NOT required for glory

### Packet Types
| Function | Type | Description |
|----------|------|-------------|
| `OpEnSq(K,V,region)` | 1 | Create squad |
| `GenJoinSquadsPacket(code,K,V)` | 4 | Join squad by code |
| `ExiT(idT,K,V)` | 7 | Leave squad |
| `FS(K,V)` | 9 | Start match (triggers INGAME status) |
| `Emote_k(...)` | - | Send emote |
| `SEnd_InV(...)` | 2 | Send squad invite |

### Server Response Analysis
After FS spam, server returns:
- 30× 15-byte status packets: `{1: UID, 2: 5, 3: 58}`
- Field 2=5 means INGAME status
- **No game server IP/port** is sent via TCP
- This confirms: glory farming works at lobby level only

---

## What We Built

### Core Components
| File | Purpose |
|------|---------|
| `bot_worker.py` | Single bot instance (login, TCP, squad, guild) |
| `multi_account_manager.py` | Orchestrates 10+ bots, glory farming loop |
| `telegram_controller.py` | Telegram UI for controlling everything |
| `bbcXgen.py` | Guest account generator (FAST mode) |
| `xC4.py` | Packet encryption/creation |

### Glory Farming System
```python
# multi_account_manager.py → start_glory_farming()
# 
# Loop:
#   1. guild_join_all_api(guild_id)  ← All bots join guild
#   2. form_multi_squads()           ← Form squads (4 per squad)
#   3. FS spam (10s per leader)      ← Trigger INGAME status
#   4. Wait match_wait seconds       ← Glory accumulates
#   5. Leave all squads              ← Reset
#   6. Cooldown → Repeat
```

### Telegram Commands
| Button | Action |
|--------|--------|
| 🔑 Login All | Login all bot accounts to FF servers |
| ⚔️ Glory Farm | Start glory farming (enter guild ID) |
| 🛑 Stop Glory | Stop glory farming loop |
| 📊 Glory Stats | Show farming statistics |
| 🏰 Guild Join | All bots join a guild |
| 🚪 Guild Leave | All bots leave a guild |
| 👥 Squad | Form squad(s) manually |
| 🎮 Match | Start single match |
| 🔄 Match Cycles | Run N match cycles |

---

## Accounts
- 10 M3SBIOS guest accounts (region: ME)
- Stored in `BIGBULL-ERA/ACCOUNTS/accounts-ME.json`
- JWT tokens in `BIGBULL-ERA/TOKENS-JWT/tokens-ME.json`

## Test Results
- 4/4 bots login to ME servers successfully
- Squad creation + join works (squad code detected from 0500 packets)
- FS spam produces INGAME status (field 2=5)
- CS mode (Clash Squad) request is ignored by server — always defaults to BR
- Action types 8,10,11,12,14 cause disconnection — only type 9 (FS) is safe

## Limitations
1. **No in-game appearance** — Bots trigger matchmaking but don't connect to game server
2. **No gameplay simulation** — Movement/shooting requires UDP game protocol (not in codebase)
3. **Region routing** — Some accounts may route to NA instead of ME despite forced region
4. **Rate limiting** — Garena enforces 429/403 on account creation
