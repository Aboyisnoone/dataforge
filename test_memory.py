import requests

# 1. Get investigations
res = requests.get('http://localhost:8000/investigations')
invs = res.json()['items']

if len(invs) >= 1:
    inv1 = invs[0]
    
    # 2. Resolve the first investigation
    print(f"Resolving investigation {inv1['id']}")
    requests.patch(f'http://localhost:8000/investigations/{inv1["id"]}', json={
        'status': 'RESOLVED',
        'resolution': {
            'root_cause': 'An upstream pipeline script dropped the column during transformation.',
            'resolution_type': 'FIXED',
            'resolved_at': '2026-09-04T00:00:00Z',
            'validation_result': 'Verified by SQL'
        }
    })
    
    # 3. If there's a second investigation, query memory
    if len(invs) > 1:
        inv2 = invs[1]
        print(f"Querying memory for {inv2['id']}")
        mem = requests.get(f'http://localhost:8000/investigations/{inv2["id"]}/memory')
        
        print("Memory Result:", mem.status_code)
        print(mem.json())
