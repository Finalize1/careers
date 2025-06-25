import json

with open(r"C:\Users\Administrator\Desktop\careers\yl1001\jobs.jl", "r", encoding="utf-8") as f:
    jobs = f.readlines()

with open(r'C:\Users\Administrator\Desktop\careers\yl1001\cookies.json', 'r', encoding='utf-8') as f:
    cookies = json.load(f)

cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])

for job in jobs:
    print(job)
    job = json.loads(job)
    print(job)
