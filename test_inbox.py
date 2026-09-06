import requests

res = requests.get('http://localhost:8000/investigations')
print("Total investigations:", len(res.json()['items']))
for inv in res.json()['items']:
    print(inv['id'], inv['title'])
    print("Findings:")
    for f in inv['findings']:
        print(f" - {f['title']} (Severity: {f['severity']})")
    print("-" * 20)
