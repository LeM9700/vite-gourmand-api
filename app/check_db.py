import sqlite3
import bcrypt

def check_database():
    """Vérifie les données dans la base SQLite"""
    
    conn = sqlite3.connect("vite_gourmand.db")
    cursor = conn.cursor()
    
    print("=== VÉRIFICATION DE LA BASE DE DONNÉES ===\n")
    
    # Vérifier les utilisateurs
    print("👥 UTILISATEURS:")
    cursor.execute("SELECT id, firstname, lastname, email, role, password_hash FROM users")
    users = cursor.fetchall()
    
    for user in users:
        print(f"  ID: {user[0]}")
        print(f"  Nom: {user[1]} {user[2]}")
        print(f"  Email: {user[3]}")
        print(f"  Rôle: {user[4]}")
        print(f"  Hash: {user[5][:50]}...")
        print("  ---")
    
    # Test du hash avec Password123!
    print("\n🔐 TEST DU MOT DE PASSE:")
    test_password = "Password123!"
    
    for user in users:
        user_hash = user[5]
        try:
            # Test avec bcrypt
            is_valid = bcrypt.checkpw(test_password.encode('utf-8'), user_hash.encode('utf-8'))
            print(f"  {user[3]}: {'✅ VALIDE' if is_valid else '❌ INVALIDE'}")
        except Exception as e:
            print(f"  {user[3]}: ❌ ERREUR - {e}")
    
    # Générer un nouveau hash correct
    print(f"\n🔧 NOUVEAU HASH POUR '{test_password}':")
    new_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
    print(f"  {new_hash.decode('utf-8')}")
    
    # Vérifier les menus
    print(f"\n📋 MENUS:")
    cursor.execute("SELECT id, title, theme, regime, base_price FROM menus")
    menus = cursor.fetchall()
    
    for menu in menus:
        print(f"  ID: {menu[0]} - {menu[1]} ({menu[2]}, {menu[3]}) - {menu[4]}€")
    
    # Vérifier les commandes
    print(f"\n📦 COMMANDES:")
    cursor.execute("""
    SELECT o.id, u.email, m.title, o.status, o.total_price 
    FROM orders o 
    JOIN users u ON o.user_id = u.id 
    JOIN menus m ON o.menu_id = m.id
    """)
    orders = cursor.fetchall()
    
    for order in orders:
        print(f"  Commande #{order[0]} - {order[1]} - {order[2]} - {order[3]} - {order[4]}€")
    
    conn.close()

def fix_passwords():
    """Corrige les mots de passe dans la base"""
    
    conn = sqlite3.connect("vite_gourmand.db")
    cursor = conn.cursor()
    
    print("\n🔧 CORRECTION DES MOTS DE PASSE...")
    
    # Générer le bon hash pour Password123!
    password = "Password123!"
    correct_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Mettre à jour tous les utilisateurs
    cursor.execute("UPDATE users SET password_hash = ?", (correct_hash.decode('utf-8'),))
    
    print(f"✅ Mots de passe mis à jour pour {cursor.rowcount} utilisateurs")
    
    conn.commit()
    conn.close()
    
    print("✅ Base de données mise à jour!")

if __name__ == "__main__":
    print("1. Vérification de la base")
    check_database()
    
    print("\n" + "="*50)
    response = input("\nVoulez-vous corriger les mots de passe ? (y/N): ")
    
    if response.lower() in ['y', 'yes', 'o', 'oui']:
        fix_passwords()
        print("\n2. Nouvelle vérification")
        check_database()