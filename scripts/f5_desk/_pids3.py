import subprocess, re
raw = subprocess.check_output(["wmic", "process", "where", "Name='python.exe'", "get", "ProcessId,CommandLine", "/FORMAT:CSV"])
text = raw.decode("utf-8", "replace")
for m in re.finditer(r'operator.*?,\s*(\d+)\s*', text):
    start = max(0, m.start()-80)
    print(m.group(1), text[start:m.end()].replace("\r","")[-180:])
print("---ALL FTMO---")
for line in text.replace("\r","").split("\n"):
    if "operator" in line:
        pid = line.rsplit(",",1)[-1].strip()
        print(pid, line[line.find("run_book"):line.find("run_book")+90] if "run_book" in line else line[-120:])
