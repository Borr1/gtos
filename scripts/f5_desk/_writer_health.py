import subprocess, re
out = subprocess.check_output(['wmic','process','where',"name='python.exe'",'get','ProcessId,CommandLine','/FORMAT:LIST'], text=True, errors='replace')
blocks = out.split('\n\n')
hits = []
for b in blocks:
    if not b.strip():
        continue
    cl = ''
    pid = ''
    for line in b.splitlines():
        if line.startswith('CommandLine='):
            cl = line[len('CommandLine='):]
        elif line.startswith('ProcessId='):
            pid = line[len('ProcessId='):].strip()
    if re.search(r'book_owner|GTOS_F5|ftmo_f5|ultimate_book|writer', cl, re.I):
        hits.append((pid, cl[:200]))
print('writer_hits', len(hits))
for pid, cl in hits:
    print(pid, '|', cl)
# also schtasks
try:
    t = subprocess.check_output(['schtasks','/Query','/TN','GTOS_F5_FTMO','/FO','LIST','/V'], text=True, errors='replace')
    for key in ('Status:','Last Run Time:','Last Result:','Next Run Time:'):
        for line in t.splitlines():
            if line.strip().startswith(key):
                print(line.strip())
except Exception as e:
    print('schtasks_err', e)
