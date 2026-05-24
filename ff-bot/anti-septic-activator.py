import json
import requests
import time
import logging
import random
import base64
import threading
import subprocess
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import sys
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import warnings
warnings.filterwarnings("ignore")

sys.path.append(os.getcwd())
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

try:
    import MajorLoginRes_pb2
    print("✅ MajorLoginRes_pb2 imported successfully")
except ImportError as e:
    print(f"❌ Failed to import MajorLoginRes_pb2: {e}")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("activation_log.txt")
    ]
)

class MultiRegionActivator:
    def __init__(self, max_workers=8, turbo_mode=True):
        self.key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
        self.iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
        self.clear_activation_log()
        self.regions = {
            'IND': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.common.ggbluefox.com/MajorLogin',
                'get_login_data_url': 'https://client.ind.freefiremobile.com/GetLoginData',
                'client_host': 'client.ind.freefiremobile.com'
            },
            'BD': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.ggpolarbear.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.ggpolarbear.com/GetLoginData',
                'client_host': 'clientbp.ggpolarbear.com'
            },
            'PK': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.ggpolarbear.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.ggpolarbear.com/GetLoginData',
                'client_host': 'clientbp.ggpolarbear.com'
            },
            'NA': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.ggpolarbear.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.ggpolarbear.com/GetLoginData',
                'client_host': 'clientbp.ggpolarbear.com'
            },
            'LK': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.ggpolarbear.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.ggpolarbear.com/GetLoginData',
                'client_host': 'clientbp.ggpolarbear.com'
            },
            'ID': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.ggpolarbear.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.ggpolarbear.com/GetLoginData',
                'client_host': 'clientbp.ggpolarbear.com'
            },
            'TH': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.ggpolarbear.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.common.ggbluefox.com/GetLoginData',
                'client_host': 'clientbp.common.ggbluefox.com'
            },
            'VN': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.ggpolarbear.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.ggpolarbear.com/GetLoginData',
                'client_host': 'clientbp.ggpolarbear.com'
            },
            'BR': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.ggpolarbear.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.ggpolarbear.com/GetLoginData',
                'client_host': 'clientbp.ggpolarbear.com'
            },
            'ME': {
                'guest_url': 'https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant',
                'major_login_url': 'https://loginbp.common.ggbluefox.com/MajorLogin',
                'get_login_data_url': 'https://clientbp.ggpolarbear.com/GetLoginData',
                'client_host': 'clientbp.ggpolarbear.com'
            }
        }
        
        self.max_workers = max_workers
        self.turbo_mode = turbo_mode
        self.request_times = []
        self.rate_limit_lock = threading.Lock()
        
        self.tcp_fast_open = self.check_tcp_fast_open()
        
        self.session = requests.Session()
        self.adapters = self.create_optimized_adapters()
        
        self.successful = 0
        self.failed = 0
        self.successful_accounts = []
        self.failed_accounts = []
        self.stats_lock = threading.Lock()
        self.selected_region = None
        self.stop_execution = False
        self.unauthorized_count = 0
        self.max_unauthorized_before_stop = 10
        
        print(f"🔧 Multi-Region Activator - Workers: {max_workers}, Turbo: {turbo_mode}")
        print(f"🌍 Supported regions: {', '.join(self.regions.keys())}")
    def clear_activation_log(self):
        try:
            log_file = "activation_log.txt"
            if os.path.exists(log_file):
                with open(log_file, 'w') as f:
                    f.write("")
                print(f"✅ Cleared activation log: {log_file}")
            else:
                with open(log_file, 'w') as f:
                    f.write("")
        except Exception as e:
            print(f"⚠️  Could not clear activation log: {e}") 
    def check_tcp_fast_open(self):
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'net.ipv4.tcp_fastopen'],
                capture_output=True, text=True, timeout=5
            )
            return int(result.stdout.strip()) >= 1
        except:
            return False
    
    def create_optimized_adapters(self):
        adapters = []
        configs = [
            {'pool_connections': 100, 'pool_maxsize': 100, 'max_retries': 1},
            {'pool_connections': 50, 'pool_maxsize': 50, 'max_retries': 0},
            {'pool_connections': 75, 'pool_maxsize': 75, 'max_retries': 2}
        ]
        for config in configs:
            adapter = requests.adapters.HTTPAdapter(**config)
            adapters.append(adapter)
        return adapters
    
    def rotate_adapter(self):
        adapter = random.choice(self.adapters)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def generate_fingerprint(self):
        user_agents = [
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ]
        
        accept_languages = [
            'en-US,en;q=0.9',
            'en-GB,en;q=0.8',
            'en-CA,en;q=0.7',
            'en-AU,en;q=0.6'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': random.choice(['1', '0']),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers'
        }
        
        self.session.headers.update(headers)
        self.rotate_adapter()
    
    def smart_rate_limit_bypass(self):
        if self.turbo_mode:
            delay = random.uniform(0.05, 0.15)
        else:
            delay = random.uniform(0.1, 0.3)
        time.sleep(delay)
        self.generate_fingerprint()
    
    def advanced_retry_strategy(self, attempt, max_attempts=3):
        if self.turbo_mode:
            base_delay = 1.5 ** attempt
        else:
            base_delay = 2 ** attempt
        jitter = random.uniform(0.8, 1.5)
        delay = base_delay * jitter
        logging.info(f"🔄 Advanced retry {attempt + 1}/{max_attempts} - Delay: {delay:.1f}s")
        time.sleep(delay)

    def encrypt_api(self, plain_text):
        try:
            plain_text = bytes.fromhex(plain_text)
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
            return cipher_text.hex()
        except Exception as e:
            logging.error(f"Encryption error: {e}")
            return None

    def parse_my_message(self, serialized_data):
        try:
            MajorLogRes = MajorLoginRes_pb2.MajorLoginRes()
            MajorLogRes.ParseFromString(serialized_data)
            jwt_token = MajorLogRes.token
            key = MajorLogRes.ak
            iv = MajorLogRes.aiv
            key_hex = key.hex() if key else None
            iv_hex = iv.hex() if iv else None
            return jwt_token, key_hex, iv_hex
        except Exception as e:
            logging.error(f"Failed to parse MajorLogin response: {e}")
            return None, None, None

    def guest_token(self, uid, password, region='IND'):
        if self.stop_execution:
            return None, None
            
        region_config = self.regions.get(region, self.regions['IND'])
        url = region_config['guest_url']
        data = {
            "uid": f"{uid}",
            "password": f"{password}",
            "response_type": "token",
            "client_type": "2",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_id": "100067",
        }
        max_attempts = 4 if self.turbo_mode else 3
        for attempt in range(max_attempts):
            try:
                if self.stop_execution:
                    return None, None
                    
                self.smart_rate_limit_bypass()
                self.generate_fingerprint()
                timeout = 8 if self.turbo_mode else 15
                response = self.session.post(url, data=data, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    data_json = response.json()
                    logging.info(f"✅ Guest tokens obtained for UID: {uid} (Region: {region})")
                    return data_json.get('access_token'), data_json.get('open_id')
                elif response.status_code == 429:
                    if self.turbo_mode:
                        logging.warning(f"🚫 Rate limit hit in turbo mode - aggressive retry")
                    else:
                        logging.warning(f"🚫 Rate limited (429) - Attempt {attempt + 1}/{max_attempts}")
                    self.advanced_retry_strategy(attempt, max_attempts)
                    continue
                elif response.status_code in [400, 401, 403]:
                    logging.error(f"❌ Client error {response.status_code} - Check credentials for {uid}")
                    if response.status_code == 401:
                        with self.stats_lock:
                            self.unauthorized_count += 1
                            if self.unauthorized_count >= self.max_unauthorized_before_stop:
                                print(f"\n🚨 CRITICAL: Too many 401 Unauthorized errors!")
                                print("💡 Possible reasons:")
                                print("   - Wrong region selected")
                                print("   - Server maintenance")
                                print("   - IP blocked")
                                print("   - Invalid credentials format")
                                self.stop_execution = True
                    return None, None
                else:
                    logging.warning(f"Guest token attempt {attempt + 1} failed with status {response.status_code}")
            except requests.exceptions.Timeout:
                logging.warning(f"⌛ Timeout on attempt {attempt + 1}")
            except Exception as e:
                logging.warning(f"Guest token attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                self.advanced_retry_strategy(attempt, max_attempts)
        logging.error(f"❌ All guest token attempts failed for {uid}")
        return None, None

    def major_login(self, access_token, open_id, region='IND'):
        if self.stop_execution:
            return None
            
        region_config = self.regions.get(region, self.regions['IND'])
        url = region_config['major_login_url']
        headers = {
            'X-Unity-Version': '2018.4.11f1',
            'ReleaseVersion': 'OB53',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-GA': 'v1 1',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; ASUS_Z01QD Build/QKQ1.190825.002)',
            'Host': 'loginbp.ggpolarbear.com',
            'Connection': 'Keep-Alive',
        }
        payload_template = bytes.fromhex(
            '1a13323032352d30372d33302031313a30323a3531220966726565206669726528013a07312e3131342e32422c416e64726f6964204f5320372e312e32202f204150492d323320284e32473438482f373030323530323234294a0848616e6468656c645207416e64726f69645a045749464960c00c68840772033332307a1f41524d7637205646507633204e454f4e20564d48207c2032343635207c203480019a1b8a010f416472656e6f2028544d292036343092010d4f70656e474c20455320332e319a012b476f6f676c657c31663361643662372d636562342d343934622d383730622d623164616364373230393131a2010c3139372e312e31322e313335aa0102656eb201203939366136323964626364623339363462653662363937386635643831346462ba010134c2010848616e6468656c64ca011073616d73756e6720534d2d473935354eea014066663930633037656239383135616633306134336234613966363031393531366530653463373033623434303932353136643064656661346365663531663261f00101ca0207416e64726f6964d2020457494649ca03203734323862323533646566633136343031386336303461316562626665626466e003daa907e803899b07f003bf0ff803ae088004999b078804daa9079004999b079804daa907c80403d204262f646174612f6170702f636f6d2e6474732e667265656669726574682d312f6c69622f61726de00401ea044832303837663631633139663537663261663465376665666630623234643964397c2f646174612f6170702f636f6d2e6474732e667265656669726574682d312f626173652e61706bf00403f804018a050233329a050a32303139313138363933a80503b205094f70656e474c455332b805ff7fc00504e005dac901ea0507616e64726f6964f2055c4b71734854394748625876574c6668437950416c52526873626d43676542557562555551317375746d525536634e30524f3751453141486e496474385963784d614c575437636d4851322b7374745279377830663935542b6456593d8806019006019a060134a2060134b2061e40001147550d0c074f530b4d5c584d57416657545a065f2a091d6a0d5033'
        )
        OLD_OPEN_ID = b"996a629dbcdb3964be6b6978f5d814db"
        OLD_ACCESS_TOKEN = b"ff90c07eb9815af30a43b4a9f6019516e0e4c703b44092516d0defa4cef51f2a"
        payload = payload_template.replace(OLD_OPEN_ID, open_id.encode())
        payload = payload.replace(OLD_ACCESS_TOKEN, access_token.encode())
        encrypted_payload = self.encrypt_api(payload.hex())
        if not encrypted_payload:
            return None
        final_payload = bytes.fromhex(encrypted_payload)
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if self.stop_execution:
                    return None
                    
                self.smart_rate_limit_bypass()
                timeout = 12 if self.turbo_mode else 18
                response = self.session.post(
                    url,
                    headers=headers,
                    data=final_payload,
                    verify=False,
                    timeout=timeout
                )
                if response.status_code == 200 and len(response.content) > 0:
                    logging.info(f"✅ MajorLogin successful (Region: {region})")
                    return response.content
                elif response.status_code == 429:
                    logging.warning(f"🚫 Rate limited at MajorLogin")
                    self.advanced_retry_strategy(attempt, max_attempts)
                    continue
                else:
                    logging.warning(f"MajorLogin attempt {attempt + 1} failed with status {response.status_code}")
            except Exception as e:
                logging.warning(f"MajorLogin attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                self.advanced_retry_strategy(attempt, max_attempts)
        return None

    def GET_PAYLOAD_BY_DATA(self, JWT_TOKEN, NEW_ACCESS_TOKEN, region='IND'):
        try:
            token_payload_base64 = JWT_TOKEN.split('.')[1]
            token_payload_base64 += '=' * ((4 - len(token_payload_base64) % 4) % 4)
            decoded_payload = base64.urlsafe_b64decode(token_payload_base64).decode('utf-8')
            decoded_payload = json.loads(decoded_payload)
            NEW_EXTERNAL_ID = decoded_payload['external_id']
            SIGNATURE_MD5 = decoded_payload['signature_md5']
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            payload = bytes.fromhex("1a13323032352d30372d33302031313a30323a3531220966726565206669726528013a07312e3131342e32422c416e64726f6964204f5320372e312e32202f204150492d323320284e32473438482f373030323530323234294a0848616e6468656c645207416e64726f69645a045749464960c00c68840772033332307a1f41524d7637205646507633204e454f4e20564d48207c2032343635207c203480019a1b8a010f416472656e6f2028544d292036343092010d4f70656e474c20455320332e319a012b476f6f676c657c31663361643662372d636562342d343934622d383730622d623164616364373230393131a2010c3139372e312e31322e313335aa0102656eb201203939366136323964626364623339363462653662363937386635643831346462ba010134c2010848616e6468656c64ca011073616d73756e6720534d2d473935354eea014066663930633037656239383135616633306134336234613966363031393531366530653463373033623434303932353136643064656661346365663531663261f00101ca0207416e64726f6964d2020457494649ca03203734323862323533646566633136343031386336303461316562626665626466e003daa907e803899b07f003bf0ff803ae088004999b078804daa9079004999b079804daa907c80403d204262f646174612f6170702f636f6d2e6474732e667265656669726574682d312f6c69622f61726de00401ea044832303837663631633139663537663261663465376665666630623234643964397c2f646174612f6170702f636f6d2e6474732e667265656669726574682d312f626173652e61706bf00403f804018a050233329a050a32303139313138363933a80503b205094f70656e474c455332b805ff7fc00504e005dac901ea0507616e64726f6964f2055c4b71734854394748625876574c6668437950416c52526873626d43676542557562555551317375746d525536634e30524f3751453141486e496474385963784d614c575437636d4851322b7374745279377830663935542b6456593d8806019006019a060134a2060134b2061e40001147550d0c074f530b4d5c584d57416657545a065f2a091d6a0d5033")
            payload = payload.replace(b"2025-07-30 11:02:51", now.encode())
            payload = payload.replace(b"ff90c07eb9815af30a43b4a9f6019516e0e4c703b44092516d0defa4cef51f2a", NEW_ACCESS_TOKEN.encode("UTF-8"))
            payload = payload.replace(b"996a629dbcdb3964be6b6978f5d814db", NEW_EXTERNAL_ID.encode("UTF-8"))
            payload = payload.replace(b"7428b253defc164018c604a1ebbfebdf", SIGNATURE_MD5.encode("UTF-8"))
            PAYLOAD = payload.hex()
            PAYLOAD = self.encrypt_api(PAYLOAD)
            if PAYLOAD:
                return bytes.fromhex(PAYLOAD)
            else:
                return None
        except Exception as e:
            logging.error(f"Error creating GetLoginData payload: {e}")
            return None

    def GET_LOGIN_DATA(self, JWT_TOKEN, PAYLOAD, region='IND'):
        if self.stop_execution:
            return False
            
        region_config = self.regions.get(region, self.regions['IND'])
        url = region_config['get_login_data_url']
        client_host = region_config['client_host']
        headers = {
            'Expect': '100-continue',
            'Authorization': f'Bearer {JWT_TOKEN}',
            'X-Unity-Version': '2018.4.11f1',
            'X-GA': 'v1 1',
            'ReleaseVersion': 'OB53',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)',
            'Host': client_host,
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                if self.stop_execution:
                    return False
                    
                self.smart_rate_limit_bypass()
                timeout = 8 if self.turbo_mode else 12
                response = self.session.post(url, headers=headers, data=PAYLOAD, verify=False, timeout=timeout)
                if response.status_code == 200:
                    logging.info(f"✅ GetLoginData successful - Account activated! (Region: {region})")
                    return True
                elif response.status_code == 401:
                    logging.error(f"❌ GetLoginData failed: 401 Unauthorized (Region: {region})")
                    with self.stats_lock:
                        self.unauthorized_count += 1
                        if self.unauthorized_count >= self.max_unauthorized_before_stop:
                            print(f"\n🚨 CRITICAL: Too many 401 Unauthorized errors!")
                            print("💡 Possible reasons:")
                            print("   - Wrong region selected")
                            print("   - Server maintenance")
                            print("   - IP blocked")
                            print("   - Invalid credentials format")
                            self.stop_execution = True
                    return False
                elif response.status_code == 404:
                    logging.error(f"❌ GetLoginData failed: 404 Not Found - Invalid region URL for {region}")
                    return False
                else:
                    logging.warning(f"GetLoginData attempt {attempt + 1} failed with status {response.status_code} (Region: {region})")
            except Exception as e:
                logging.warning(f"GetLoginData attempt {attempt + 1} failed: {e} (Region: {region})")
            if attempt < max_attempts - 1:
                self.advanced_retry_strategy(attempt, max_attempts)
        return False
#sajeeb
    def detect_region_from_account(self, account_data):
        region = account_data.get('region', 'IND')
        if region not in self.regions:
            return None
        return region

    def activate_single_account(self, account_data):
        if self.stop_execution:
            return False
            
        uid = account_data['uid']
        password = account_data['password']
        name = account_data.get('name', 'N/A')
        account_id = account_data.get('account_id', 'N/A')
        region = self.selected_region
        
        if not region:
            detected_region = self.detect_region_from_account(account_data)
            if not detected_region:
                with self.stats_lock:
                    self.failed += 1
                    failed_data = {
                        'uid': uid,
                        'password': password,
                        'account_id': account_id,
                        'name': name,
                        'region': 'UNKNOWN',
                        'error': 'Invalid region in account data'
                    }
                    self.failed_accounts.append(failed_data)
                return False
            region = detected_region
            
        thread_id = threading.current_thread().name
        logging.info(f"🧵 {thread_id} - Starting: {name} (UID: {uid}, Region: {region})")
        
        access_token, open_id = self.guest_token(uid, password, region)
        if not access_token or not open_id:
            with self.stats_lock:
                self.failed += 1
                failed_data = {
                    'uid': uid,
                    'password': password,
                    'account_id': account_id,
                    'name': name,
                    'region': region,
                    'error': 'Guest token failed'
                }
                self.failed_accounts.append(failed_data)
            return False
        
        major_login_response = self.major_login(access_token, open_id, region)
        if not major_login_response:
            with self.stats_lock:
                self.failed += 1
                failed_data = {
                    'uid': uid,
                    'password': password,
                    'account_id': account_id,
                    'name': name,
                    'region': region,
                    'error': 'MajorLogin failed'
                }
                self.failed_accounts.append(failed_data)
            return False
 #sb       
        jwt_token, key, iv = self.parse_my_message(major_login_response)
        if not jwt_token:
            with self.stats_lock:
                self.failed += 1
                failed_data = {
                    'uid': uid,
                    'password': password,
                    'account_id': account_id,
                    'name': name,
                    'region': region,
                    'error': 'JWT extraction failed'
                }
                self.failed_accounts.append(failed_data)
            return False
        
        payload = self.GET_PAYLOAD_BY_DATA(jwt_token, access_token, region)
        if not payload:
            with self.stats_lock:
                self.failed += 1
                failed_data = {
                    'uid': uid,
                    'password': password,
                    'account_id': account_id,
                    'name': name,
                    'region': region,
                    'error': 'Payload creation failed'
                }
                self.failed_accounts.append(failed_data)
            return False
        
        activation_success = self.GET_LOGIN_DATA(jwt_token, payload, region)
        if activation_success:
            logging.info(f"🎉 {thread_id} - SUCCESS: {name} activated in {region}!")
            with self.stats_lock:
                self.successful += 1
                success_data = {
                    'uid': uid,
                    'password': password,
                    'account_id': account_id,
                    'name': name,
                    'region': region,
                    'status': 'activated'
                }
                self.successful_accounts.append(success_data)
            return True
        else:
            with self.stats_lock:
                self.failed += 1
                failed_data = {
                    'uid': uid,
                    'password': password,
                    'account_id': account_id,
                    'name': name,
                    'region': region,
                    'error': 'GetLoginData failed'
                }
                self.failed_accounts.append(failed_data)
            return False

    def save_results(self):
        try:
            region_name = self.selected_region if self.selected_region else 'MULTI'
            success_file = f'success-{region_name}.json'
            failed_file = f'failed-{region_name}.json'
            
            with open(success_file, 'w', encoding='utf-8') as f:
                json.dump(self.successful_accounts, f, indent=2, ensure_ascii=False)
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_accounts, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved: {success_file} ({len(self.successful_accounts)}), {failed_file} ({len(self.failed_accounts)})")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

    def detect_file_format(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return 'json_array'
                elif isinstance(data, dict):
                    return 'json_object'
            except:
                pass
            lines = content.split('\n')
            if len(lines) > 0:
                first_line = lines[0].strip()
                if ':' in first_line or ' ' in first_line:
                    return 'line_format'
            return 'unknown'
        except Exception as e:
            return 'unknown'

    def parse_accounts_from_file(self, filepath, file_format):
        accounts = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if file_format == 'json_array':
                data = json.loads(content)
                for account in data:
                    if self.extract_uid_password(account):
                        accounts.append(self.extract_uid_password(account))
            elif file_format == 'json_object':
                data = json.loads(content)
                for key, value in data.items():
                    account_data = self.extract_uid_password_from_couple(key, value)
                    if account_data:
                        accounts.append(account_data)
            elif file_format == 'line_format':
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    account_data = self.extract_uid_password_from_line(line)
                    if account_data:
                        accounts.append(account_data)
            print(f"📁 Parsed {len(accounts)} accounts from {filepath} ({file_format})")
            return accounts
        except Exception as e:
            print(f"❌ Error parsing file {filepath}: {e}")
            return []

    def extract_uid_password(self, data):
        if isinstance(data, dict):
            uid = data.get('uid') or data.get('user') or data.get('username') or data.get('email')
            password = data.get('password') or data.get('pass') or data.get('pwd')
            if uid and password:
                return {
                    'uid': str(uid),
                    'password': str(password),
                    'name': data.get('name', 'Unknown'),
                    'account_id': data.get('account_id', 'N/A'),
                    'region': data.get('region', 'IND')
                }
        return None

    def extract_uid_password_from_couple(self, key, value):
        if isinstance(value, dict):
            uid = value.get('uid')
            password = value.get('password')
            if uid and password:
                return {
                    'uid': str(uid),
                    'password': str(password),
                    'name': value.get('name', 'Unknown'),
                    'account_id': value.get('account_id', 'N/A'),
                    'region': value.get('region', 'IND')
                }
        elif isinstance(value, str):
            if key.isdigit() and len(key) >= 4:
                return {
                    'uid': key,
                    'password': value,
                    'name': 'Unknown',
                    'account_id': 'N/A',
                    'region': 'IND'
                }
        return None
#sajeeb ahamed
    def extract_uid_password_from_line(self, line):
        separators = [':', ' ', '|', '\t', ';']
        for sep in separators:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    uid = parts[0].strip()
                    password = parts[1].strip()
                    if uid and password and (uid.isdigit() and len(uid) >= 4):
                        return {
                            'uid': uid,
                            'password': password,
                            'name': 'Unknown',
                            'account_id': 'N/A',
                            'region': 'IND'
                        }
        return None

    def check_region_in_file(self, accounts):
        has_valid_region = False
        has_any_region = False
        invalid_regions = set()
        
        for account in accounts:
            region = account.get('region')
            if region:
                has_any_region = True
                if region in self.regions:
                    has_valid_region = True
                else:
                    invalid_regions.add(region)
        
        return has_valid_region, has_any_region, invalid_regions

    def select_region_menu(self):
        print(f"\n🌍 REGION SELECTION MENU")
        print(f"{'='*50}")
        regions_list = list(self.regions.keys())
        print("\nAvailable Regions:")
        for i, region in enumerate(regions_list, 1):
            region_info = self.regions[region]
            server = region_info['client_host']
            print(f"{i:2d}. {region:4} - Server: {server}")
        print(f"{'='*50}")
        print("💡 Tips:")
        print("   - IND: India")
        print("   - BD: Bangladesh")
        print("   - PK: Pakistan") 
        print("   - ID: Indonesia")
        print("   - TH: Thailand")
        print("   - VN: Vietnam")
        print("   - BR: Brazil")
        print("   - Choose region closest to your accounts' location")
        print(f"{'='*50}")
        while True:
            try:
                choice = input(f"\n🎯 Select region (1-{len(regions_list)}): ").strip()
                if not choice:
                    continue
                region_index = int(choice) - 1
                if 0 <= region_index < len(regions_list):
                    selected_region = regions_list[region_index]
                    print(f"✅ Selected region: {selected_region}")
                    return selected_region
                else:
                    print(f"❌ Please enter a number between 1 and {len(regions_list)}")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                sys.exit(0)

    def scan_account_files(self):
        account_files = []
        all_files = glob.glob('*')
        for filepath in all_files:
            if filepath.endswith(('.txt', '.json')):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    accounts_count = self.count_accounts_in_content(content, filepath)
                    if accounts_count > 0:
                        account_files.append({
                            'path': filepath,
                            'accounts': accounts_count,
                            'format': self.detect_file_format(filepath)
                        })
                except:
                    continue
        return account_files

    def count_accounts_in_content(self, content, filepath):
        try:
            accounts = []
            if filepath.endswith('.json'):
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        if self.extract_uid_password(item):
                            accounts.append(item)
                elif isinstance(data, dict):
                    for key, value in data.items():
                        account_data = self.extract_uid_password_from_couple(key, value)
                        if account_data:
                            accounts.append(account_data)
            else:
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        account_data = self.extract_uid_password_from_line(line)
                        if account_data:
                            accounts.append(account_data)
            return len(accounts)
        except:
            return 0

    def select_input_file(self):
        account_files = self.scan_account_files()
        if not account_files:
            print("❌ No account files found in current directory!")
            return None, None, None
        print(f"\n📂 AVAILABLE ACCOUNT FILES:")
        print(f"{'='*50}")
        for i, file_info in enumerate(account_files, 1):
            print(f"{i}. {file_info['path']} ({file_info['format']}) - {file_info['accounts']} accounts")
        print(f"{'='*50}")
        while True:
            try:
                choice = input(f"\n🎯 Select file (1-{len(account_files)}): ").strip()
                if not choice:
                    continue
                file_index = int(choice) - 1
                if 0 <= file_index < len(account_files):
                    selected_file = account_files[file_index]['path']
                    file_format = account_files[file_index]['format']
                    print(f"✅ Selected: {selected_file}")
                    accounts = self.parse_accounts_from_file(selected_file, file_format)
                    if not accounts:
                        print("❌ No valid accounts found in the selected file!")
                        return None, None, None
                    
                    has_valid_region, has_any_region, invalid_regions = self.check_region_in_file(accounts)
                    
                    if not has_valid_region:
                        if has_any_region:
                            print(f"\n⚠️  File contains invalid regions: {', '.join(invalid_regions)}")
                        else:
                            print(f"\nℹ️  No valid region found in account file")
                        
                        print("🔧 Please select a region to use for all accounts:")
                        selected_region = self.select_region_menu()
                    else:
                        use_file_regions = input("\n🤔 Use regions from file? (y/N): ").strip().lower()
                        if use_file_regions in ['y', 'yes']:
                            selected_region = None
                            print("✅ Using regions from file")
                        else:
                            selected_region = self.select_region_menu()
                    
                    self.selected_region = selected_region
                    if selected_region:
                        for account in accounts:
                            account['region'] = selected_region
                        print(f"✅ Applied '{selected_region}' region to all accounts")
                    
                    return selected_file, file_format, accounts
                else:
                    print(f"❌ Please enter a number between 1 and {len(account_files)}")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                return None, None, None

    def process_all_accounts_parallel(self, accounts):
        total_accounts = len(accounts)
        print(f"🚀 Starting Multi-Region Activation for {total_accounts} accounts...")
        print(f"🔧 Workers: {self.max_workers}, Turbo Mode: {self.turbo_mode}")
        if self.selected_region:
            print(f"🌍 Selected Region: {self.selected_region}")
        else:
            print(f"🌍 Using regions from file")
        print(f"{'='*60}")
        
        self.stop_execution = False
        self.unauthorized_count = 0
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="MultiRegion") as executor:
            future_to_account = {
                executor.submit(self.activate_single_account, account): account 
                for account in accounts
            }
            completed = 0
            for future in as_completed(future_to_account):
                if self.stop_execution:
                    print(f"\n🛑 Stopping execution due to too many 401 errors!")
                    executor.shutdown(wait=False)
                    break
                    
                account = future_to_account[future]
                try:
                    result = future.result()
                    completed += 1
                    progress = (completed / total_accounts) * 100
                    speed = completed / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
                    print(f"📊 Progress: {completed}/{total_accounts} ({progress:.1f}%) - Speed: {speed:.2f} acc/s - ✅: {self.successful} ❌: {self.failed}")
                except Exception as e:
                    logging.error(f"❌ Thread error: {e}")
                    completed += 1
                    with self.stats_lock:
                        self.failed += 1
                        failed_data = {
                            'uid': account.get('uid', 'N/A'),
                            'password': account.get('password', 'N/A'),
                            'account_id': account.get('account_id', 'N/A'),
                            'name': account.get('name', 'N/A'),
                            'region': account.get('region', 'N/A'),
                            'error': str(e)
                        }
                        self.failed_accounts.append(failed_data)
        
        total_time = time.time() - start_time
        
        if self.stop_execution:
            print(f"\n🚨 EXECUTION STOPPED EARLY!")
            print(f"💡 Reason: Too many 401 Unauthorized errors detected")
            print(f"🔧 Solution: Try selecting a different region or check your credentials")
        
        self.save_results()
        return self.successful, self.failed, self.failed_accounts, total_time

def main():
    MAX_WORKERS = 8
    TURBO_MODE = True
    activator = MultiRegionActivator(
        max_workers=MAX_WORKERS,
        turbo_mode=TURBO_MODE
    )
    selected_file, file_format, accounts = activator.select_input_file()
    if not selected_file or not accounts:
        return
    print(f"🎯 Starting Multi-Region Activation for {len(accounts)} accounts...")
    successful, failed, failed_accounts, total_time = activator.process_all_accounts_parallel(accounts)
    
    print(f"\n{'='*70}")
    print("🎯 MULTI-REGION ACTIVATION COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(accounts)}")
    if accounts:
        success_rate = (successful/len(accounts))*100 if successful > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")
    else:
        print("🎯 Success Rate: 0%")
    print(f"⏰ Total Time: {total_time:.2f} seconds")
    if total_time > 0:
        print(f"⚡ Accounts per second: {len(accounts)/total_time:.2f}")
        print(f"🚀 Accounts per minute: {(len(accounts)/total_time)*60:.1f}")
    else:
        print(f"⚡ Accounts per second: N/A")
        print(f"🚀 Accounts per minute: N/A")
    
    region_name = activator.selected_region if activator.selected_region else 'MULTI'
    print(f"💾 Results saved to: success-{region_name}.json, failed-{region_name}.json")
    
    if activator.stop_execution:
        print(f"\n⚠️  NOTE: Execution was stopped early due to 401 errors!")
        print(f"💡 Try selecting a different region or check your account credentials")
    
    print(f"{'='*70}")

if __name__ == "__main__":
    main()