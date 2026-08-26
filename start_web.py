import subprocess
import sys

log = open("web_start.log", "w", encoding="utf-8")
p = subprocess.Popen(
    [sys.executable, "-m", "md2style.interfaces.web"],
    creationflags=0x00000008,  # DETACHED_PROCESS
    cwd=r"d:\zh材料\vibe code\skills\md转换",
    stdout=log,
    stderr=subprocess.STDOUT,
)
print("Web 界面已后台启动: http://127.0.0.1:8080  (pid=%s)" % p.pid)
