import requests

BASE_URL = "https://qa-internship.avito.com"

for u_len in [2, 3, 4, 5, 10, 64, 65]:
    uname = "a" * u_len
    r = requests.post(f"{BASE_URL}/api/1/register", json={"username": uname, "password": "Password123!"})
    print(f"Username len={u_len}: status={r.status_code}, body={r.text}")

for p_len in [0, 1, 2, 3, 4, 5, 6, 8]:
    pwd = "p" * p_len
    r = requests.post(f"{BASE_URL}/api/1/register", json={"username": f"test_p_{p_len}_{int(u_len)}", "password": pwd})
    print(f"Password len={p_len}: status={r.status_code}, body={r.text}")
