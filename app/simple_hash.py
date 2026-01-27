import bcrypt

def hash_password(password: str) -> str:
    # Encode le mot de passe en bytes
    pwd_bytes = password.encode('utf-8')
    # Génère un salt et hache le mot de passe
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    # Encode le mot de passe et le hash
    pwd_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    # Vérifie le mot de passe
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

if __name__ == "__main__":
    # Test des mots de passe
    passwords = ["admin123", "user123", "employee123"]
    
    print("Test avec bcrypt direct :")
    for pwd in passwords:
        hashed = hash_password(pwd)
        verification = verify_password(pwd, hashed)
        print(f"Password: {pwd}")
        print(f"Hash: {hashed}")
        print(f"Verify: {verification}")
        print("-" * 50)