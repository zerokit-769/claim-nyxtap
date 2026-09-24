import sys
import os
import time
import urllib.parse
import asyncio
from telethon import TelegramClient, functions, types
from telethon.errors import RPCError


API_ID = 35898257
API_HASH = 'fb06985ea797ac51aaa1e6d1168ceaaa'
COMMON_SHORT_NAMES = ['app', 'play', 'start', 'game', 'farm', 'mine', 'tap', 'coin', 'bot']


class Col:
    R = '\033[0m'
    B = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GRN = '\033[92m'
    WHT = '\033[97m'
    NEON_G = '\033[38;5;46m'
    NEON_C = '\033[38;5;51m'
    NEON_Y = '\033[38;5;226m'
    DIM_C = '\033[38;5;244m'

def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def render_banner():
    clear_screen()
    print(f"{Col.NEON_C}╔══════════════════════════════════════════════════════╗{Col.R}")
    print(f"{Col.NEON_C}║{Col.R}               {Col.B}{Col.NEON_G}ZeinthHub Project v1{Col.R}                   {Col.NEON_C}║{Col.R}")
    print(f"{Col.NEON_C}║{Col.R}         {Col.DIM_C}Advanced Init Data Extractor CLI{Col.R}             {Col.NEON_C}║{Col.R}")
    print(f"{Col.NEON_C}╚══════════════════════════════════════════════════════╝{Col.R}")
    print()

async def async_spinner(coro, text="Loading"):

    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    task = asyncio.create_task(coro)
    i = 0
    while not task.done():
        sys.stdout.write(f"\r {Col.NEON_C}[{spinner_chars[i]}]{Col.R} {Col.WHT}{text}...{Col.R}")
        sys.stdout.flush()
        i = (i + 1) % len(spinner_chars)
        await asyncio.sleep(0.1)
    
    
    sys.stdout.write(f"\r{' ' * (len(text) + 15)}\r")
    sys.stdout.flush()
    return await task

def print_sys(msg, status="info"):
    icons = {
        "info": f"{Col.NEON_C}[*]{Col.R}",
        "ok": f"{Col.NEON_G}[✓]{Col.R}",
        "err": f"{Col.RED}[✗]{Col.R}",
        "warn": f"{Col.NEON_Y}[!]{Col.R}"
    }
    print(f" {icons.get(status, icons['info'])} {msg}")

async def generate_init_data():
    render_banner()
    print_sys("Tunggu sebentar...", "info")
    time.sleep(0.5)
    
    client = TelegramClient('session_generator', API_ID, API_HASH)

    def get_phone(): return input(f" {Col.NEON_C}➜{Col.R} {Col.WHT}Nomor HP (+62...): {Col.R}").strip()
    def get_code(): return input(f" {Col.NEON_C}➜{Col.R} {Col.WHT}Kode OTP Telegram: {Col.R}").strip()
    def get_password(): return input(f" {Col.NEON_C}➜{Col.R} {Col.WHT}Password 2FA (jika ada): {Col.R}").strip()

    await client.start(phone=get_phone, code_callback=get_code, password=get_password)
    print_sys(f"{Col.NEON_G}Sesi terautentikasi dan diamankan.{Col.R}\n", "ok")

    while True:
        print(f"{Col.DIM_C}────────────────────────────────────────────────────────{Col.R}")
        user_input = input(f" {Col.NEON_Y}Input Target{Col.R} {Col.DIM_C}(@bot/exit) ➜{Col.R} {Col.WHT}").strip()

        if user_input.lower() in ['exit', 'keluar', 'quit']:
            print_sys("Memutus koneksi...", "info")
            break
        if not user_input:
            continue

        bot_username = user_input.replace('https://', '').replace('http://', '').replace('t.me/', '').replace('@', '').split('/')[0]
        
        try:
            print()
            bot = await async_spinner(
                client.get_input_entity(bot_username), 
                f"Menghubungi server @{bot_username}"
            )
            print_sys(f"Terhubung dengan target: {Col.B}@{bot_username}{Col.R}", "ok")
            
          
            try:
                await client.send_message(bot, '/start')
            except Exception:
                pass 

            success = False
            
            for s_name in COMMON_SHORT_NAMES:
                try:
                    
                    async def fetch_app():
                        return await client(functions.messages.RequestAppWebViewRequest(
                            peer=bot,
                            app=types.InputBotAppShortName(bot_id=bot, short_name=s_name),
                            platform='android',
                            write_allowed=True,
                            start_param='' 
                        ))
                        
                    res_app = await async_spinner(
                        fetch_app(), 
                        f"Bypass keamanan (short_name: {s_name})"
                    )
                    
                    if res_app and hasattr(res_app, 'url'):
                        parsed = urllib.parse.urlparse(res_app.url)
                        params = urllib.parse.parse_qs(parsed.fragment or parsed.query)
                        init_data = params.get('tgWebAppData', [None])[0]
                        
                        print_sys(f"Akses diberikan! Endpoint: {Col.NEON_G}{s_name}{Col.R}", "ok")
                        
                        
                        print(f"\n{Col.NEON_C}┌─ {Col.B}INIT DATA PAYLOAD{Col.R} {Col.NEON_C}──────────────────────────────────┐{Col.R}")
                        print(f"{Col.NEON_G}{init_data}{Col.R}")
                        print(f"{Col.NEON_C}└────────────────────────────────────────────────────┘{Col.R}\n")
                        
                        success = True
                        break
                        
                except RPCError as e:
                    if "BOT_APP_INVALID" in str(e):
                        continue
                    else:
                        print_sys(f"Ditolak saat mencoba '{s_name}': {e}", "err")
                        break
            
            if not success:
                print_sys(f"Gagal menembus @{bot_username}. Nama aplikasi terlalu unik.", "warn")
                print_sys("Gunakan link manual (t.me/namabot/namaaplikasi).", "info")

        except Exception as e:
            print_sys(f"Target tidak valid atau error jaringan: {e}", "err")

    await client.disconnect()

if __name__ == '__main__':
    
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
            
    try:
        asyncio.run(generate_init_data())
    except KeyboardInterrupt:
        print(f"\n\n{Col.NEON_C}[*]{Col.R} Dihentikan secara paksa oleh pengguna.")
