"""
Tests pour le service d'envoi d'emails avec mocking Mailgun API
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.email_service import EmailService, email_service
from app.core.config import settings


def _mock_mailgun_response(status_code=200):
    """Helper: crée un objet Response mocké pour Mailgun"""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"id": "<mock-msg-id>", "message": "Queued. Thank you."}
    resp.text = '{"id":"<mock-msg-id>","message":"Queued. Thank you."}'
    return resp


@pytest.fixture
def mock_mailgun():
    """Fixture pour mocker l'appel requests.post vers Mailgun"""
    with patch('app.core.email_service.requests.post') as mock_post:
        mock_post.return_value = _mock_mailgun_response(200)
        yield mock_post


@pytest.fixture
def email_svc():
    """Fixture pour créer une instance du service email avec config de test"""
    svc = EmailService()
    # Injecter des valeurs de test pour éviter le mode simulation (api_key vide)
    svc.api_key = "test-api-key-123456"
    svc.domain = "test.mailgun.org"
    svc.from_email = "Test <postmaster@test.mailgun.org>"
    svc.base_url = "https://api.mailgun.net/v3/test.mailgun.org/messages"
    return svc


class TestEmailServiceConfiguration:
    """Tests de configuration du service email"""
    
    def test_email_service_initialization(self, email_svc):
        """Test que le service email s'initialise avec les bons paramètres"""
        assert email_svc.api_key is not None
        assert len(email_svc.api_key) > 0
        assert email_svc.from_email is not None
        assert "mailgun.org" in email_svc.base_url
    
    def test_email_service_global_instance(self):
        """Test que l'instance globale email_service existe"""
        assert email_service is not None
        assert isinstance(email_service, EmailService)


class TestConfirmationToken:
    """Tests de génération et vérification des tokens de confirmation"""
    
    def test_generate_confirmation_token(self, email_svc):
        """Test génération d'un token de confirmation"""
        user_id = 123
        email = "test@example.com"
        
        token = email_svc.generate_confirmation_token(user_id, email)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_verify_valid_confirmation_token(self, email_svc):
        """Test vérification d'un token valide"""
        user_id = 123
        email = "test@example.com"
        
        # Générer le token
        token = email_svc.generate_confirmation_token(user_id, email)
        
        # Vérifier le token
        payload = email_svc.verify_confirmation_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["type"] == "email_confirmation"
        assert payload["iss"] == "vite-gourmand-email"
    
    def test_verify_expired_token(self, email_svc):
        """Test qu'un token expiré est rejeté"""
        # Créer un token expiré (expire dans le passé)
        user_id = 123
        email = "test@example.com"
        expire = datetime.now(timezone.utc) - timedelta(hours=1)  # Expiré il y a 1h
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "email_confirmation",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": "vite-gourmand-email"
        }
        
        expired_token = jwt.encode(payload, settings.email_confirmation_secret, algorithm="HS256")
        
        # Vérifier qu'il est rejeté
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            email_svc.verify_confirmation_token(expired_token)
        
        assert exc_info.value.status_code == 400
        assert "expiré" in exc_info.value.detail.lower() or "expired" in exc_info.value.detail.lower()
    
    def test_verify_invalid_token(self, email_svc):
        """Test qu'un token invalide est rejeté"""
        invalid_token = "invalid.token.here"
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            email_svc.verify_confirmation_token(invalid_token)
        
        assert exc_info.value.status_code == 400
    
    def test_verify_wrong_type_token(self, email_svc):
        """Test qu'un token d'un mauvais type est rejeté"""
        # Créer un token avec un type différent
        payload = {
            "sub": "123",
            "email": "test@example.com",
            "type": "password_reset",  # Mauvais type
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            "iat": datetime.now(timezone.utc),
            "iss": "vite-gourmand-email"
        }
        
        wrong_type_token = jwt.encode(payload, settings.email_confirmation_secret, algorithm="HS256")
        
        with pytest.raises(ValueError) as exc_info:
            email_svc.verify_confirmation_token(wrong_type_token)
        
        assert "Type de token invalide" in str(exc_info.value)


