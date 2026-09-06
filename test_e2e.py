import requests
import time
import os

BASE_URL = 'http://localhost:8000'

def create_dataset_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def run_e2e():
    print("=== 10.1 E2E Test ===")
    
    # 1. Create V1
    v1_content = "id,name,email\n1,Alice,alice@a.com\n2,Bob,bob@b.com\n3,Charlie,char@c.com\n"
    create_dataset_file('v1.csv', v1_content)
    
    with open('v1.csv', 'rb') as f:
        res = requests.post(f"{BASE_URL}/datasets", files={"file": f}, data={"name": "E2E Dataset", "description": "Testing E2E"})
    
    assert res.status_code == 200, res.text
    ds_id = res.json()['id']
    print(f"Dataset created: {ds_id}")
    
    # 2. Create V2 (introduces nulls in email)
    v2_content = "id,name,email\n1,Alice,\n2,Bob,\n3,Charlie,char@c.com\n"
    create_dataset_file('v2.csv', v2_content)
    
    with open('v2.csv', 'rb') as f:
        res = requests.post(f"{BASE_URL}/datasets/{ds_id}/versions", files={"file": f}, data={"description": "V2 update"})
    
    assert res.status_code == 200, res.text
    print("V2 uploaded")
    
    # 3. Wait for investigation to be generated (synchronous in this architecture)
    res = requests.get(f"{BASE_URL}/investigations", params={"dataset_id": ds_id})
    invs = res.json()['items']
    assert len(invs) > 0, "No investigation generated"
    inv_id = invs[0]['id']
    print(f"Investigation generated: {inv_id}")
    
    inv = requests.get(f"{BASE_URL}/investigations/{inv_id}").json()
    
    # Transition to INVESTIGATING
    res = requests.patch(f"{BASE_URL}/investigations/{inv_id}", json={"status": "INVESTIGATING"})
    assert res.status_code == 200, res.text
    
    # 4. Extract Hypothesis
    hypotheses = inv.get('hypotheses', [])
    assert len(hypotheses) > 0, "No hypotheses generated"
    hyp_id = hypotheses[0]['id']
    print(f"Hypothesis found: {hyp_id}")
    
    # 5. Create SQL Experiment
    sql = "SELECT * FROM dataset WHERE email IS NULL"
    res = requests.post(f"{BASE_URL}/investigations/{inv_id}/hypotheses/{hyp_id}/experiments", json={
        "sql_query": sql,
        "requested_by": "Test Engineer"
    })
    assert res.status_code == 200, res.text
    exp_id = res.json()['id']
    print(f"Experiment drafted: {exp_id}")
    
    # 6. Run Experiment
    res = requests.post(f"{BASE_URL}/investigations/{inv_id}/experiments/{exp_id}/run")
    assert res.status_code == 200, res.text
    result = res.json()['result']
    assert result['row_count'] == 2, f"Expected 2 nulls, got {result['row_count']}"
    print(f"Experiment validated: found {result['row_count']} rows")
    
    # 7. Resolve Investigation
    res = requests.patch(f"{BASE_URL}/investigations/{inv_id}", json={
        "status": "RESOLVED",
        "resolution": {
            "root_cause": "An automated e2e test verified that 2 rows lost their emails.",
            "resolution_type": "FIXED",
            "resolved_at": "2026-09-05T00:00:00Z",
            "validation_result": "Verified by test experiment"
        }
    })
    assert res.status_code == 200, res.text
    print("Investigation resolved.")
    
    # 8. Create another similar incident (V3)
    v3_content = "id,name,email\n1,Alice,\n2,Bob,\n3,Charlie,\n"
    create_dataset_file('v3.csv', v3_content)
    with open('v3.csv', 'rb') as f:
        res = requests.post(f"{BASE_URL}/datasets/{ds_id}/versions", files={"file": f}, data={"description": "V3 update"})
    
    res = requests.get(f"{BASE_URL}/investigations", params={"dataset_id": ds_id})
    invs = res.json()['items']
    assert len(invs) > 1, "No second investigation generated"
    new_inv_id = [i for i in invs if i['id'] != inv_id][0]['id']
    
    # 9. Query memory
    res = requests.get(f"{BASE_URL}/investigations/{new_inv_id}/memory")
    memories = res.json()
    assert len(memories) > 0, "No memory retrieved!"
    assert memories[0]['investigation_id'] == inv_id, "Retrieved memory does not match the first investigation"
    print(f"Memory successfully retrieved precedent: {memories[0]['resolution_root_cause']}")
    
    print("E2E Test Passed ?")

if __name__ == '__main__':
    run_e2e()
