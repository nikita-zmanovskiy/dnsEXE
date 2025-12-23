
import eel

import subprocess

import ctypes

import sys

import re



# Конфигурация провайдеров (берем первые адреса для теста скорости)

DNS_PROVIDERS = {
    "my_dns": {
        "ipv4": ["176.99.11.77", "80.78.247.254"],
        "ipv6": ["2001:4860:4860::8888", "2001:4860:4860::8844"]
    },
    "google": {
        "ipv4": ["8.8.8.8", "8.8.4.4"],
        "ipv6": ["2001:4860:4860::8888", "2001:4860:4860::8844"]
    },
    "cloudflare": {
        "ipv4": ["1.1.1.1", "1.0.0.1"],
        "ipv6": ["2606:4700:4700::1111", "2606:4700:4700::1001"]
    },
    "adguard": {
        "ipv4": ["94.140.14.14", "94.140.15.15"],
        "ipv6": ["2a10:50c0::ad1:ff", "2a10:50c0::ad2:ff"]
    }
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
    try:
        for name, data in DNS_PROVIDERS.items():
            # Теперь берем первый IPv4 адрес из вложенного словаря
            ip_to_ping = data["ipv4"][0] 
            p = get_ping(ip_to_ping)
            results[name] = p
        
        # Находим провайдера с минимальным пингом
        best_provider = min(results, key=results.get)
        
        if results[best_provider] == 999:
            return {"error": "All providers timed out"}
        
        return {"best": best_provider, "ping": results[best_provider]}
    except Exception as e:
        print(f"Ошибка в auto_select: {e}")
        return {"error": str(e)}

@eel.expose
def py_set_dns(provider_id):
    # Достаем данные по ключу (например, "google")
    data = DNS_PROVIDERS.get(provider_id)
    v4 = data["ipv4"]
    v6 = data["ipv6"]
    
    try:
        # Ставим IPv4
        subprocess.run(f'netsh interface ip set dns name="{INTERFACE}" static {v4[0]}', shell=True, check=True)
        subprocess.run(f'netsh interface ip add dns name="{INTERFACE}" {v4[1]} index=2', shell=True, check=True)
        
        # Ставим IPv6
        subprocess.run(f'netsh interface ipv6 set dns name="{INTERFACE}" static {v6[0]}', shell=True, check=True)
        subprocess.run(f'netsh interface ipv6 add dns name="{INTERFACE}" {v6[1]} index=2', shell=True, check=True)
        
        # СБРОС КЭША
        subprocess.run('ipconfig /flushdns', shell=True, check=True)
        
        return f"✅ {provider_id.upper()} применен (v4/v6 + Flush)"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

@eel.expose
def py_reset_dns():
    try:
        # Возвращаем DHCP для обоих протоколов
        subprocess.run(f'netsh interface ip set dns name="{INTERFACE}" source=dhcp', shell=True, check=True)
        subprocess.run(f'netsh interface ipv6 set dns name="{INTERFACE}" source=dhcp', shell=True, check=True)
        subprocess.run('ipconfig /flushdns', shell=True, check=True)
        return "✅ DNS сброшен в авто (DHCP)"
    except:
        return "❌ Ошибка сброса"



if __name__ == "__main__":

    if not ctypes.windll.shell32.IsUserAnAdmin():

        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

        sys.exit()



    eel.init('web')

    # Отключаем скролл и фиксируем размер

    eel.start('index.html', mode='edge', size=(450, 720))



