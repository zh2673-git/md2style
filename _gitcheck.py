import subprocess, os
# 用原始字符串避免编码问题
ROOT = r"d:\zh材料\vibe code\skills\md转换"
os.chdir(ROOT)
print("CWD:", os.getcwd())
for args in (["git","rev-parse","--is-inside-work-tree"],
             ["git","remote","-v"],
             ["git","status","--short"],
             ["git","log","--oneline","-3"]):
    r = subprocess.run(args, capture_output=True, text=True)
    print("CMD", args, "-> rc", r.returncode)
    print(r.stdout, r.stderr)
