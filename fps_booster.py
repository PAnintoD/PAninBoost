import os
import sys
import ctypes
import time
import subprocess
import threading
import psutil
import winreg

class AdminPrivilegeHandler:
    @staticmethod
    def ensure_admin():
        if ctypes.windll.shell32.IsUserAnAdmin() == 0:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()

class SystemOptimizer:
    def __init__(self):
        self.paused_services = []
        self.blacklist = [
            "chrome.exe", "msedge.exe", "discord.exe", "spotify.exe",
            "steamwebhelper.exe", "slack.exe", "teams.exe", "onedrive.exe"
        ]
        self.services_to_pause = ["SysMain", "BITS"]

    def terminate_background_apps(self):
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and proc.info['name'].lower() in self.blacklist:
                    proc.kill()
            except Exception:
                pass

    def clear_memory_cache(self):
        try:
            ctypes.windll.kernel32.SetSystemFileCacheSize(ctypes.c_size_t(-1), ctypes.c_size_t(-1), 0)
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() not in ["system", "smss.exe", "csrss.exe"]:
                        handle = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0100, False, proc.info['pid'])
                        if handle:
                            ctypes.windll.psapi.EmptyWorkingSet(handle)
                            ctypes.windll.kernel32.CloseHandle(handle)
                except Exception:
                    pass
        except Exception:
            pass

    def suspend_services(self):
        for svc in self.services_to_pause:
            try:
                res = subprocess.run(["sc", "query", svc], capture_output=True, text=True)
                if "RUNNING" in res.stdout:
                    subprocess.run(["sc", "stop", svc], capture_output=True)
                    self.paused_services.append(svc)
            except Exception:
                pass

    def flush_dns(self):
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
        except Exception:
            pass

    def revert(self):
        for svc in self.paused_services:
            try:
                subprocess.run(["sc", "start", svc], capture_output=True)
            except Exception:
                pass
        self.paused_services.clear()

class HardwareOptimizer:
    def __init__(self):
        self.original_power_plan = None
        self.game_pids = []

    def set_power_plan(self, plan_guid="e9a42b02-d5df-448d-aa00-03f14749eb61"):
        try:
            out = subprocess.check_output(["powercfg", "/getactivescheme"], text=True)
            if "GUID:" in out:
                self.original_power_plan = out.split()[3]
            subprocess.run(["powercfg", "-duplicatescheme", plan_guid], capture_output=True)
            subprocess.run(["powercfg", "/setactive", plan_guid], capture_output=True)
        except Exception:
            pass

    def trigger_msi_afterburner(self, profile):
        path = r"C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe"
        if os.path.exists(path):
            try:
                subprocess.Popen([path, f"-Profile{profile}"])
            except Exception:
                pass

    def optimize_cpu(self, game_name):
        cores = os.cpu_count() or 4
        game_cores = list(range(max(1, cores - 2)))
        bg_cores = list(range(max(1, cores - 2), cores))

        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == game_name.lower():
                    p = psutil.Process(proc.info['pid'])
                    p.nice(psutil.HIGH_PRIORITY_CLASS)
                    p.cpu_affinity(game_cores)
                    if p.pid not in self.game_pids:
                        self.game_pids.append(p.pid)
                elif proc.info['name'] and proc.info['name'].lower() not in ["system", "idle", "registry", "smss.exe"]:
                    p = psutil.Process(proc.info['pid'])
                    p.cpu_affinity(bg_cores)
            except Exception:
                pass

    def revert(self):
        if self.original_power_plan:
            try:
                subprocess.run(["powercfg", "/setactive", self.original_power_plan], capture_output=True)
            except Exception:
                pass
        self.trigger_msi_afterburner(2)
        
        cores = list(range(os.cpu_count() or 4))
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                p = psutil.Process(proc.info['pid'])
                p.cpu_affinity(cores)
                if p.pid in self.game_pids:
                    p.nice(psutil.NORMAL_PRIORITY_CLASS)
            except Exception:
                pass
        self.game_pids.clear()

