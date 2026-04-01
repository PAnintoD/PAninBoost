import os
import sys
import ctypes
import time
import subprocess
import threading
import psutil
import winreg
import customtkinter as ctk

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
        self.currently_boosted_pid = None

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

    def optimize_cpu_dynamic(self, active_pid):
        try:
            if self.currently_boosted_pid and self.currently_boosted_pid != active_pid:
                try:
                    old_p = psutil.Process(self.currently_boosted_pid)
                    old_p.nice(psutil.NORMAL_PRIORITY_CLASS)
                except Exception:
                    pass
            if active_pid:
                new_p = psutil.Process(active_pid)
                new_p.nice(psutil.HIGH_PRIORITY_CLASS)
                self.currently_boosted_pid = active_pid
        except Exception:
            pass

    def revert(self):
        if self.original_power_plan:
            try:
                subprocess.run(["powercfg", "/setactive", self.original_power_plan], capture_output=True)
            except Exception:
                pass
        self.trigger_msi_afterburner(2)
        if self.currently_boosted_pid:
            try:
                p = psutil.Process(self.currently_boosted_pid)
                p.nice(psutil.NORMAL_PRIORITY_CLASS)
            except Exception:
                pass
        self.currently_boosted_pid = None

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

class DynamicForegroundTracker:
    def __init__(self, log_callback=lambda x: None):
        self.sys_opt = SystemOptimizer()
        self.hw_opt = HardwareOptimizer()
        self.net_opt = NetworkAndLatencyManager()
        self.is_boosted = False
        self.log = log_callback
        self.stop_event = threading.Event()
        self.active_process_name = "None"

    def get_foreground_process(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if hwnd:
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                return pid.value
        except Exception:
            pass
        return None

    def toggle_boost(self):
        if not self.is_boosted:
            self.log("Activating Global System Options...")
            self.sys_opt.terminate_background_apps()
            self.sys_opt.suspend_services()
            self.sys_opt.clear_memory_cache()
            self.sys_opt.flush_dns()
            self.log("Applying Hardware Modifications globally...")
            self.hw_opt.set_power_plan()
            self.hw_opt.trigger_msi_afterburner(1)
            self.log("Applying Network OS Low-Latency parameters...")
            self.net_opt.set_timer_resolution(5000)
            self.net_opt.set_tcp_no_delay()
            self.log("GLOBAL BOOST ACTIVE")
            self.is_boosted = True
        else:
            self.log("Deactivating Global Booster...")
            self.sys_opt.revert()
            self.hw_opt.revert()
            self.net_opt.revert()
            self.is_boosted = False
            self.active_process_name = "None"
            self.log("System Restored")

    def run_loop(self):
        while not self.stop_event.is_set():
            if self.is_boosted:
                active_pid = self.get_foreground_process()
                if active_pid:
                    try:
                        p = psutil.Process(active_pid)
                        name = p.name()
                        if name.lower() not in ["system", "idle", "ui", "explorer.exe", "searchapp.exe"]:
                            if self.hw_opt.currently_boosted_pid != active_pid:
                                self.hw_opt.optimize_cpu_dynamic(active_pid)
                                self.log(f"Dynamic Boost Attached -> {name} (PID: {active_pid})")
                                self.active_process_name = name
                    except Exception:
                        pass
            time.sleep(1.5)

class BoosterGUI(ctk.CTk):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.title("Global Dynamic FPS Booster")
        self.geometry("800x550")
        self.resizable(False, False)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="System Booster", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        self.lbl_cpu = ctk.CTkLabel(self.sidebar_frame, text="CPU Usage: --%", font=ctk.CTkFont(size=14))
        self.lbl_cpu.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        self.lbl_ram = ctk.CTkLabel(self.sidebar_frame, text="RAM Used: --%", font=ctk.CTkFont(size=14))
        self.lbl_ram.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        
        self.lbl_status = ctk.CTkLabel(self.sidebar_frame, text="Global Status: IDLE", font=ctk.CTkFont(size=15, weight="bold"), text_color="gray")
        self.lbl_status.grid(row=3, column=0, padx=20, pady=20, sticky="w")
        
        self.btn_revert = ctk.CTkButton(self.sidebar_frame, text="Revert to Normal", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), hover_color="#B22222", command=self.manual_revert)
        self.btn_revert.grid(row=6, column=0, padx=20, pady=20)
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        
        self.lbl_header = ctk.CTkLabel(self.main_frame, text="Currently Accelerated Program", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_header.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        self.lbl_active_window = ctk.CTkLabel(self.main_frame, text="None (Waiting for Boost...)", font=ctk.CTkFont(size=20, weight="bold"), text_color="#3498db")
        self.lbl_active_window.grid(row=1, column=0, sticky="w", pady=(0, 20))
        
        self.log_textbox = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(family="Consolas", size=13))
        self.log_textbox.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        self.log_textbox.configure(state="disabled")
        
        self.btn_force_boost = ctk.CTkButton(self.main_frame, text="⚡ ACTIVATE GLOBAL BOOST", height=60, font=ctk.CTkFont(size=16, weight="bold"), command=self.manual_boost)
        self.btn_force_boost.grid(row=3, column=0, sticky="ew")

        self.tracker.log = self.append_log
        self.append_log("System Ready. Click Activate to grant Dynamic Powers.")
        self.update_stats()

    def manual_boost(self):
        if not self.tracker.is_boosted:
            self.tracker.toggle_boost()
            self.btn_force_boost.configure(text="⚡ DEACTIVATE BOOST", fg_color="#e74c3c", hover_color="#c0392b")
        else:
            self.tracker.toggle_boost()
            self.btn_force_boost.configure(text="⚡ ACTIVATE GLOBAL BOOST", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])

    def manual_revert(self):
        if self.tracker.is_boosted:
            self.manual_boost()

    def append_log(self, text):
        self.log_textbox.configure(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log_textbox.insert("end", f"[{ts}] {text}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def update_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        self.lbl_cpu.configure(text=f"CPU Usage: {cpu:.1f}%")
        self.lbl_ram.configure(text=f"RAM Used: {mem.percent:.1f}%")
        
        if self.tracker.is_boosted:
            self.lbl_status.configure(text="Status: ACTIVE", text_color="#3498db")
            if self.tracker.active_process_name:
                self.lbl_active_window.configure(text=self.tracker.active_process_name)
        else:
            self.lbl_status.configure(text="Status: IDLE", text_color="gray")
            self.lbl_active_window.configure(text="None (Waiting for Boost...)")
            
        self.after(1500, self.update_stats)

    def on_closing(self):
        self.tracker.stop_event.set()
        if self.tracker.is_boosted:
            self.tracker.toggle_boost()
        self.destroy()

if __name__ == "__main__":
    AdminPrivilegeHandler.ensure_admin()
    app_tracker = DynamicForegroundTracker()
    
    thread = threading.Thread(target=app_tracker.run_loop, daemon=True)
    thread.start()
    
    gui = BoosterGUI(app_tracker)
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()
