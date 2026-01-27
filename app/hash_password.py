from passlib.context import CryptContext

# Test direct sans dépendances du projet
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == "__main__":
    # Test des mots de passe
    passwords = ["admin123", "user123", "employee123"]
    
    for pwd in passwords:
        hashed = hash_password(pwd)
        verification = verify_password(pwd, hashed)
        print(f"Password: {pwd}")
        print(f"Hash: {hashed}")
        print(f"Verify: {verification}")
        print("-" * 50)