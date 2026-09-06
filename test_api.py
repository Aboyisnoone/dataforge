import requests

# 1. Test CSV V1
print('Uploading V1 CSV')
r1 = requests.post('http://localhost:8000/datasets', files={'file': open('test_v1.csv', 'rb')}, data={'dataset_name': 'customer_data'})
print(r1.status_code, r1.json())

# 2. Test Deduplication
print('\nUploading V1 CSV again')
r2 = requests.post('http://localhost:8000/datasets', files={'file': open('test_v1.csv', 'rb')}, data={'dataset_name': 'customer_data'})
print(r2.status_code, r2.json())

# 3. Test CSV V2 (Schema drift)
print('\nUploading V2 CSV')
r3 = requests.post('http://localhost:8000/datasets', files={'file': open('test_v2.csv', 'rb')}, data={'dataset_name': 'customer_data'})
print(r3.status_code, r3.json())

# 4. Test JSON
print('\nUploading JSON')
rj = requests.post('http://localhost:8000/datasets', files={'file': open('test.json', 'rb')})
print(rj.status_code, rj.json())

# 5. Test NDJSON
print('\nUploading NDJSON')
rn = requests.post('http://localhost:8000/datasets', files={'file': open('test.ndjson', 'rb')})
print(rn.status_code, rn.json())

# 6. Test Parquet
print('\nUploading Parquet')
rp = requests.post('http://localhost:8000/datasets', files={'file': open('test.parquet', 'rb')})
print(rp.status_code, rp.json())

# 7. Test Malformed
print('\nUploading Malformed CSV')
rm = requests.post('http://localhost:8000/datasets', files={'file': open('test_malformed.csv', 'rb')}, data={'dataset_name': 'bad_data'})
print(rm.status_code, rm.json())

