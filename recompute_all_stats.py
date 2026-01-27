"""
Script pour recalculer toutes les statistiques MongoDB à partir des commandes PostgreSQL
"""
import requests
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"
ADMIN_EMAIL = "jose.admin@vitegourmand.test"  # Admin du seed
ADMIN_PASSWORD = "admin123"  # Mot de passe par défaut du seed

def get_admin_token():
    """Récupère le token admin"""
    print("🔐 Connexion admin...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Erreur de connexion: {response.text}")
        sys.exit(1)
    
    token = response.json()["access_token"]
    print(f"✅ Token obtenu: {token[:20]}...")
    return token

def recompute_stats_for_date(token, date):
    """Recalcule les stats pour une date donnée"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/admin/stats/recompute",
        params={"day": date.strftime("%Y-%m-%d")},
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ {date.strftime('%Y-%m-%d')}: {result.get('items_computed', 0)} stats calculées")
        return True
    else:
        print(f"  ⚠️  {date.strftime('%Y-%m-%d')}: {response.status_code} - {response.text}")
        return False

def main():
    """Recalcule les stats pour les 60 derniers jours"""
    print("📊 Recalcul des statistiques MongoDB\n")
    
    # Connexion
    token = get_admin_token()
    
    # Période à recalculer (basé sur les screenshots: décembre 2025 à janvier 2026)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)  # 60 derniers jours
    
    print(f"\n📅 Période: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}\n")
    
    # Recalculer jour par jour
    current_date = start_date
    success_count = 0
    total_days = (end_date - start_date).days + 1
    
    while current_date <= end_date:
        if recompute_stats_for_date(token, current_date):
            success_count += 1
        current_date += timedelta(days=1)
    
    print(f"\n✅ Terminé: {success_count}/{total_days} jours calculés avec succès")
    print(f"\n💡 Vous pouvez maintenant voir les statistiques dans l'application Flutter!")

if __name__ == "__main__":
    main()
