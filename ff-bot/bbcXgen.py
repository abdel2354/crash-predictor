#bigbullcheat owner#bbcindia


import hmac,hashlib,requests,string,random,json,codecs,time,os,sys,base64,signal,threading,re,subprocess,importlib
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from colorama import Fore, Style, init
import urllib3
import psutil

init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_random_color():
    colors = [Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTWHITE_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTMAGENTA_EX]
    return random.choice(colors)

class Colors:
    BRIGHT = Style.BRIGHT
    RESET = Style.RESET_ALL

# ========== HIDDEN - MULTI LAYER ENCODED (UPDATED FOR BIG BULL) ==========
_H1 = "VkVSV1NGRlZVVlZFVk5WQQ=="
_H2 = "UkdWeFVGRkZWRVZGVlJRVkE9PQ=="
_H3 = "VkZSU1RVRkZWREVGRlJXUUE9PQ=="
_XOR = [0x42, 0x59, 0x5F, 0x42, 0x49, 0x47, 0x42, 0x55, 0x4C, 0x4C, 0x5F]

def _get_hidden():
    try:
        s1 = base64.b64decode(_H3).decode()
        s2 = s1[::-1]
        s3 = base64.b64decode(s2).decode()
        return ''.join(chr(ord(s3[i]) ^ _XOR[i % len(_XOR)]) for i in range(len(s3)))
    except:
        return base64.b64decode("QklHQlVMTENIRUFUUw==").decode()

_HIDDEN = _get_hidden()

EXIT_FLAG = False
SUCCESS_COUNTER = 0
TARGET_ACCOUNTS = 0
RARE_COUNTER = 0
COUPLES_COUNTER = 0
RARITY_SCORE_THRESHOLD = 8
LOCK = threading.Lock()
START_TIME = 0

# Folders - BIGBULL BRANDING
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_FOLDER = os.path.join(CURRENT_DIR, "BIGBULL-ERA")
TOKENS_FOLDER = os.path.join(BASE_FOLDER, "TOKENS-JWT")
ACCOUNTS_FOLDER = os.path.join(BASE_FOLDER, "ACCOUNTS")
RARE_ACCOUNTS_FOLDER = os.path.join(BASE_FOLDER, "RARE ACCOUNTS")
COUPLES_ACCOUNTS_FOLDER = os.path.join(BASE_FOLDER, "COUPLES ACCOUNTS")
GHOST_FOLDER = os.path.join(BASE_FOLDER, "GHOST")
GHOST_ACCOUNTS_FOLDER = os.path.join(GHOST_FOLDER, "ACCOUNTS")
GHOST_RARE_FOLDER = os.path.join(GHOST_FOLDER, "RAREACCOUNT")
GHOST_COUPLES_FOLDER = os.path.join(GHOST_FOLDER, "COUPLESACCOUNT")

for folder in [BASE_FOLDER, TOKENS_FOLDER, ACCOUNTS_FOLDER, RARE_ACCOUNTS_FOLDER, COUPLES_ACCOUNTS_FOLDER, GHOST_FOLDER, GHOST_ACCOUNTS_FOLDER, GHOST_RARE_FOLDER, GHOST_COUPLES_FOLDER]:
    os.makedirs(folder, exist_ok=True)

REGION_LANG = {"ME":"ar","IND":"hi","ID":"id","VN":"vi","TH":"th","BD":"bn","PK":"ur","TW":"zh","CIS":"ru","SAC":"es","BR":"pt"}
HEX_KEY = bytes.fromhex("32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533")

FILE_LOCKS = {}
def get_lock(fname):
    if fname not in FILE_LOCKS:
        FILE_LOCKS[fname] = threading.Lock()
    return FILE_LOCKS[fname]

# Rare patterns
PATTERNS = {
    "R4": [r"(\d)\1{3,}", 3], "R3": [r"(\d)\1\1(\d)\2\2", 2],
    "S5": [r"(12345|23456|34567|45678|56789)", 4], "S4": [r"(0123|1234|2345|3456|4567|5678|6789|9876|8765|7654|6543|5432|4321|3210)", 3],
    "P6": [r"^(\d)(\d)(\d)\3\2\1$", 5], "P4": [r"^(\d)(\d)\2\1$", 3],
    "SPH": [r"(69|420|1337|007)", 4], "SPM": [r"(100|200|300|400|500|666|777|888|999)", 2],
    "QD": [r"(1111|2222|3333|4444|5555|6666|7777|8888|9999|0000)", 4],
    "MH": [r"^(\d{2,3})\1$", 3], "MM": [r"(\d{2})0\1", 2], "GD": [r"1618|0618", 3]
}

COUPLES_DATA = {}
COUPLES_LOCK = threading.Lock()

def check_rarity(account_data):
    account_id = account_data.get("account_id", "")
    if account_id == "N/A" or not account_id:
        return False, None, None, 0
    score = 0
    patterns_found = []
    for ptype, (pattern, pts) in PATTERNS.items():
        if re.search(pattern, account_id):
            score += pts
            patterns_found.append(ptype)
    digits = [int(d) for d in account_id if d.isdigit()]
    if len(set(digits)) == 1 and len(digits) >= 4:
        score += 5
        patterns_found.append("UNIFORM")
    if len(digits) >= 4:
        diffs = [digits[i+1] - digits[i] for i in range(len(digits)-1)]
        if len(set(diffs)) == 1:
            score += 4
            patterns_found.append("ARITHMETIC")
    if len(account_id) <= 8 and account_id.isdigit() and int(account_id) < 1000000:
        score += 3
        patterns_found.append("LOW_ID")
    if score >= RARITY_SCORE_THRESHOLD:
        reason = f"ID:{account_id} | Score:{score} | {','.join(patterns_found)}"
        return True, "RARE", reason, score
    return False, None, None, score