class TestSendEmails:
    """Tests d'envoi d'emails avec mocking Mailgun API"""
    
    def test_send_confirmation_email_success(self, email_svc, mock_mailgun):
        """Test envoi réussi d'un email de confirmation"""
        user_id = 123
        email = "test@example.com"
        firstname = "Jean"
        
        result = email_svc.send_confirmation_email(user_id, email, firstname)
        
        # Vérifier que l'envoi a réussi
        assert result is True
        
        # Vérifier que Mailgun a été appelé
        mock_mailgun.assert_called_once()
        call_kwargs = mock_mailgun.call_args
        assert call_kwargs[1]["auth"] == ("api", email_svc.api_key)
    
    def test_send_confirmation_email_contains_token(self, email_svc, mock_mailgun):
        """Test que l'email de confirmation contient un token"""
        user_id = 123
        email = "test@example.com"
        firstname = "Jean"
        
        email_svc.send_confirmation_email(user_id, email, firstname)
        
        # Récupérer l'appel à requests.post
        assert mock_mailgun.called
        call_data = mock_mailgun.call_args[1]["data"]
        
        # Vérifier que le HTML contient un lien de confirmation
        assert "confirm" in call_data["html"].lower() or "confirme" in call_data["html"].lower()
    
    def test_send_confirmation_email_mailgun_failure(self, email_svc, mock_mailgun):
        """Test gestion d'erreur lors d'un échec Mailgun"""
        mock_mailgun.return_value = _mock_mailgun_response(500)
        
        user_id = 123
        email = "test@example.com"
        firstname = "Jean"
        
        result = email_svc.send_confirmation_email(user_id, email, firstname)
        
        # L'envoi doit échouer gracieusement
        assert result is False
    
    def test_send_order_confirmation_email(self, email_svc, mock_mailgun):
        """Test envoi d'un email de confirmation de commande"""
        result = email_svc.send_order_confirmation_email(
            user_email="client@example.com",
            user_name="Jean Dupont",
            order_id=456,
            menu_title="Menu Gastronomique",
            event_date="2026-02-15",
            event_time="19:00",
            people_count=15,
            total_price=750.00,
            delivery_city="Paris"
        )
        
        assert result is True
        mock_mailgun.assert_called_once()
    
    def test_send_order_completed_email(self, email_svc, mock_mailgun):
        """Test envoi d'un email de commande complétée"""
        result = email_svc.send_order_completed_email(
            user_email="client@example.com",
            user_name="Jean Dupont",
            order_id=456,
            menu_title="Menu Gastronomique"
        )
        
        assert result is True
        mock_mailgun.assert_called_once()
    
    def test_send_employee_welcome_email(self, email_svc, mock_mailgun):
        """Test envoi d'un email de bienvenue pour employé"""
        result = email_svc.send_employee_welcome_email(
            email="employe@example.com",
            firstname="Marie",
            lastname="Martin"
        )
        
        assert result is True
        mock_mailgun.assert_called_once()
    
    def test_send_equipment_return_reminder(self, email_svc, mock_mailgun):
        """Test envoi d'un rappel de retour de matériel"""
        result = email_svc.send_equipment_return_reminder(
            user_email="client@example.com",
            user_name="Jean Dupont",
            order_id=456,
            event_date="2026-02-15"
        )
        
        assert result is True
        mock_mailgun.assert_called_once()


class TestPasswordResetEmail:
    """Tests pour les emails de réinitialisation de mot de passe"""
    
    def test_send_password_reset_email(self, email_svc, mock_mailgun):
        """Test envoi d'un email de réinitialisation de mot de passe"""
        result = email_svc.send_password_reset_email(
            user_email="user@example.com",
            user_name="Jean",
            reset_token="test-reset-token-12345",
            frontend_url="http://localhost:3000"
        )
        
        assert result is True
        mock_mailgun.assert_called_once()


class TestEmailTemplates:
    """Tests pour les templates HTML des emails"""
    
    def test_confirmation_email_template_contains_url(self, email_svc):
        """Test que le template de confirmation contient l'URL"""
        firstname = "Jean"
        confirmation_url = "http://localhost:8000/auth/confirm-email?token=abc123"
        
        html = email_svc._get_confirmation_email_template(firstname, confirmation_url)
        
        assert html is not None
        assert firstname in html
        assert confirmation_url in html
        assert "confirm" in html.lower() or "confirme" in html.lower()
    
    def test_confirmation_email_template_is_html(self, email_svc):
        """Test que le template de confirmation est du HTML valide"""
        html = email_svc._get_confirmation_email_template("Jean", "http://test.com")
        
        assert "<html" in html.lower() or "<!doctype" in html.lower()
        assert "</html>" in html.lower()
        assert "<body" in html.lower()


class TestMailgunAPI:
    """Tests pour l'intégration Mailgun"""
    
    def test_mailgun_timeout_handling(self, email_svc):
        """Test gestion du timeout Mailgun"""
        import requests as req
        with patch('app.core.email_service.requests.post') as mock_post:
            mock_post.side_effect = req.exceptions.Timeout("Connection timed out")
            
            # S'assurer que l'api_key est présente pour éviter le mode simulation
            email_svc.api_key = "test-key"
            result = email_svc._send_email(
                to_email="test@example.com",
                subject="Test",
                html_content="<p>Test</p>"
            )
            
            assert result is False
    
    def test_mailgun_network_error(self, email_svc):
        """Test gestion d'erreur réseau Mailgun"""
        import requests as req
        with patch('app.core.email_service.requests.post') as mock_post:
            mock_post.side_effect = req.exceptions.ConnectionError("Network error")
            
            email_svc.api_key = "test-key"
            result = email_svc._send_email(
                to_email="test@example.com",
                subject="Test",
                html_content="<p>Test</p>"
            )
            
            assert result is False


class TestEmailValidation:
    """Tests de validation des paramètres d'email"""
    
    def test_send_email_with_empty_recipient(self, email_svc, mock_mailgun):
        """Test qu'un email avec destinataire vide échoue"""
        result = email_svc._send_email(
            to_email="",
            subject="Test",
            html_content="<p>Test</p>",
            text_content="Test"
        )
        
        assert result is False
        mock_mailgun.assert_not_called()
    
    def test_send_email_with_empty_subject(self, email_svc, mock_mailgun):
        """Test qu'un email avec sujet vide fonctionne quand même"""
        result = email_svc._send_email(
            to_email="test@example.com",
            subject="",
            html_content="<p>Test</p>",
            text_content="Test"
        )
        
        # Doit fonctionner même avec sujet vide
        assert result is True
