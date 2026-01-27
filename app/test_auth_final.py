import requests
import json

def test_auth_endpoints():
    """Test les deux endpoints d'authentification"""
    
    base_url = "http://localhost:8000"
    
    # Données de test
    test_data = {
        "email": "jose.admin@vitegourmand.test",
        "password": "Password123!"
    }
    
    print("🧪 TEST DES ENDPOINTS D'AUTHENTIFICATION\n")
    
    # Test 1: Endpoint JSON /auth/login
    print("📡 Test 1: POST /auth/login (JSON)")
    try:
        response = requests.post(
            f"{base_url}/auth/login",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS: Token reçu")
            print(f"   Token: {data['access_token'][:50]}...")
        else:
            print(f"   ❌ ERROR: {response.text}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 2: Endpoint Form /auth/token
    print("📡 Test 2: POST /auth/token (Form-data)")
    try:
        response = requests.post(
            f"{base_url}/auth/token",
            data={
                "username": test_data["email"],  # OAuth2 utilise 'username'
                "password": test_data["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS: Token reçu")
            print(f"   Token: {data['access_token'][:50]}...")
        else:
            print(f"   ❌ ERROR: {response.text}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")

    print("\n" + "-" * 60)
    
    # Test 3: Vérification avec curl (à copier-coller dans le terminal)
    print("🔧 Test manuel avec curl:")
    print("\n# Test JSON:")
    print(f'curl -X POST "{base_url}/auth/login" \\')
    print('  -H "Content-Type: application/json" \\')
    print(f'  -d \'{json.dumps(test_data)}\'')
    
    print("\n# Test Form:")
    print(f'curl -X POST "{base_url}/auth/token" \\')
    print('  -H "Content-Type: application/x-www-form-urlencoded" \\')
    print(f'  -d "username={test_data["email"]}&password={test_data["password"]}"')

if __name__ == "__main__":
    print("Assurez-vous que votre serveur FastAPI est démarré:")
    print("uvicorn app.main:app --reload\n")
    
    input("Appuyez sur Entrée pour continuer...")
    test_auth_endpoints()