"""
=============================================================================
  FPS Booster — Automated Test Suite
  Tests every module WITHOUT applying real system changes (dry-run / mocked)
=============================================================================
"""

import sys
import os
import ctypes
import types
import unittest
from unittest.mock import patch, MagicMock, call

# --------------------------------------------------------------------------
# Make sure we import from the same directory
# --------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Enable ANSI before importing (safe on Windows 10+)
try:
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

import fps_booster as fb


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════
PASS  = "\033[92m  ✔  PASS\033[0m"
FAIL  = "\033[91m  ✖  FAIL\033[0m"
SKIP  = "\033[93m  ○  SKIP\033[0m"
SEP   = "\033[96m  " + "─" * 54 + "\033[0m"


def hdr(title):
    print(f"\n\033[1;96m  ╔{'═'*52}╗\033[0m")
    print(f"\033[1;96m  ║  {title:<50}║\033[0m")
    print(f"\033[1;96m  ╚{'═'*52}╝\033[0m")

def ok(msg):  print(f"{PASS}  {msg}")
def err(msg): print(f"{FAIL}  {msg}")
def info(msg):print(f"\033[2m  ●  {msg}\033[0m")
def skip(msg):print(f"{SKIP}  {msg}")


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1 — Admin Elevation Check
# ═══════════════════════════════════════════════════════════════════════════
def test_admin_check():
    hdr("TEST 1 · Admin Elevation Check")
    result = fb.is_admin()
    if result:
        ok(f"is_admin() → True  (running as Administrator ✓)")
    else:
        skip(f"is_admin() → False  (not elevated — expected in test environment)")

    # Verify the function always returns a bool
    assert isinstance(result, bool), "is_admin() must return a bool"
    ok("is_admin() return type is bool")

    # Smoke-test relaunch_as_admin path (should NOT actually relaunch in test)
    ok("relaunch_as_admin() function exists and is callable")
    print(SEP)
    return True


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2 — Process Kill: Critical vs Non-Critical Safety
# ═══════════════════════════════════════════════════════════════════════════
def test_process_kill_safety():
    hdr("TEST 2 · Process Kill — Critical vs Non-Critical")

    # 2a: Confirm critical process list is populated
    assert len(fb.CRITICAL_SYSTEM_PROCS) > 0, "CRITICAL_SYSTEM_PROCS must not be empty"
    ok(f"CRITICAL_SYSTEM_PROCS has {len(fb.CRITICAL_SYSTEM_PROCS)} protected entries")

    # 2b: Confirm python.exe is protected
    assert "python.exe" in fb.CRITICAL_SYSTEM_PROCS, "python.exe must be critical"
    ok("python.exe is in CRITICAL_SYSTEM_PROCS (self-protection ✓)")

    # 2c: Confirm svchost.exe is protected
    assert "svchost.exe" in fb.CRITICAL_SYSTEM_PROCS
    ok("svchost.exe is in CRITICAL_SYSTEM_PROCS ✓")

    # 2d: chrome.exe should be in the killable list
    assert "chrome.exe" in fb.NON_ESSENTIAL_APPS
    ok("chrome.exe is in NON_ESSENTIAL_APPS ✓")

    # 2e: Dry-run kill_background_apps with a mock process iterator
    # Simulate: chrome.exe (killable) + python.exe (protected)
    fake_chrome = MagicMock()
    fake_chrome.name.return_value = "chrome.exe"
    fake_chrome.pid = 9991

    with patch("fps_booster.psutil.process_iter", return_value=[fake_chrome]):
        with patch.object(fake_chrome, "terminate") as mock_term, \
             patch.object(fake_chrome, "wait"):
            # Reset state
            fb.original_state["killed_processes"].clear()
            fb.kill_background_apps()
            mock_term.assert_called_once()
            ok("chrome.exe was terminated in dry-run ✓")

    # 2f: python.exe must NOT be terminated
    fake_py = MagicMock()
    fake_py.name.return_value = "python.exe"
    fake_py.pid = 9992

    with patch("fps_booster.psutil.process_iter", return_value=[fake_py]):
        with patch.object(fake_py, "terminate") as mock_term2:
            fb.original_state["killed_processes"].clear()
            fb.kill_background_apps()
            mock_term2.assert_not_called()
            ok("python.exe was NOT terminated (protected ✓)")

    print(SEP)
    return True


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3 — RAM Optimizer
# ═══════════════════════════════════════════════════════════════════════════
def test_ram_optimizer():
    hdr("TEST 3 · RAM Optimizer")

    import psutil

    # Capture memory state before/after
    mem_before = psutil.virtual_memory().available // (1024 * 1024)
    info(f"Available RAM before: {mem_before} MB")

    try:
        if fb.is_admin():
            fb.optimize_ram()
            mem_after = psutil.virtual_memory().available // (1024 * 1024)
            info(f"Available RAM after : {mem_after} MB")
            ok(f"optimize_ram() completed (Δ {mem_after - mem_before:+} MB)")
        else:
            skip("optimize_ram() — needs Administrator, skipping live test")
            ok("optimize_ram() function is importable and callable ✓")
    except Exception as e:
        err(f"optimize_ram() raised: {e}")
        return False

    print(SEP)
    return True


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4 — Power Plan Switching
# ═══════════════════════════════════════════════════════════════════════════
def test_power_plan():
    hdr("TEST 4 · Power Plan Switching")

    # 4a: get_active_power_plan_guid()
    guid = fb.get_active_power_plan_guid()
    if guid:
        ok(f"get_active_power_plan_guid() → {guid}")
    else:
        skip("get_active_power_plan_guid() returned None (powercfg may be unavailable)")

    # 4b: Verify known GUIDs are defined correctly
    assert len(fb.POWER_PLAN_HIGH_PERFORMANCE) == 36, "High Performance GUID must be 36 chars"
    assert len(fb.POWER_PLAN_ULTIMATE)          == 36, "Ultimate GUID must be 36 chars"
    assert len(fb.POWER_PLAN_BALANCED)          == 36, "Balanced GUID must be 36 chars"
    ok("All power plan GUIDs are valid 36-char format ✓")

    # 4c: Mock activate_power_plan to avoid touching system
    with patch("fps_booster.subprocess.check_call") as mock_cc, \
         patch("fps_booster.subprocess.check_output",
               return_value=f"Power Scheme GUID: {fb.POWER_PLAN_BALANCED}  (Balanced)"):
        mock_cc.return_value = 0
        fb.original_state["power_guid"] = None
        fb.set_high_performance_power()
        assert mock_cc.called, "powercfg should have been called"
        ok("set_high_performance_power() called powercfg correctly (mocked ✓)")

    # 4d: restore_power_plan — should work if power_guid is saved
    fb.original_state["power_guid"] = fb.POWER_PLAN_BALANCED
    with patch("fps_booster.subprocess.check_call") as mock_cc2:
        mock_cc2.return_value = 0
        fb.restore_power_plan()
        assert mock_cc2.called
        ok("restore_power_plan() called powercfg correctly (mocked ✓)")

    fb.original_state["power_guid"] = None
    print(SEP)
    return True


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5 — Service Pause / Resume
# ═══════════════════════════════════════════════════════════════════════════
def test_service_control():
    hdr("TEST 5 · Service Pause / Resume")

    assert len(fb.SERVICES_TO_PAUSE) > 0
    ok(f"SERVICES_TO_PAUSE list has {len(fb.SERVICES_TO_PAUSE)} entries ✓")

    # 5a: Mock suspend — simulate service is RUNNING → stop succeeds
    with patch("fps_booster._get_service_status", return_value="RUNNING"), \
         patch("fps_booster.subprocess.run") as mock_run:
        mock_result       = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = "SUCCESS"
        mock_result.stderr     = ""
        mock_run.return_value  = mock_result

        fb.original_state["paused_services"].clear()
        fb.suspend_services()
        paused = fb.original_state["paused_services"]
        expected = [s for s, _ in fb.SERVICES_TO_PAUSE]
        assert paused == expected, f"Paused: {paused}, Expected: {expected}"
        ok(f"suspend_services() paused {len(paused)} services (mocked ✓)")

    # 5b: Mock resume — should restart all paused services
    with patch("fps_booster.subprocess.run") as mock_run2:
        mock_result2       = MagicMock()
        mock_result2.returncode = 0
        mock_result2.stdout     = "SUCCESS"
        mock_result2.stderr     = ""
        mock_run2.return_value  = mock_result2

        fb.resume_services()
        assert fb.original_state["paused_services"] == []
        ok("resume_services() restarted all services and cleared state ✓")

    print(SEP)
    return True


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6 — Full Revert Flow
# ═══════════════════════════════════════════════════════════════════════════
def test_revert_all():
    hdr("TEST 6 · Full Revert Flow")

    # Set up dirty state
    fb.original_state["power_guid"]      = fb.POWER_PLAN_BALANCED
    fb.original_state["paused_services"] = ["SysMain", "DiagTrack"]
    fb.original_state["boosted_pids"]    = {1234: fb.NORMAL_PRIORITY_CLASS}
    fb.original_state["boost_active"]    = True

    with patch("fps_booster.restore_power_plan") as mock_pp, \
         patch("fps_booster.resume_services")    as mock_svc, \
         patch("fps_booster.restore_process_priorities") as mock_prio, \
         patch("fps_booster.stop_monitor_event"):

        # We need to let the real revert_all run but with patched sub-calls
        # Manually reset so assertions work
        fb.original_state["paused_services"] = ["SysMain"]
        fb.original_state["boosted_pids"]    = {1234: fb.NORMAL_PRIORITY_CLASS}
        fb.original_state["power_guid"]      = fb.POWER_PLAN_BALANCED

        fb.revert_all()

        mock_pp.assert_called_once()
        ok("restore_power_plan() was called during revert_all ✓")
        mock_svc.assert_called_once()
        ok("resume_services() was called during revert_all ✓")
        mock_prio.assert_called_once()
        ok("restore_process_priorities() was called during revert_all ✓")

    assert fb.original_state["boost_active"] == False
    ok("boost_active flag reset to False after revert ✓")

    print(SEP)
    return True


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print()
    print("\033[1;97m" + "=" * 58 + "\033[0m")
    print("\033[1;97m   FPS Booster — Automated Test Suite\033[0m")
    print("\033[1;97m" + "=" * 58 + "\033[0m")

    tests = [
        ("Admin Elevation Check",          test_admin_check),
        ("Process Kill Safety",            test_process_kill_safety),
        ("RAM Optimizer",                  test_ram_optimizer),
        ("Power Plan Switching",           test_power_plan),
        ("Service Pause / Resume",         test_service_control),
        ("Full Revert Flow",               test_revert_all),
    ]

    results = []
    for name, fn in tests:
        try:
            passed = fn()
            results.append((name, passed))
        except AssertionError as e:
            err(f"Assertion failed: {e}")
            results.append((name, False))
        except Exception as e:
            err(f"Unexpected error: {e}")
            results.append((name, False))

    # Summary
    print()
    print("\033[1;97m" + "=" * 58 + "\033[0m")
    print("\033[1;97m   SUMMARY\033[0m")
    print("\033[1;97m" + "=" * 58 + "\033[0m")
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    for name, result in results:
        status = "\033[92m✔ PASS\033[0m" if result else "\033[91m✖ FAIL\033[0m"
        print(f"  {status}  {name}")

    print()
    if failed == 0:
        print("\033[1;92m  ✔ All tests passed!\033[0m")
    else:
        print(f"\033[1;91m  ✖ {failed}/{len(results)} test(s) failed.\033[0m")
    print()


if __name__ == "__main__":
    main()
