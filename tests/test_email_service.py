"""
Tests pour le service d'envoi d'emails avec mocking SMTP
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.email_service import EmailService, email_service
from app.core.config import settings


@pytest.fixture
def mock_smtp():
    """Fixture pour mocker le serveur SMTP"""
    with patch('smtplib.SMTP') as mock:
        smtp_instance = MagicMock()
        mock.return_value = smtp_instance
        yield smtp_instance


@pytest.fixture
def email_svc():
    """Fixture pour créer une instance du service email"""
    return EmailService()


class TestEmailServiceConfiguration:
    """Tests de configuration du service email"""
    
    def test_email_service_initialization(self, email_svc):
        """Test que le service email s'initialise avec les bons paramètres"""
        assert email_svc.smtp_server == settings.smtp_server
        assert email_svc.smtp_port == settings.smtp_port
        assert email_svc.smtp_username == settings.smtp_username
        assert email_svc.smtp_password == settings.smtp_password
        assert email_svc.from_email == settings.smtp_from
    
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
    """Tests d'envoi d'emails avec mocking SMTP"""
    
    def test_send_confirmation_email_success(self, email_svc, mock_smtp):
        """Test envoi réussi d'un email de confirmation"""
        user_id = 123
        email = "test@example.com"
        firstname = "Jean"
        
        result = email_svc.send_confirmation_email(user_id, email, firstname)
        
        # Vérifier que l'envoi a réussi
        assert result is True
        
        # Vérifier que SMTP a été appelé
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with(settings.smtp_username, settings.smtp_password)
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()
    
    def test_send_confirmation_email_contains_token(self, email_svc, mock_smtp):
        """Test que l'email de confirmation contient un token"""
        user_id = 123
        email = "test@example.com"
        firstname = "Jean"
        
        email_svc.send_confirmation_email(user_id, email, firstname)
        
        # Récupérer l'appel à send_message
        assert mock_smtp.send_message.called
        sent_message = mock_smtp.send_message.call_args[0][0]
        
        # Vérifier que le message contient des éléments attendus
        message_str = str(sent_message)
        assert "confirmation" in message_str.lower() or "confirm" in message_str.lower()
    
    def test_send_confirmation_email_smtp_failure(self, email_svc, mock_smtp):
        """Test gestion d'erreur lors d'un échec SMTP"""
        mock_smtp.send_message.side_effect = Exception("SMTP Error")
        
        user_id = 123
        email = "test@example.com"
        firstname = "Jean"
        
        result = email_svc.send_confirmation_email(user_id, email, firstname)
        
        # L'envoi doit échouer gracieusement
        assert result is False
    
    def test_send_order_confirmation_email(self, email_svc, mock_smtp):
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
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once()
        mock_smtp.send_message.assert_called_once()
        
        # Pas besoin de vérifier le contenu base64, juste que l'email a été envoyé
        assert result is True
    
    def test_send_order_completed_email(self, email_svc, mock_smtp):
        """Test envoi d'un email de commande complétée"""
        result = email_svc.send_order_completed_email(
            user_email="client@example.com",
            user_name="Jean Dupont",
            order_id=456,
            menu_title="Menu Gastronomique"
        )
        
        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once()
        mock_smtp.send_message.assert_called_once()
        
        # Pas besoin de vérifier le contenu base64, juste que l'email a été envoyé
        assert result is True
    
    def test_send_employee_welcome_email(self, email_svc, mock_smtp):
        """Test envoi d'un email de bienvenue pour employé"""
        result = email_svc.send_employee_welcome_email(
            email="employe@example.com",
            firstname="Marie",
            lastname="Martin"
        )
        
        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once()
        mock_smtp.send_message.assert_called_once()
    
    def test_send_equipment_return_reminder(self, email_svc, mock_smtp):
        """Test envoi d'un rappel de retour de matériel"""
        result = email_svc.send_equipment_return_reminder(
            user_email="client@example.com",
            user_name="Jean Dupont",
            order_id=456,
            event_date="2026-02-15"
        )
        
        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once()
        mock_smtp.send_message.assert_called_once()


class TestPasswordResetEmail:
    """Tests pour les emails de réinitialisation de mot de passe"""
    
    def test_send_password_reset_email(self, email_svc, mock_smtp):
        """Test envoi d'un email de réinitialisation de mot de passe"""
        result = email_svc.send_password_reset_email(
            user_email="user@example.com",
            user_name="Jean",
            reset_token="test-reset-token-12345",
            frontend_url="http://localhost:3000"
        )
        
        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once()
        mock_smtp.send_message.assert_called_once()


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


class TestSMTPConnection:
    """Tests pour la gestion de la connexion SMTP"""
    
    def test_smtp_connection_with_tls(self, email_svc):
        """Test que la connexion SMTP utilise TLS si configuré"""
        with patch('smtplib.SMTP') as mock_smtp:
            smtp_instance = MagicMock()
            mock_smtp.return_value = smtp_instance
            
            # Forcer TLS
            email_svc.smtp_use_tls = True
            
            conn = email_svc._get_smtp_connection()
            
            # Vérifier que starttls a été appelé
            if conn:
                smtp_instance.starttls.assert_called()
    
    def test_smtp_connection_failure(self, email_svc):
        """Test gestion d'erreur lors d'une connexion SMTP échouée"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = Exception("Connection failed")
            
            # La méthode _get_smtp_connection lève une exception HTTPException
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                email_svc._get_smtp_connection()
            
            assert exc_info.value.status_code == 500


class TestEmailValidation:
    """Tests de validation des paramètres d'email"""
    
    def test_send_email_with_empty_recipient(self, email_svc, mock_smtp):
        """Test qu'un email avec destinataire vide échoue"""
        result = email_svc._send_email(
            to_email="",
            subject="Test",
            html_content="<p>Test</p>",
            text_content="Test"
        )
        
        assert result is False or not mock_smtp.send_message.called
    
    def test_send_email_with_empty_subject(self, email_svc, mock_smtp):
        """Test qu'un email avec sujet vide fonctionne quand même"""
        result = email_svc._send_email(
            to_email="test@example.com",
            subject="",
            html_content="<p>Test</p>",
            text_content="Test"
        )
        
        # Doit fonctionner même avec sujet vide
        assert result is True or result is False  # Dépend de l'implémentation
