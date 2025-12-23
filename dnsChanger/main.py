
import eel

import subprocess

import ctypes

import sys

import re



# Конфигурация провайдеров (берем первые адреса для теста скорости)

DNS_PROVIDERS = {

    "my_dns": ["176.99.11.77", "80.78.247.254"],

    "google": ["8.8.8.8", "8.8.4.4"],

    "cloudflare": ["1.1.1.1", "1.0.0.1"],

    "adguard": ["94.140.14.14", "94.140.15.15"]

}



def get_wifi_interface():

    try:

        output = subprocess.check_output('netsh interface show interface', encoding='cp866')

        for line in output.split('\n'):

            if ("Беспроводная" in line or "Wi-Fi" in line) and ("Connected" in line or "Связное" in line):

                return line.split('   ')[-1].strip()

        return "Wi-Fi"

    except: return "Wi-Fi"



INTERFACE = get_wifi_interface()



@eel.expose

def get_ping(ip="8.8.8.8"):

    try:

        # Уменьшаем время ожидания для быстрого теста

        output = subprocess.check_output(f"ping -n 1 -w 500 {ip}", shell=True, encoding='cp866')

        match = re.search(r"=\s*(\.?)(\d+)\s*ms", output) or re.search(r"=\s*(\d+)мс", output)

        if match:

            return int(match.group(2))

        return 999

    except: return 999



@eel.expose

def auto_select_best():

    results = {}

    for name, ips in DNS_PROVIDERS.items():

        p = get_ping(ips[0])

        results[name] = p

    

    # Находим провайдера с минимальным пингом

    best_provider = min(results, key=results.get)

    if results[best_provider] == 999:

        return {"error": "All providers timed out"}

    

    return {"best": best_provider, "ping": results[best_provider]}



@eel.expose

def py_set_dns(provider_id):

    servers = DNS_PROVIDERS.get(provider_id)

    try:

        subprocess.run(f'netsh interface ip set dns name="{INTERFACE}" static {servers[0]}', shell=True, check=True)

        subprocess.run(f'netsh interface ip add dns name="{INTERFACE}" {servers[1]} index=2', shell=True, check=True)

        return f"✅ {provider_id.upper()} Applied"

    except: return "❌ Admin error"



@eel.expose

def py_reset_dns():

    try:

        subprocess.run(f'netsh interface ip set dns name="{INTERFACE}" source=dhcp', shell=True, check=True)

        return "✅ DHCP Enabled"

    except: return "❌ Reset Failed"



if __name__ == "__main__":

    if not ctypes.windll.shell32.IsUserAnAdmin():

        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

        sys.exit()



    eel.init('web')

    # Отключаем скролл и фиксируем размер

    eel.start('index.html', mode='edge', size=(450, 720))