def check_couple(account_data, thread_id):
    account_id = account_data.get("account_id", "")
    if account_id == "N/A" or not account_id:
        return False, None, None
    with COUPLES_LOCK:
        for stored_id, stored in COUPLES_DATA.items():
            stored_aid = stored.get('account_id', '')
            if stored_aid and abs(int(account_id) - int(stored_aid)) == 1:
                partner = stored
                del COUPLES_DATA[stored_id]
                return True, f"Sequential: {account_id} & {stored_aid}", partner
            if stored_aid and account_id == stored_aid[::-1]:
                partner = stored
                del COUPLES_DATA[stored_id]
                return True, f"Mirror: {account_id} & {stored_aid}", partner
        COUPLES_DATA[account_id] = {
            'uid': account_data.get('uid', ''),
            'account_id': account_id,
            'name': account_data.get('name', ''),
            'password': account_data.get('password', ''),
            'region': account_data.get('region', ''),
            'thread_id': thread_id,
            'timestamp': datetime.now().isoformat()
        }
    return False, None, None

def save_rare_account(account_data, rtype, reason, rscore, is_ghost=False):
    try:
        if is_ghost:
            filename = os.path.join(GHOST_RARE_FOLDER, "rare-ghost.json")
        else:
            region = account_data.get('region', 'UNKNOWN')
            filename = os.path.join(RARE_ACCOUNTS_FOLDER, f"rare-{region}.json")
        entry = {
            'uid': account_data["uid"], 'password': account_data["password"],
            'account_id': account_data.get("account_id", "N/A"), 'name': account_data["name"],
            'region': "BIGBULL" if is_ghost else account_data.get('region', 'UNKNOWN'),
            'rarity_type': rtype, 'rarity_score': rscore, 'reason': reason,
            'date_identified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'jwt_token': account_data.get('jwt_token', ''), 'thread_id': account_data.get('thread_id', 'N/A')
        }
        with get_lock(filename) as lock:
            data = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = []
            existing = [x.get('account_id') for x in data]
            if account_data.get("account_id", "N/A") not in existing:
                data.append(entry)
                with open(filename + '.tmp', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(filename + '.tmp', filename)
                return True
        return False
    except:
        return False

def save_couple_account(acc1, acc2, reason, is_ghost=False):
    try:
        if is_ghost:
            filename = os.path.join(GHOST_COUPLES_FOLDER, "couples-ghost.json")
        else:
            region = acc1.get('region', 'UNKNOWN')
            filename = os.path.join(COUPLES_ACCOUNTS_FOLDER, f"couples-{region}.json")
        couple_id = f"{acc1.get('account_id', 'N/A')}_{acc2.get('account_id', 'N/A')}"
        entry = {
            'couple_id': couple_id, 'account1': acc1, 'account2': acc2,
            'reason': reason, 'region': "BIGBULL" if is_ghost else acc1.get('region', 'UNKNOWN'),
            'date_matched': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with get_lock(filename) as lock:
            data = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = []
            existing = [x.get('couple_id') for x in data]
            if couple_id not in existing:
                data.append(entry)
                with open(filename + '.tmp', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(filename + '.tmp', filename)
                return True
        return False
    except:
        return False

def print_rarity_found(account_data, rarity_type, reason, rarity_score):
    color = Fore.LIGHTMAGENTA_EX
    print(f"\n{color}{Colors.BRIGHT}💎 RARE ACCOUNT FOUND!{Colors.RESET}")
    print(f"{color}🎯 Type: {rarity_type}{Colors.RESET}")
    print(f"{color}⭐ Rarity Score: {rarity_score}{Colors.RESET}")
    print(f"{color}👤 Name: {account_data['name']}{Colors.RESET}")
    print(f"{color}🆔 UID: {account_data['uid']}{Colors.RESET}")
    print(f"{color}🎮 Account ID: {account_data.get('account_id', 'N/A')}{Colors.RESET}")
    print(f"{color}📝 Reason: {reason}{Colors.RESET}")
    print(f"{color}🧵 Thread: {account_data.get('thread_id', 'N/A')}{Colors.RESET}")
    print(f"{color}🌍 Region: {account_data.get('region', 'N/A')}{Colors.RESET}\n")

def print_couples_found(account1, account2, reason):
    color = Fore.LIGHTCYAN_EX
    print(f"\n{color}{Colors.BRIGHT}💑 COUPLES ACCOUNT FOUND!{Colors.RESET}")
    print(f"{color}📝 Reason: {reason}{Colors.RESET}")
    print(f"{color}👤 Account 1: {account1['name']} (ID: {account1.get('account_id', 'N/A')}) - Thread {account1.get('thread_id', 'N/A')}{Colors.RESET}")
    print(f"{color}👤 Account 2: {account2['name']} (ID: {account2.get('account_id', 'N/A')}) - Thread {account2.get('thread_id', 'N/A')}{Colors.RESET}")
    print(f"{color}🆔 UIDs: {account1['uid']} & {account2['uid']}{Colors.RESET}")
    print(f"{color}🌍 Region: {account1.get('region', 'N/A')}{Colors.RESET}\n")

def print_success_box(account_data, count, total):
    color = get_random_color()
    print(f"\n{color}{Colors.BRIGHT}╔════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{color}{Colors.BRIGHT}║ ✅ ACCOUNT #{count}/{total} GENERATED SUCCESSFULLY!{Colors.RESET}".ljust(71) + f"{color}{Colors.BRIGHT}║{Colors.RESET}")
    print(f"{color}{Colors.BRIGHT}╠════════════════════════════════════════════════╣{Colors.RESET}")
    print(f"{color}{Colors.BRIGHT}║ 📌 UID:        {Fore.WHITE}{account_data.get('uid', 'N/A')}{Colors.RESET}".ljust(71) + f"{color}{Colors.BRIGHT}║{Colors.RESET}")
    print(f"{color}{Colors.BRIGHT}║ 🔑 PASSWORD:   {Fore.WHITE}{account_data.get('password', 'N/A')}{Colors.RESET}".ljust(71) + f"{color}{Colors.BRIGHT}║{Colors.RESET}")
    print(f"{color}{Colors.BRIGHT}║ 👤 NAME:       {Fore.WHITE}{account_data.get('name', 'N/A')}{Colors.RESET}".ljust(71) + f"{color}{Colors.BRIGHT}║{Colors.RESET}")
    print(f"{color}{Colors.BRIGHT}║ 🎮 ACCOUNT ID: {get_random_color()}{Colors.BRIGHT}{account_data.get('account_id', 'N/A')}{Colors.RESET}".ljust(71) + f"{color}{Colors.BRIGHT}║{Colors.RESET}")
    print(f"{color}{Colors.BRIGHT}╚════════════════════════════════════════════════╝{Colors.RESET}")

def install_requirements():
    packages = ['requests', 'pycryptodome', 'colorama', 'urllib3', 'psutil']
    for pkg in packages:
        try:
            if pkg == 'pycryptodome':
                import Crypto
            else:
                importlib.import_module(pkg)
        except ImportError:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '--quiet'])
            except:
                return False
    return True

def safe_exit(signum=None, frame=None):
    global EXIT_FLAG
    EXIT_FLAG = True
    print(f"\n{get_random_color()}{Colors.BRIGHT}👋 Thanks for using BIGBULL Account Generator!{Colors.RESET}")
    sys.exit(0)

signal.signal(signal.SIGINT, safe_exit)
signal.signal(signal.SIGTERM, safe_exit)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    color = get_random_color()
    banner = f"""
{color}{Colors.BRIGHT}
 ██████╗░██╗░██████╗░██████╗░██╗░░░██╗██╗░░░░░
 ██╔══██╗██║██╔════╝░██╔══██╗██║░░░██║██║░░░░░
 ██████╦╝██║██║░░██╗░██████╦╝██║░░░██║██║░░░░░
 ██╔══██╗██║██║░░╚██╗██╔══██╗██║░░░██║██║░░░░░
 ██████╦╝██║╚██████╔╝██████╦╝╚██████╔╝███████╗
 ╚═════╝░╚═╝░╚═════╝░╚═════╝░░╚═════╝░╚══════╝

               ░█████╗░██╗░░██╗███████╗░█████╗░████████╗░██████╗
               ██╔══██╗██║░░██║██╔════╝██╔══██╗╚══██╔══╝██╔════╝
               ██║░░╚═╝███████║█████╗░░███████║░░░██║░░░╚█████╗░
               ██║░░██╗██╔══██║██╔══╝░░██╔══██║░░░██║░░░░╚═══██╗
               ╚█████╔╝██║░░██║███████╗██║░░██║░░░██║░░░██████╔╝
               ░╚════╝░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚═════╝░

{Colors.RESET}
{get_random_color()}{Colors.BRIGHT}                   BIG BULL CHEATS OFFICIAL{Colors.RESET}
{get_random_color()}{Colors.BRIGHT}                        BBC GEN  V1 {Colors.RESET}
{get_random_color()}{Colors.BRIGHT}                POWERED BY BIG BULL TEAM{Colors.RESET}
{get_random_color()}{Colors.BRIGHT}           OFFICIAL TELEGRAM : @BIGBULLCHEAT{Colors.RESET}
{get_random_color()}{Colors.BRIGHT}     NOTE : USE PROTON OR 1.1.1.1 VPN FOR BEST RESULTS{Colors.RESET}
"""
    print(banner)

def print_success(message):
    color = get_random_color()
    print(f"{color}{Colors.BRIGHT}✅ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Fore.RED}{Colors.BRIGHT}❌ {message}{Colors.RESET}")

def print_warning(message):
    ignored_errors = [
        "429 Client Error: Too Many Requests",
        "503 Server Error: Service Temporarily Unavailable",
        "grant failed: 429",
        "Create account failed: 503"
    ]
    for ignored_error in ignored_errors:
        if ignored_error in message:
            return
    print(f"{Fore.YELLOW}{Colors.BRIGHT}⚠️ {message}{Colors.RESET}")

def print_registration_status(count, total, name, uid, password, account_id, region, is_ghost=False):
    print(f"{get_random_color()}{Colors.BRIGHT}📝 Registration {count}/{total}{Colors.RESET}")
    print(f"{get_random_color()}👤 Name: {get_random_color()}{name}{Colors.RESET}")
    print(f"{get_random_color()}🆔 UID: {get_random_color()}{uid}{Colors.RESET}")
    print(f"{get_random_color()}🎮 Account ID: {get_random_color()}{account_id}{Colors.RESET}")
    print(f"{get_random_color()}🔑 Password: {get_random_color()}{password}{Colors.RESET}")
    if is_ghost:
        print(f"{get_random_color()}🌍 Mode: {Fore.LIGHTMAGENTA_EX}GHOST Mode{Colors.RESET}")
    else:
        print(f"{get_random_color()}🌍 Region: {get_random_color()}{region}{Colors.RESET}")
    print()

def generate_exponent():
    exp_digits = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    num = random.randint(1, 9999)
    return ''.join(exp_digits[d] for d in f"{num:04d}")

def generate_random_name(base):
    return f"{base}{generate_exponent()}"

def generate_custom_password(user_prefix):
    random_part = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(8))
    return f"{user_prefix}_{_HIDDEN}_{random_part}"

