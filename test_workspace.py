import requests

# get list to get an id
res = requests.get('http://localhost:8000/investigations')
invs = res.json()['items']
if invs:
    inv_id = invs[0]['id']
    print(f"Fetching {inv_id}")
    r = requests.get(f'http://localhost:8000/investigations/{inv_id}')
    print(r.status_code)
    data = r.json()
    print("Dataset:", data.get('dataset_name'), data.get('dataset_version_number'))
    print("Findings:", len(data.get('findings', [])))
    print("Timeline:", len(data.get('timeline', [])))
    print("Hypotheses:", len(data.get('hypotheses', [])))
