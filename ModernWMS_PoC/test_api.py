import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

def print_response(response, description):
    print(f"\n{description}:")
    print(f"Status Code: {response.status_code}")
    try:
        print("Response:", json.dumps(response.json(), indent=2))
    except:
        print("Response:", response.text)

def test_authentication():
    print("\n=== Testing Authentication ===")
    
    # Test login with admin credentials
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": ADMIN_CREDENTIALS["username"], "password": ADMIN_CREDENTIALS["password"]}
    )
    print_response(response, "Login with admin credentials")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test getting current user
        response = requests.get(f"{BASE_URL}/users/me/", headers=headers)
        print_response(response, "Get current user")
        
        return headers
    return {}

def test_warehouse_operations(headers):
    if not headers:
        print("Skipping warehouse tests - no valid token")
        return
        
    print("\n=== Testing Warehouse Operations ===")
    
    # Test creating a warehouse
    warehouse_data = {
        "name": "Main Warehouse",
        "location": "New York"
    }
    response = requests.post(
        f"{BASE_URL}/warehouses/", 
        json=warehouse_data,
        headers=headers
    )
    print_response(response, "Create warehouse")
    warehouse_id = response.json().get("id") if response.status_code == 200 else None
    
    # Test listing warehouses
    response = requests.get(f"{BASE_URL}/warehouses/", headers=headers)
    print_response(response, "List warehouses")

def test_user_management(headers):
    if not headers:
        print("Skipping user management tests - no valid token")
        return
        
    print("\n=== Testing User Management ===")
    
    # Test creating a new user
    user_data = {
        "username": "testuser",
        "password": "testpass123",
        "role": "user"
    }
    response = requests.post(
        f"{BASE_URL}/users/", 
        json=user_data,
        headers=headers
    )
    print_response(response, "Create user")

if __name__ == "__main__":
    print("Starting WMS PoC API Tests...")
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Root endpoint")
    
    # Run tests
    headers = test_authentication()
    test_warehouse_operations(headers)
    test_user_management(headers)
    
    print("\n=== Tests Complete ===")
