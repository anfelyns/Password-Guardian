# -*- coding: utf-8 -*-
# main.py
import os, subprocess, sys, time, runpy

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def start_backend():
    # Run Flask as a module from project root so "database" package is found
    env = os.environ.copy()
    return subprocess.Popen(
        [sys.executable, "-m", "backend_api.app"],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=None,
        stderr=None,
    )

def start_gui():
    """
    Try importing start_securevault as a module. If not found,
    execute start_securevault.py as a script.
    """
    sys.path.insert(0, PROJECT_ROOT) 
    try:
        from start_securevault import main as gui_main  
        return gui_main()
    except ModuleNotFoundError:
        # Fallback: run the script directly
        gui_path = os.path.join(PROJECT_ROOT, "start_securevault.py")
        if not os.path.exists(gui_path):
            raise FileNotFoundError(
                "Could not import 'start_securevault' and file 'start_securevault.py' not found in project root."
            )
        return runpy.run_path(gui_path, run_name="__main__")

if __name__ == "__main__":
    proc = start_backend()
    print("Backend starting on http://127.0.0.1:5000 ...")
    time.sleep(1.5)
    try:
        start_gui()
    finally:
        try:
            proc.terminate()
        except Exception:
            pass
