import requests

# 1. Get an investigation
res = requests.get('http://localhost:8000/investigations')
invs = res.json()['items']
inv = invs[0]
print(f"Testing on {inv['id']} - {inv['title']}")

# 2. Find a hypothesis
if len(inv['hypotheses']) > 0:
    hyp = inv['hypotheses'][0]
    print(f"Selected Hypothesis: {hyp['description']}")
    
    # 3. Create an experiment
    print("Creating experiment...")
    sql = 'SELECT * FROM dataset WHERE email IS NULL'
    exp_res = requests.post(f'http://localhost:8000/investigations/{inv["id"]}/hypotheses/{hyp["id"]}/experiments', json={'sql_query': sql})
    exp = exp_res.json()
    print("Created experiment:", exp['id'])
    
    # 4. Run the experiment
    print("Running experiment...")
    run_res = requests.post(f'http://localhost:8000/investigations/{inv["id"]}/experiments/{exp["id"]}/run')
    run = run_res.json()
    print("Run result status:", run['status'])
    if run.get('result'):
        print("Rows:", run['result']['row_count'])
        print("Columns:", run['result']['columns'])
    else:
        print("No result object?", run)
else:
    print("No hypotheses found.")
