"""Single-instance guard for the book monitor daemon (.tools/monitor_books.py::_another_monitor_running).

Locks in the root-cause fix: the venv `Scripts\\python.exe` is a thin launcher that re-execs the real
interpreter as a CHILD, so the daemon runs as a shim->child pair sharing one `monitor_books.py --loop`
command line. The guard must NOT treat its own launcher-parent (or a spawned child) as a rival monitor
(doing so made every monitor child instantly defer to its own shim and exit -> NO monitor survived).
It must still yield to a GENUINELY separate SENIOR monitor, with a total-order (create_time, pid) tie-break.
"""
import importlib.util
import os
import sys
import types

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD_PATH = os.path.join(REPO, ".tools", "monitor_books.py")


def _load_module():
    # stub the heavy/Windows-only imports the module pulls at import time so the test is portable
    sys.modules.setdefault("MetaTrader5", types.ModuleType("MetaTrader5"))
    if "dotenv" not in sys.modules:
        dotenv = types.ModuleType("dotenv")
        dotenv.load_dotenv = lambda *a, **k: None
        sys.modules["dotenv"] = dotenv
    spec = importlib.util.spec_from_file_location("monitor_books_under_test", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load_module()

CMD = ["python", r".tools\monitor_books.py", "--loop", "300"]   # a real monitor command line


def _fake_psutil(me_pid, me_ppid, me_ct, procs):
    """procs: list of dicts {pid, ppid, name, create_time, cmdline}."""
    fake = types.ModuleType("psutil")

    class _Me:
        pid = me_pid

        def create_time(self):
            return me_ct

        def ppid(self):
            return me_ppid

    class _P:
        def __init__(self, d):
            self.info = d

    fake.Process = lambda: _Me()
    fake.process_iter = lambda attrs=None: [_P(d) for d in procs]
    return fake


def _run(monkeypatch, me_pid, me_ppid, me_ct, procs):
    monkeypatch.setitem(sys.modules, "psutil", _fake_psutil(me_pid, me_ppid, me_ct, procs))
    return MOD._another_monitor_running()


def _proc(pid, ppid, ct, name="python.exe", cmdline=None):
    return {"pid": pid, "ppid": ppid, "name": name, "create_time": ct,
            "cmdline": CMD if cmdline is None else cmdline}


def test_excludes_own_launcher_parent(monkeypatch):
    # the ONLY other monitor is our venv-shim PARENT (pid==my_ppid) -> NOT a rival -> survive
    procs = [_proc(50, 10, 1000.0)]   # pid 50 == me's ppid
    assert _run(monkeypatch, me_pid=100, me_ppid=50, me_ct=1000.0, procs=procs) is None


def test_excludes_own_child(monkeypatch):
    # the other monitor is a process WE spawned (its ppid == my_pid) -> same lineage -> survive
    procs = [_proc(200, 100, 1000.0)]   # ppid 100 == me's pid
    assert _run(monkeypatch, me_pid=100, me_ppid=50, me_ct=1000.0, procs=procs) is None


def test_yields_to_separate_senior(monkeypatch):
    # a genuinely separate, OLDER monitor -> defer to it
    procs = [_proc(80, 10, 999.0)]
    assert _run(monkeypatch, me_pid=100, me_ppid=50, me_ct=1000.0, procs=procs) == 80


def test_does_not_yield_to_separate_junior(monkeypatch):
    # a separate but YOUNGER monitor -> we are senior -> survive
    procs = [_proc(300, 10, 1001.0)]
    assert _run(monkeypatch, me_pid=100, me_ppid=50, me_ct=1000.0, procs=procs) is None


def test_tie_broken_by_pid_lower_is_senior(monkeypatch):
    # exact create_time tie: the LOWER pid is senior
    assert _run(monkeypatch, me_pid=100, me_ppid=50, me_ct=1000.0,
                procs=[_proc(80, 10, 1000.0)]) == 80      # 80 < 100 -> senior -> defer
    assert _run(monkeypatch, me_pid=100, me_ppid=50, me_ct=1000.0,
                procs=[_proc(120, 10, 1000.0)]) is None   # 120 > 100 -> junior -> survive


def test_ignores_non_python_and_non_monitor(monkeypatch):
    procs = [
        _proc(80, 10, 999.0, name="powershell.exe"),                 # a shell that merely mentions the script
        _proc(81, 10, 999.0, cmdline=["python", "other.py"]),        # python but not the monitor
        _proc(82, 10, 999.0, cmdline=["python", "monitor_books.py"]),# monitor but no --loop (one-shot)
    ]
    assert _run(monkeypatch, me_pid=100, me_ppid=50, me_ct=1000.0, procs=procs) is None


def test_self_excluded(monkeypatch):
    # our own pid in the list must never count as a rival
    procs = [_proc(100, 50, 1000.0)]   # pid == me_pid
    assert _run(monkeypatch, me_pid=100, me_ppid=50, me_ct=1000.0, procs=procs) is None