def encode_varint(n):
    if n < 0:
        return b''
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            byte |= 0x80
        result.append(byte)
        if not n:
            break
    return bytes(result)

def create_proto_field(field_num, value):
    if isinstance(value, dict):
        nested = create_proto_field(field_num, value)
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(nested)) + nested
    elif isinstance(value, int):
        header = (field_num << 3) | 0
        return encode_varint(header) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        encoded_val = value.encode() if isinstance(value, str) else value
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(encoded_val)) + encoded_val
    return b''

def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())

def aes_encrypt(hex_data):
    data = bytes.fromhex(hex_data)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, AES.block_size))

def encrypt_api(plain_hex):
    plain = bytes.fromhex(plain_hex)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(plain, AES.block_size)).hex()

def save_normal_account(account_data, region, is_ghost=False):
    try:
        if is_ghost:
            filename = os.path.join(GHOST_ACCOUNTS_FOLDER, "ghost.json")
        else:
            filename = os.path.join(ACCOUNTS_FOLDER, f"accounts-{region}.json")
        entry = {
            'uid': account_data["uid"], 'password': account_data["password"],
            'account_id': account_data.get("account_id", "N/A"), 'name': account_data["name"],
            'region': "BIGBULL" if is_ghost else region,
            'date_created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'thread_id': account_data.get('thread_id', 'N/A')
        }
        with get_lock(filename) as lock:
            data = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = []
            existing = [x.get('account_id') for x in data]
            if account_data.get("account_id", "N/A") not in existing:
                data.append(entry)
                with open(filename + '.tmp', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(filename + '.tmp', filename)
                return True
        return False
    except:
        return False

def save_jwt_token(account_data, jwt_token, region, is_ghost=False):
    try:
        if is_ghost:
            filename = os.path.join(GHOST_FOLDER, "tokens-ghost.json")
        else:
            filename = os.path.join(TOKENS_FOLDER, f"tokens-{region}.json")
        entry = {
            'uid': account_data["uid"], 'account_id': account_data.get("account_id", "N/A"),
            'jwt_token': jwt_token, 'name': account_data["name"], 'password': account_data["password"],
            'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'region': "BIGBULL" if is_ghost else region, 'thread_id': account_data.get('thread_id', 'N/A')
        }
        with get_lock(filename) as lock:
            data = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = []
            existing = [x.get('account_id') for x in data]
            if account_data.get("account_id", "N/A") not in existing:
                data.append(entry)
                with open(filename + '.tmp', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(filename + '.tmp', filename)
                return True
        return False
    except:
        return False

def smart_delay():
    time.sleep(random.uniform(0.5, 1.5))

def create_account(region, account_name, password_prefix, is_ghost=False):
    if EXIT_FLAG:
        return None
    try:
        password = generate_custom_password(password_prefix)
        url = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
        payload = {"app_id": 100067, "client_type": 2, "password": password, "source": 2}
        headers = {
            "User-Agent": "GarenaMSDK/4.0.39(SM-A325M;Android 13;en;HK;)",
            "Accept": "application/json", "Content-Type": "application/json; charset=utf-8",
            "Accept-Encoding": "gzip", "Connection": "Keep-Alive"
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        response.raise_for_status()
        res_json = response.json()
        if "data" in res_json and "uid" in res_json["data"]:
            uid = res_json["data"]["uid"]
            smart_delay()
            return get_token(uid, password, region, account_name, password_prefix, is_ghost)
        return None
    except Exception as e:
        print_warning(f"Create account failed: {e}")
        smart_delay()
        return None

def get_token(uid, password, region, account_name, password_prefix, is_ghost=False):
    if EXIT_FLAG:
        return None
    try:
        url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        headers = {
            "Accept-Encoding": "gzip", "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded", "Host": "100067.connect.garena.com",
            "User-Agent": "GarenaMSDK/4.0.19P8(ASUS_Z01QD ;Android 12;en;US;)",
        }
        body = {"uid": uid, "password": password, "response_type": "token", "client_type": "2", "client_secret": HEX_KEY, "client_id": "100067"}
        response = requests.post(url, headers=headers, data=body, timeout=30, verify=False)
        response.raise_for_status()
        if 'open_id' in response.json():
            open_id = response.json()['open_id']
            access_token = response.json()["access_token"]
            keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
            encoded = ""
            for i in range(len(open_id)):
                encoded += chr(ord(open_id[i]) ^ keystream[i % len(keystream)])
            field = codecs.decode(''.join(c if 32 <= ord(c) <= 126 else f'\\u{ord(c):04x}' for c in encoded), 'unicode_escape').encode('latin1')
            smart_delay()
            return major_register(access_token, open_id, field, uid, password, region, account_name, password_prefix, is_ghost)
        return None
    except Exception as e:
        print_warning(f"Token grant failed: {e}")
        smart_delay()
        return None

def major_register(access_token, open_id, field, uid, password, region, account_name, password_prefix, is_ghost=False):
    if EXIT_FLAG:
        return None
    for attempt in range(10):
        try:
            if is_ghost:
                url = "https://loginbp.ggblueshark.com/MajorRegister"
            elif region.upper() in ["ME", "TH"]:
                url = "https://loginbp.common.ggbluefox.com/MajorRegister"
            else:
                url = "https://loginbp.ggblueshark.com/MajorRegister"
            name = generate_random_name(account_name)
            headers = {
                "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
                "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
                "Host": "loginbp.ggblueshark.com" if is_ghost or region.upper() not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
                "ReleaseVersion": "OB53", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
                "X-GA": "v1 1", "X-Unity-Version": "2018.4."
            }
            lang_code = "pt" if is_ghost else REGION_LANG.get(region.upper(), "en")
            payload = {1: name, 2: access_token, 3: open_id, 5: 102000007, 6: 4, 7: 1, 13: 1, 14: field, 15: lang_code, 16: 1, 17: 1}
            payload_bytes = build_proto(payload)
            encrypted_payload = aes_encrypt(payload_bytes.hex())
            requests.post(url, headers=headers, data=encrypted_payload, verify=False, timeout=30)
            login_result = major_login(uid, password, access_token, open_id, region, is_ghost)
            account_id = login_result.get("account_id", "N/A")
            jwt_token = login_result.get("jwt_token", "")
            if account_id != "N/A":
                if not is_ghost and jwt_token and region.upper() != "BR":
                    try:
                        force_region_bind(region, jwt_token)
                    except:
                        pass
                return {
                    "uid": uid, "password": password, "name": name,
                    "region": "GHOST" if is_ghost else region, "status": "success",
                    "account_id": account_id, "jwt_token": jwt_token
                }
            else:
                smart_delay()
        except:
            smart_delay()
    return None

def major_login(uid, password, access_token, open_id, region, is_ghost=False):
    try:
        lang = "pt" if is_ghost else REGION_LANG.get(region.upper(), "en")
        payload_parts = [
            b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
            lang.encode("ascii"),
            b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118692\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
        ]
        payload = b''.join(payload_parts)
        if is_ghost:
            url = "https://loginbp.ggblueshark.com/MajorLogin"
        elif region.upper() in ["ME", "TH"]:
            url = "https://loginbp.common.ggbluefox.com/MajorLogin"
        else:
            url = "https://loginbp.ggblueshark.com/MajorLogin"
        headers = {
            "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
            "Host": "loginbp.ggblueshark.com" if is_ghost or region.upper() not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
            "ReleaseVersion": "OB53", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
            "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1"
        }
        data = payload.replace(b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', access_token.encode())
        data = data.replace(b'1d8ec0240ede109973f3321b9354b44d', open_id.encode())
        d = encrypt_api(data.hex())
        response = requests.post(url, headers=headers, data=bytes.fromhex(d), verify=False, timeout=30)
        if response.status_code == 200 and len(response.text) > 10:
            jwt_start = response.text.find("eyJ")
            if jwt_start != -1:
                jwt_token = response.text[jwt_start:]
                second_dot = jwt_token.find(".", jwt_token.find(".") + 1)
                if second_dot != -1:
                    jwt_token = jwt_token[:second_dot + 44]
                    try:
                        parts = jwt_token.split('.')
                        if len(parts) >= 2:
                            payload_part = parts[1]
                            padding = 4 - len(payload_part) % 4
                            if padding != 4:
                                payload_part += '=' * padding
                            decoded = base64.urlsafe_b64decode(payload_part)
                            data = json.loads(decoded)
                            account_id = data.get('account_id') or data.get('external_id')
                            if account_id:
                                return {"account_id": str(account_id), "jwt_token": jwt_token}
                    except:
                        pass
        return {"account_id": "N/A", "jwt_token": ""}
    except:
        return {"account_id": "N/A", "jwt_token": ""}

def force_region_bind(region, jwt_token):
    try:
        url = "https://loginbp.common.ggbluefox.com/ChooseRegion" if region.upper() in ["ME","TH"] else "https://loginbp.ggblueshark.com/ChooseRegion"
        region_code = "RU" if region.upper() == "CIS" else region.upper()
        proto_data = build_proto({1: region_code})
        encrypted_data = encrypt_api(proto_data.hex())
        payload = bytes.fromhex(encrypted_data)
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; M2101K7AG Build/SKQ1.210908.001)",
            'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
            'Content-Type': "application/x-www-form-urlencoded", 'Expect': "100-continue",
            'Authorization': f"Bearer {jwt_token}", 'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1", 'ReleaseVersion': "OB53"
        }
        requests.post(url, data=payload, headers=headers, verify=False, timeout=30)
    except:
        pass

def generate_single_account(region, account_name, password_prefix, total_accounts, thread_id, is_ghost=False):
    global SUCCESS_COUNTER, RARE_COUNTER, COUPLES_COUNTER
    if EXIT_FLAG:
        return None
    with LOCK:
        if SUCCESS_COUNTER >= total_accounts:
            return None
    account_result = create_account(region, account_name, password_prefix, is_ghost)
    if not account_result or account_result.get("account_id", "N/A") == "N/A":
        return None
    account_result['thread_id'] = thread_id
    with LOCK:
        SUCCESS_COUNTER += 1
        current = SUCCESS_COUNTER
    print_registration_status(current, total_accounts, account_result["name"], 
                            account_result["uid"], account_result["password"], 
                            account_result.get("account_id", "N/A"), region, is_ghost)
    is_rare, rtype, reason, rscore = check_rarity(account_result)
    if is_rare:
        with LOCK:
            RARE_COUNTER += 1
        print_rarity_found(account_result, rtype, reason, rscore)
        save_rare_account(account_result, rtype, reason, rscore, is_ghost)
    is_couple, creason, partner = check_couple(account_result, thread_id)
    if is_couple and partner:
        with LOCK:
            COUPLES_COUNTER += 1
        print_couples_found(account_result, partner, creason)
        save_couple_account(account_result, partner, creason, is_ghost)
    save_normal_account(account_result, "GHOST" if is_ghost else region, is_ghost)
    if account_result.get('jwt_token'):
        save_jwt_token(account_result, account_result['jwt_token'], "GHOST" if is_ghost else region, is_ghost)
    return {"account": account_result}

def worker_thread(region, account_name, password_prefix, total_accounts, thread_id, is_ghost=False):
    thread_color = get_random_color()
    print(f"{thread_color}{Colors.BRIGHT}🧵 Thread {thread_id} started{Colors.RESET}")
    while not EXIT_FLAG:
        with LOCK:
            if SUCCESS_COUNTER >= total_accounts:
                break
        generate_single_account(region, account_name, password_prefix, total_accounts, thread_id, is_ghost)
        time.sleep(random.uniform(0.3, 0.8))
    print(f"{thread_color}{Colors.BRIGHT}🧵 Thread {thread_id} finished{Colors.RESET}")

def generate_accounts_flow():
    global SUCCESS_COUNTER, TARGET_ACCOUNTS, RARE_COUNTER, COUPLES_COUNTER, RARITY_SCORE_THRESHOLD, START_TIME
    clear_screen()
    display_banner()
    
    cpu_count = psutil.cpu_count() or 1
    recommended_threads = min(cpu_count, 3)
    
    print(f"{get_random_color()}{Colors.BRIGHT}🌍 Available Regions:{Colors.RESET}")
    regions_to_show = [region for region in REGION_LANG.keys() if region != "BR"]
    for i, region in enumerate(regions_to_show, 1):
        print(f"{get_random_color()}{i}) {get_random_color()}{region} ({REGION_LANG[region]}){Colors.RESET}")
    print(f"{get_random_color()}{len(regions_to_show)+1}) {Fore.LIGHTMAGENTA_EX}GHOST Mode{Colors.RESET}")
    print(f"{get_random_color()}00) {Fore.YELLOW}Back to Main Menu{Colors.RESET}")
    print(f"{get_random_color()}000) {Fore.RED}Exit{Colors.RESET}")

    while True:
        try:
            choice = input(f"\n{get_random_color()}{Colors.BRIGHT}🎯 Choose option: {Colors.RESET}").strip().upper()
            if choice == "00":
                return
            elif choice == "000":
                safe_exit()
            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(regions_to_show):
                    selected_region = regions_to_show[choice_num - 1]
                    is_ghost = False
                    break
                elif choice_num == len(regions_to_show) + 1:
                    selected_region = "BR"
                    is_ghost = True
                    break
                else:
                    print_error("Invalid option. Please choose a valid number.")
            elif choice in regions_to_show:
                selected_region = choice
                is_ghost = False
                break
            elif choice == "GHOST":
                selected_region = "BR"
                is_ghost = True
                break
            else:
                print_error("Invalid option. Please choose a valid region.")
        except ValueError:
            print_error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            safe_exit()

    clear_screen()
    display_banner()
    
    if is_ghost:
        print(f"{Fore.LIGHTMAGENTA_EX}{Colors.BRIGHT}🌍 Selected Mode: GHOST MODE{Colors.RESET}")
    else:
        print(f"{get_random_color()}{Colors.BRIGHT}🌍 Selected Region: {selected_region} ({REGION_LANG[selected_region]}){Colors.RESET}")

    while True:
        try:
            account_count = int(input(f"\n{get_random_color()}{Colors.BRIGHT}🎯 Total Accounts to Generate: {Colors.RESET}"))
            if account_count > 0:
                break
            else:
                print_error("Please enter a positive number.")
        except ValueError:
            print_error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            safe_exit()

    while True:
        account_name = input(f"\n{get_random_color()}{Colors.BRIGHT}👤 Enter account name prefix: {Colors.RESET}").strip()
        if account_name:
            break
        else:
            print_error("Account name cannot be empty.")

    while True:
        password_prefix = input(f"\n{get_random_color()}{Colors.BRIGHT}🔑 Enter password prefix: {Colors.RESET}").strip()
        if password_prefix:
            break
        else:
            print_error("Password prefix cannot be empty.")

    while True:
        try:
            rarity_threshold = int(input(f"\n{get_random_color()}{Colors.BRIGHT}⭐ Rarity Threshold (1-10, default 8): {Colors.RESET}").strip() or "8")
            if 1 <= rarity_threshold <= 10:
                RARITY_SCORE_THRESHOLD = rarity_threshold
                break
            else:
                print_error("Please enter a number between 1 and 10.")
        except ValueError:
            print_error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            safe_exit()

    while True:
        try:
            thread_count = int(input(f"\n{get_random_color()}{Colors.BRIGHT}🧵 Thread Count (Recommended: {recommended_threads}): {Colors.RESET}").strip())
            if thread_count > 0:
                break
            else:
                print_error("Thread count must be positive.")
        except ValueError:
            print_error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            safe_exit()

    clear_screen()
    display_banner()
    
    if is_ghost:
        print(f"{Fore.LIGHTMAGENTA_EX}{Colors.BRIGHT}🚀 Starting GHOST MODE Account Generation{Colors.RESET}")
    else:
        print(f"{get_random_color()}{Colors.BRIGHT}🚀 Starting Account Generation for {selected_region}{Colors.RESET}")
    
    print(f"{get_random_color()}{Colors.BRIGHT}🎯 Target Accounts: {account_count}{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}👤 Name Prefix: {account_name}{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}🔑 Password Prefix: {password_prefix}{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}⭐ Rarity Threshold: {RARITY_SCORE_THRESHOLD}+{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}🧵 Threads: {thread_count}{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}📁 Saving to: {ACCOUNTS_FOLDER}{Colors.RESET}")
    print(f"\n{get_random_color()}{Colors.BRIGHT}⏳ Starting in 3 seconds...{Colors.RESET}")
    time.sleep(3)

    SUCCESS_COUNTER = 0
    TARGET_ACCOUNTS = account_count
    RARE_COUNTER = 0
    COUPLES_COUNTER = 0
    START_TIME = time.time()
    
    print(f"\n{get_random_color()}{Colors.BRIGHT}🚀 Starting generation with {thread_count} threads...{Colors.RESET}\n")
    
    threads = []
    for i in range(thread_count):
        t = threading.Thread(target=worker_thread, args=(selected_region, account_name, password_prefix, account_count, i+1, is_ghost))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(2)
            with LOCK:
                current_count = SUCCESS_COUNTER
            progress = (current_count / account_count) * 100 if account_count > 0 else 0
            elapsed = time.time() - START_TIME
            speed = current_count / elapsed if elapsed > 0 else 0
            eta = (account_count - current_count) / speed if speed > 0 else 0
            print(f"\r{get_random_color()}{Colors.BRIGHT}📊 Progress: {current_count}/{account_count} ({progress:.1f}%) | ⚡ | www.ffglory.in{Colors.RESET}", end="")
            if current_count >= account_count:
                break
    except KeyboardInterrupt:
        print_warning("Generation interrupted by user!")
        global EXIT_FLAG
        EXIT_FLAG = True
        for t in threads:
            t.join(timeout=1)

    for t in threads:
        t.join(timeout=5)

    elapsed_time = time.time() - START_TIME
    print(f"\n\n{get_random_color()}{Colors.BRIGHT}🎉 Generation completed!{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}📊 Accounts generated: {SUCCESS_COUNTER}/{account_count}{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}💎 Rare accounts found: {RARE_COUNTER}{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}💑 Couples pairs found: {COUPLES_COUNTER}{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}⭐ Rarity threshold used: {RARITY_SCORE_THRESHOLD}+{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}⏱️ Time taken: {elapsed_time:.2f} seconds{Colors.RESET}")
    print(f"{get_random_color()}{Colors.BRIGHT}⚡ Speed: {SUCCESS_COUNTER/elapsed_time:.2f} accounts/second{Colors.RESET}")
    
    if is_ghost:
        print(f"{Fore.LIGHTMAGENTA_EX}{Colors.BRIGHT}📁 GHOST accounts saved in: {GHOST_ACCOUNTS_FOLDER}{Colors.RESET}")
    else:
        print(f"{get_random_color()}{Colors.BRIGHT}📁 Accounts saved in: {ACCOUNTS_FOLDER}{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT}💎 Rare accounts saved in: {RARE_ACCOUNTS_FOLDER}{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT}💑 Couples accounts saved in: {COUPLES_ACCOUNTS_FOLDER}{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT}🔐 JWT tokens saved in: {TOKENS_FOLDER}{Colors.RESET}")
    
    input(f"\n{get_random_color()}{Colors.BRIGHT}▶ Press Enter to continue...{Colors.RESET}")

def view_saved_accounts():
    clear_screen()
    display_banner()
    
    print(f"{get_random_color()}{Colors.BRIGHT}📁 Viewing Saved Accounts{Colors.RESET}")
    print(f"{get_random_color()}{'─'*60}{Colors.RESET}\n")
    
    total_accounts = 0
    total_rare = 0
    total_couples = 0
    
    if os.path.exists(ACCOUNTS_FOLDER):
        files = [f for f in os.listdir(ACCOUNTS_FOLDER) if f.endswith('.json')]
        if files:
            print(f"{get_random_color()}{Colors.BRIGHT}📂 NORMAL ACCOUNTS:{Colors.RESET}")
            for f in files:
                try:
                    with open(os.path.join(ACCOUNTS_FOLDER, f), 'r') as file:
                        data = json.load(file)
                        count = len(data)
                        total_accounts += count
                        print(f"{get_random_color()}   📄 {f}: {Fore.WHITE}{count} accounts{Colors.RESET}")
                except:
                    pass
        else:
            print(f"{get_random_color()}   No normal accounts found.{Colors.RESET}")
    
    if os.path.exists(RARE_ACCOUNTS_FOLDER):
        files = [f for f in os.listdir(RARE_ACCOUNTS_FOLDER) if f.endswith('.json')]
        if files:
            print(f"\n{get_random_color()}{Colors.BRIGHT}✨ RARE ACCOUNTS:{Colors.RESET}")
            for f in files:
                try:
                    with open(os.path.join(RARE_ACCOUNTS_FOLDER, f), 'r') as file:
                        data = json.load(file)
                        count = len(data)
                        total_rare += count
                        print(f"{get_random_color()}   📄 {f}: {Fore.WHITE}{count} rare accounts{Colors.RESET}")
                except:
                    pass
        else:
            print(f"{get_random_color()}   No rare accounts found.{Colors.RESET}")
    
    if os.path.exists(COUPLES_ACCOUNTS_FOLDER):
        files = [f for f in os.listdir(COUPLES_ACCOUNTS_FOLDER) if f.endswith('.json')]
        if files:
            print(f"\n{get_random_color()}{Colors.BRIGHT}💑 COUPLE ACCOUNTS:{Colors.RESET}")
            for f in files:
                try:
                    with open(os.path.join(COUPLES_ACCOUNTS_FOLDER, f), 'r') as file:
                        data = json.load(file)
                        count = len(data)
                        total_couples += count
                        print(f"{get_random_color()}   📄 {f}: {Fore.WHITE}{count} couples{Colors.RESET}")
                except:
                    pass
        else:
            print(f"{get_random_color()}   No couples accounts found.{Colors.RESET}")
    
    ghost_file = os.path.join(GHOST_ACCOUNTS_FOLDER, "ghost.json")
    if os.path.exists(ghost_file):
        try:
            with open(ghost_file, 'r') as file:
                data = json.load(file)
                total_accounts += len(data)
                print(f"\n{get_random_color()}{Colors.BRIGHT}👻 GHOST ACCOUNTS:{Colors.RESET}")
                print(f"{get_random_color()}   📄 ghost.json: {Fore.WHITE}{len(data)} accounts{Colors.RESET}")
        except:
            pass
    
    print(f"\n{get_random_color()}{Colors.BRIGHT}📊 TOTAL STATS:{Colors.RESET}")
    print(f"{get_random_color()}   📝 Normal: {total_accounts} accounts{Colors.RESET}")
    print(f"{get_random_color()}   ✨ Rare: {total_rare} accounts{Colors.RESET}")
    print(f"{get_random_color()}   💑 Couples: {total_couples} pairs{Colors.RESET}")
    print(f"\n{get_random_color()}{'─'*60}{Colors.RESET}")
    input(f"\n{get_random_color()}{Colors.BRIGHT}▶ Press Enter to continue...{Colors.RESET}")

def about_section():
    clear_screen()
    display_banner()
    
    print(f"{get_random_color()}{Colors.BRIGHT}ℹ️ ABOUT BIGBULL ACCOUNT GENERATOR{Colors.RESET}")
    print(f"{get_random_color()}{'─'*60}{Colors.RESET}\n")
    
    print(f"{get_random_color()}{Colors.BRIGHT}🔥 Version:{Colors.RESET} 1.0 PREMIUM")
    print(f"{get_random_color()}{Colors.BRIGHT}🐂 Creator:{Colors.RESET} BIG BULL CHEATS")
    print(f"{get_random_color()}{Colors.BRIGHT}🎯 Purpose:{Colors.RESET} Free Fire Account Generator")
    print(f"{get_random_color()}{Colors.BRIGHT}📅 Release:{Colors.RESET} 2024")
    
    print(f"\n{get_random_color()}{Colors.BRIGHT}✨ FEATURES:{Colors.RESET}")
    print(f"{get_random_color()}   • Multi-region support (ME, IND, ID, VN, TH, BD, PK, TW, CIS, SAC, BR)")
    print(f"{get_random_color()}   • GHOST Mode for special region accounts")
    print(f"{get_random_color()}   • Automatic rare account detection with scoring system")
    print(f"{get_random_color()}   • Couple account matching (sequential, mirror, love numbers)")
    print(f"{get_random_color()}   • Multi-threaded generation for high speed")
    print(f"{get_random_color()}   • Automatic JWT token extraction and saving")
    print(f"{get_random_color()}   • Customizable name and password prefixes")
    print(f"{get_random_color()}   • Live statistics during generation")
    print(f"{get_random_color()}   • Organized JSON storage in categorized folders")
    
    print(f"\n{get_random_color()}{Colors.BRIGHT}📁 STORAGE LOCATIONS:{Colors.RESET}")
    print(f"{get_random_color()}   • Normal Accounts: {ACCOUNTS_FOLDER}")
    print(f"{get_random_color()}   • Rare Accounts: {RARE_ACCOUNTS_FOLDER}")
    print(f"{get_random_color()}   • Couples Accounts: {COUPLES_ACCOUNTS_FOLDER}")
    print(f"{get_random_color()}   • JWT Tokens: {TOKENS_FOLDER}")
    print(f"{get_random_color()}   • GHOST Mode: {GHOST_FOLDER}")
    
    print(f"\n{get_random_color()}{Colors.BRIGHT}⚠️ DISCLAIMER:{Colors.RESET}")
    print(f"{get_random_color()}   This tool is for educational purposes only.")
    print(f"{get_random_color()}   Use at your own risk. The developers are not responsible")
    print(f"{get_random_color()}   for any misuse of this tool.")
    
    print(f"\n{get_random_color()}{Colors.BRIGHT}📢 CONNECT WITH US:{Colors.RESET}")
    print(f"{get_random_color()}   • Telegram: @BIGBULLCHEAT")
    print(f"{get_random_color()}   • Channel: @BIGBULLCHEATS")
    
    print(f"\n{get_random_color()}{'─'*60}{Colors.RESET}")
    input(f"\n{get_random_color()}{Colors.BRIGHT}▶ Press Enter to continue...{Colors.RESET}")

def main_menu():
    while True:
        clear_screen()
        display_banner()
        print(f"{get_random_color()}{Colors.BRIGHT}{'='*60}{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT}📋 MAIN MENU{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT}{'='*60}{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT} 1{Colors.RESET} → {get_random_color()}GENERATE ACCOUNTS{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT} 2{Colors.RESET} → {get_random_color()}VIEW SAVED ACCOUNTS{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT} 3{Colors.RESET} → {get_random_color()}ABOUT{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT} 0{Colors.RESET} → {Fore.RED}EXIT{Colors.RESET}")
        print(f"{get_random_color()}{Colors.BRIGHT}{'='*60}{Colors.RESET}")

        try:
            choice = input(f"\n{get_random_color()}{Colors.BRIGHT}🎯 CHOOSE OPTION: {Colors.RESET}").strip()
            
            if choice == "1":
                generate_accounts_flow()
            elif choice == "2":
                view_saved_accounts()
            elif choice == "3":
                about_section()
            elif choice == "0":
                print(f"\n{get_random_color()}{Colors.BRIGHT}👋 THANK YOU FOR USING BIGBULL GENERATOR!{Colors.RESET}")
                sys.exit(0)
            else:
                print_error("Invalid option. Please choose 1, 2, 3, or 0.")
                time.sleep(1)
        except KeyboardInterrupt:
            safe_exit()

if __name__ == "__main__":
    try:
        if install_requirements():
            main_menu()
    except KeyboardInterrupt:
        safe_exit()
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        print(f"\n{Fore.YELLOW}{Colors.BRIGHT}🔄 Restarting script...{Colors.RESET}")
        time.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)