import requests

BASE_URL = 'http://localhost:8000'

def test_failures():
    print("=== 10.2 Failure & Recovery Tests ===")
    
    # 1. Malformed CSV
    res = requests.post(f"{BASE_URL}/datasets", files={"file": ('bad.csv', b"id,name\n1,Alice\n\x00\x01\xff")}, data={"name": "Bad"})
    print("Malformed CSV status:", res.status_code)
    
    # 2. Get the previously created investigation
    res = requests.get(f"{BASE_URL}/investigations")
    inv_id = res.json()['items'][0]['id']
    
    # 3. Create a malicious SQL experiment
    inv = requests.get(f"{BASE_URL}/investigations/{inv_id}").json()
    hyp_id = inv['hypotheses'][0]['id']
    
    bad_sql = "DROP TABLE dataset;"
    res = requests.post(f"{BASE_URL}/investigations/{inv_id}/hypotheses/{hyp_id}/experiments", json={
        "sql_query": bad_sql,
        "requested_by": "Hacker"
    })
    exp_id = res.json()['id']
    
    res = requests.post(f"{BASE_URL}/investigations/{inv_id}/experiments/{exp_id}/run")
    assert res.status_code == 200 # the run route catches errors and sets them in result
    
    result = res.json()['result']
    print("Malicious SQL Result Error:", result.get('error_message'))
    assert result.get('error_message') is not None, "SQL Injection was NOT caught!"
    
    print("Failure Tests Passed ?")

if __name__ == '__main__':
    test_failures()
