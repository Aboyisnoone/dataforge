import requests

BASE_URL = 'http://localhost:8000'

def test_missing_entities():
    print("=== Testing Missing Entities ===")
    res = requests.get(f"{BASE_URL}/datasets/ds_fake_id_123")
    print("Fake Dataset GET:", res.status_code)
    assert res.status_code == 404

    res = requests.get(f"{BASE_URL}/investigations/inv_fake_id_123")
    print("Fake Investigation GET:", res.status_code)
    assert res.status_code == 404
    
    print("Missing Entities Handled correctly.")

if __name__ == '__main__':
    test_missing_entities()