class NetworkAndLatencyManager:
    def __init__(self):
        self.modified_interfaces = []
        try:
            self.ntdll = ctypes.WinDLL('ntdll.dll')
            self.ntdll.NtSetTimerResolution.argtypes = [ctypes.c_ulong, ctypes.c_byte, ctypes.POINTER(ctypes.c_ulong)]
        except Exception:
            self.ntdll = None

    def set_timer_resolution(self, res_100ns):
        if not self.ntdll:
            return
        try:
            current_res = ctypes.c_ulong()
            self.ntdll.NtSetTimerResolution(res_100ns, True, ctypes.byref(current_res))
        except Exception:
            pass

    def set_tcp_no_delay(self):
        base_key = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key) as interfaces_key:
                for i in range(winreg.QueryInfoKey(interfaces_key)[0]):
                    interface_name = winreg.EnumKey(interfaces_key, i)
                    interface_path = f"{base_key}\\{interface_name}"
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, interface_path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as iface_key:
                            ip_addr = None
                            try:
                                ip_addr = winreg.QueryValueEx(iface_key, "DhcpIPAddress")[0]
                            except Exception:
                                try:
                                    ip_addr = winreg.QueryValueEx(iface_key, "IPAddress")[0]
                                except Exception:
                                    pass
                            
                            valid_ip = False
                            if isinstance(ip_addr, str) and ip_addr != "0.0.0.0":
                                valid_ip = True
                            elif isinstance(ip_addr, list) and len(ip_addr) > 0 and ip_addr[0] != "0.0.0.0":
                                valid_ip = True

                            if valid_ip:
                                winreg.SetValueEx(iface_key, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                                winreg.SetValueEx(iface_key, "TCPNoDelay", 0, winreg.REG_DWORD, 1)
                                self.modified_interfaces.append(interface_path)
                    except Exception:
                        pass
        except Exception:
            pass

    def revert(self):
        if self.ntdll:
            try:
                current_res = ctypes.c_ulong()
                self.ntdll.NtSetTimerResolution(156250, True, ctypes.byref(current_res))
            except Exception:
                pass

        for path in self.modified_interfaces:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE) as key:
                    try:
                        winreg.DeleteValue(key, "TcpAckFrequency")
                    except Exception:
                        pass
                    try:
                        winreg.DeleteValue(key, "TCPNoDelay")
                    except Exception:
                        pass
            except Exception:
                pass
        self.modified_interfaces.clear()

class AutoTriggerDaemon:
    def __init__(self, target_game):
        self.target_game = target_game
        self.sys_opt = SystemOptimizer()
        self.hw_opt = HardwareOptimizer()
        self.net_opt = NetworkAndLatencyManager()
        self.is_boosted = False

    def is_game_running(self):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == self.target_game.lower():
                    return True
            except Exception:
                pass
        return False

    def boost(self):
        if not self.is_boosted:
            self.sys_opt.terminate_background_apps()
            self.sys_opt.suspend_services()
            self.sys_opt.clear_memory_cache()
            self.sys_opt.flush_dns()
            self.hw_opt.set_power_plan()
            self.hw_opt.trigger_msi_afterburner(1)
            self.net_opt.set_timer_resolution(5000)
            self.net_opt.set_tcp_no_delay()
            self.is_boosted = True

    def update_cpu_affinity(self):
        if self.is_boosted:
            self.hw_opt.optimize_cpu(self.target_game)

    def revert(self):
        if self.is_boosted:
            self.sys_opt.revert()
            self.hw_opt.revert()
            self.net_opt.revert()
            self.is_boosted = False

    def run(self):
        while True:
            running = self.is_game_running()
            if running:
                if not self.is_boosted:
                    self.boost()
                self.update_cpu_affinity()
            else:
                if self.is_boosted:
                    self.revert()
            time.sleep(5)

if __name__ == "__main__":
    AdminPrivilegeHandler.ensure_admin()
    game_exe = sys.argv[1] if len(sys.argv) > 1 else "valorant.exe"
    daemon = AutoTriggerDaemon(game_exe)
    daemon.run()
