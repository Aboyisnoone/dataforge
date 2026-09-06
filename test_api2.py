import requests

with open('test_malformed2.csv', 'w', encoding='utf-8') as f:
    f.write('id,name\n')
    f.write('1,Alice\n')
    f.write('2,Bob,extra,super,extra\n') # too many columns
    f.write('3,Charlie,xyz\n')

# Or even better, a file that is not even a CSV
with open('test_malformed3.csv', 'wb') as f:
    f.write(b'\x00\x01\x02\x03\x04\x05\x06')

print('\nUploading Malformed CSV 3 (binary garbage)')
rm = requests.post('http://localhost:8000/datasets', files={'file': open('test_malformed3.csv', 'rb')}, data={'dataset_name': 'bad_data3'})
print(rm.status_code, rm.json())

