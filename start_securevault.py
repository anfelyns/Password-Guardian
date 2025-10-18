import os, subprocess, sys, time

def start_backend():
    here = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(here, "backend_api")
    env = os.environ.copy()
    # change port via env if you want: env["PORT"]="5000"
    return subprocess.Popen([sys.executable, "app.py"], cwd=api_dir, env=env)

if __name__ == "__main__":
    proc = start_backend()
    print("Backend starting on http://127.0.0.1:5000 ...")
    time.sleep(1.5)
    try:
        from main import main
        main()
    finally:
        proc.terminate()
