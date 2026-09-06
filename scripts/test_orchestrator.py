import requests
import pandas as pd
import numpy as np

print('Generating v1.csv...')
df1 = pd.DataFrame({'id': range(1000), 'name': ['User ' + str(i) for i in range(1000)], 'email': ['user' + str(i) + '@example.com' if i > 10 else None for i in range(1000)], 'age': np.random.randint(20, 60, size=1000)})
df1.to_csv('v1.csv', index=False)

print('Generating v2.csv...')
df2 = pd.DataFrame({'id': range(1000), 'name': ['User ' + str(i) for i in range(1000)], 'email': ['user' + str(i) + '@example.com' if i > 380 else None for i in range(1000)], 'age': np.random.randint(20, 60, size=1000), 'phone': ['555-010' + str(i) for i in range(1000)]})
df2.to_csv('v2.csv', index=False)

url = 'http://localhost:8000/datasets'
with open('v1.csv', 'rb') as f:
    res1 = requests.post(url, files={'file': f}, data={'dataset_name': 'customers'})
dataset_id = res1.json()['id']

url_v2 = url + '/' + dataset_id + '/versions'
with open('v2.csv', 'rb') as f:
    res2 = requests.post(url_v2, files={'file': f})
print('v2 status:', res2.status_code)

inv_res = requests.get('http://localhost:8000/investigations')
for inv in inv_res.json():
    print('Investigation:', inv['id'], inv['title'])
    print('  Findings:', len(inv.get('findings', list())))
