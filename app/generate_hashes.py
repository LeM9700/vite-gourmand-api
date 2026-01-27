import sys
sys.path.append('.')

from app.modules.auth.security import hash_password

# Génération des hashs pour vos utilisateurs de test
passwords = {
    "admin123": "",
    "user123": "",
    "employee123": ""
}

print("Hashes pour vos utilisateurs de test :")
print("=====================================")

for password, _ in passwords.items():
    hashed = hash_password(password)
    print(f"Password: {password}")
    print(f"Hash: {hashed}")
    print("-" * 50)