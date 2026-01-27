import smtplib
import secrets
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from jose import jwt, JWTError

from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
        self.from_email = settings.smtp_from
        
        # Log de diagnostic SMTP
        logger.info(f"🔧 SMTP Config: server={self.smtp_server}, port={self.smtp_port}, user={self.smtp_username[:10] if self.smtp_username else 'N/A'}..., from={self.from_email}")

    def _get_smtp_connection(self):
        """Créer une connexion SMTP sécurisée"""
        try:
            if settings.environment == "development" and not self.smtp_server:
                logger.warning("SMTP non configuré en développement - simulation d'envoi")
                return None
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.smtp_use_tls:
                server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            return server
        except Exception as e:
            logger.error(f"Erreur connexion SMTP: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de l'envoi de l'email"
            )

    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Envoyer un email avec gestion d'erreurs"""
        try:
            # Validation de l'email
            if not to_email or '@' not in to_email:
                raise ValueError("Email invalide")
            
            # En développement, juste logger
            if settings.environment == "development" and not settings.smtp_server:
                logger.info(f"📧 EMAIL SIMULÉ - To: {to_email}, Subject: {subject}")
                logger.info(f"Content: {text_content or html_content[:100]}...")
                return True
            
            server = self._get_smtp_connection()
            if not server:
                return False
            
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Ajouter le contenu texte
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Ajouter le contenu HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Envoyer
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email envoyé avec succès à {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email à {to_email}: {e}")
            return False

    def generate_confirmation_token(self, user_id: int, email: str) -> str:
        """Générer un token de confirmation sécurisé"""
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.email_confirmation_expire_hours)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "email_confirmation",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16),  # Unique token ID
            "iss": "vite-gourmand-email"
        }
        
        return jwt.encode(payload, settings.email_confirmation_secret, algorithm="HS256")

    def verify_confirmation_token(self, token: str) -> dict:
        """Vérifier un token de confirmation"""
        try:
            payload = jwt.decode(
                token, 
                settings.email_confirmation_secret, 
                algorithms=["HS256"]
            )
            
            if payload.get("type") != "email_confirmation":
                raise ValueError("Type de token invalide")
            
            return payload
            
        except JWTError as e:
            logger.warning(f"Token de confirmation invalide: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de confirmation invalide ou expiré"
            )

    def send_confirmation_email(self, user_id: int, email: str, firstname: str) -> bool:
        """Envoyer l'email de confirmation d'inscription"""
        try:
            # Générer le token
            token = self.generate_confirmation_token(user_id, email)
            
            # URL de confirmation
            confirmation_url = f"{settings.frontend_url}/auth/confirm-email?token={token}"
            
            # Template HTML
            html_content = self._get_confirmation_email_template(firstname, confirmation_url)
            
            # Template texte simple
            text_content = f"""
Bonjour {firstname},

Bienvenue chez Vite & Gourmand !

Pour activer votre compte, veuillez cliquer sur le lien suivant :
{confirmation_url}

Ce lien est valide pendant {settings.email_confirmation_expire_hours} heures.

Si vous n'avez pas créé de compte, ignorez ce message.

Merci,
L'équipe Vite & Gourmand
            """.strip()
            
            # Envoyer l'email
            return self._send_email(
                to_email=email,
                subject="Confirmez votre inscription - Vite & Gourmand",
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {e}")
            return False

    def _get_confirmation_email_template(self, firstname: str, confirmation_url: str) -> str:
        """Template HTML pour l'email de confirmation"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmez votre inscription</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Vite & Gourmand</h1>
    </div>
    
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
        <h2 style="color: #333; margin-top: 0;">Bonjour {firstname} !</h2>
        
        <p>Bienvenue chez <strong>Vite & Gourmand</strong> ! 🎉</p>
        
        <p>Pour finaliser votre inscription et activer votre compte, veuillez confirmer votre adresse email en cliquant sur le bouton ci-dessous :</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{confirmation_url}" 
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; 
                      padding: 15px 30px; 
                      text-decoration: none; 
                      border-radius: 25px; 
                      font-weight: bold;
                      display: inline-block;
                      font-size: 16px;">
                ✅ Confirmer mon inscription
            </a>
        </div>
        
        <p style="font-size: 14px; color: #666;">
            <strong>⏰ Important :</strong> Ce lien est valide pendant {settings.email_confirmation_expire_hours} heures.
        </p>
        
        <p style="font-size: 14px; color: #666;">
            Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :<br>
            <a href="{confirmation_url}" style="color: #667eea; word-break: break-all;">{confirmation_url}</a>
        </p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        
        <p style="font-size: 12px; color: #999;">
            Si vous n'avez pas créé de compte sur Vite & Gourmand, ignorez ce message.<br>
            Cet email a été envoyé automatiquement, merci de ne pas y répondre.
        </p>
    </div>
</body>
</html>
        """.strip()

    def send_equipment_return_reminder(self, user_email: str, user_name: str, order_id: int, event_date: str):
        """Email de rappel pour retour matériel"""
        subject = "Rappel : Retour du matériel prêté - Vite & Gourmand"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #D4AF37 0%, #C5A028 100%); 
                   color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
        .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Rappel Important</h1>
        </div>
        <div class="content">
            <p>Bonjour {user_name},</p>
            
            <p>Votre événement du <strong>{event_date}</strong> est terminé.</p>
            
            <p>Nous vous rappelons que vous avez emprunté du matériel lors de cette prestation 
            (commande n°{order_id}).</p>
            
            <p><strong>Merci de nous contacter pour organiser le retour du matériel dans les plus brefs délais.</strong></p>
            
            <p>📞 <strong>Téléphone :</strong> +33 6 12 34 56 78<br>
            📧 <strong>Email :</strong> contact@vite-et-gourmand.fr</p>
            
            <p>Nous vous remercions pour votre confiance et restons à votre disposition.</p>
            
            <p style="margin-top: 30px;">Cordialement,<br>
            <strong>L'équipe Vite & Gourmand</strong></p>
        </div>
        <div class="footer">
            <p>Vite & Gourmand - Traiteur événementiel<br>
            Cet email a été envoyé automatiquement, merci de ne pas y répondre directement.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return self._send_email(user_email, subject, html_content)

    def send_employee_welcome_email(self, email: str, firstname: str, lastname: str) -> bool:
        """
        Email de bienvenue pour un nouveau compte employé créé par l'administrateur.
        ⚠️ IMPORTANT : Le mot de passe n'est JAMAIS communiqué par email pour des raisons de sécurité.
        L'employé doit contacter l'administrateur José pour obtenir ses identifiants.
        """
        try:
            subject = "Bienvenue dans l'équipe Vite & Gourmand ! 🎉"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenue dans l'équipe</title>
</head>
<body style="font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #1A1A1A; margin: 0; padding: 0; background-color: #FAF9F6;">
    <div style="max-width: 600px; margin: 40px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.08);">
        
        <!-- Header Premium avec gradient doré -->
        <div style="background: linear-gradient(135deg, #D4AF37 0%, #C5A028 100%); padding: 40px 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">
                🎉 Bienvenue dans l'équipe !
            </h1>
            <p style="color: rgba(255,255,255,0.95); margin: 10px 0 0 0; font-size: 16px;">
                Vite & Gourmand - Traiteur événementiel haut de gamme
            </p>
        </div>
        
        <!-- Contenu -->
        <div style="padding: 40px 30px; background: #FAF9F6;">
            <p style="font-size: 18px; color: #1A1A1A; margin: 0 0 20px 0;">
                Bonjour <strong>{firstname} {lastname}</strong>,
            </p>
            
            <p style="font-size: 16px; color: #2C2C2C; line-height: 1.8; margin: 0 0 20px 0;">
                Nous sommes ravis de vous accueillir au sein de l'équipe <strong>Vite & Gourmand</strong> ! 
                Votre compte employé a été créé avec succès par notre administrateur.
            </p>
            
            <!-- Carte d'informations importante -->
            <div style="background: linear-gradient(135deg, rgba(212,175,55,0.08) 0%, rgba(197,160,40,0.12) 100%); 
                        border-left: 4px solid #D4AF37; 
                        border-radius: 12px; 
                        padding: 24px; 
                        margin: 30px 0;">
                <div style="display: flex; align-items: start;">
                    <div style="font-size: 28px; margin-right: 15px;">🔐</div>
                    <div>
                        <h3 style="margin: 0 0 12px 0; font-size: 18px; color: #1A1A1A; font-weight: 600;">
                            Informations de connexion
                        </h3>
                        <p style="margin: 0 0 12px 0; font-size: 15px; color: #2C2C2C; line-height: 1.6;">
                            <strong>Identifiant (email) :</strong><br>
                            <span style="background: white; padding: 8px 12px; border-radius: 6px; display: inline-block; margin-top: 6px; font-family: 'Courier New', monospace; color: #D4AF37; font-weight: 600;">
                                {email}
                            </span>
                        </p>
                        <p style="margin: 0; font-size: 14px; color: #8B4513; line-height: 1.6;">
                            ⚠️ <strong>Important pour votre sécurité :</strong><br>
                            Votre mot de passe temporaire ne vous a <strong>pas été envoyé par email</strong> pour des raisons de sécurité.
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Instructions claires -->
            <div style="background: white; 
                        border: 2px solid #E8E8E8; 
                        border-radius: 12px; 
                        padding: 24px; 
                        margin: 25px 0;">
                <h3 style="margin: 0 0 16px 0; font-size: 17px; color: #1A1A1A; font-weight: 600;">
                    📋 Prochaines étapes
                </h3>
                <ol style="margin: 0; padding-left: 20px; color: #2C2C2C; line-height: 1.9;">
                    <li style="margin-bottom: 10px; font-size: 15px;">
                        <strong>Contactez José</strong> (notre administrateur) pour obtenir votre mot de passe temporaire
                    </li>
                    <li style="margin-bottom: 10px; font-size: 15px;">
                        Connectez-vous à l'application avec votre email et le mot de passe fourni
                    </li>
                    <li style="margin-bottom: 10px; font-size: 15px;">
                        <strong>Modifiez immédiatement</strong> votre mot de passe pour des raisons de sécurité
                    </li>
                    <li style="font-size: 15px;">
                        Explorez votre espace employé et familiarisez-vous avec les fonctionnalités
                    </li>
                </ol>
            </div>
            
            <!-- Accès aux fonctionnalités -->
            <div style="margin: 25px 0;">
                <h3 style="margin: 0 0 16px 0; font-size: 17px; color: #1A1A1A; font-weight: 600;">
                    ✨ Vos accès employé
                </h3>
                <p style="margin: 0 0 12px 0; font-size: 15px; color: #2C2C2C; line-height: 1.8;">
                    En tant qu'<strong>employé</strong>, vous aurez accès à :
                </p>
                <ul style="margin: 0; padding-left: 20px; color: #2C2C2C; line-height: 1.9;">
                    <li style="margin-bottom: 8px; font-size: 15px;">📋 Gestion des menus et des plats</li>
                    <li style="margin-bottom: 8px; font-size: 15px;">🕐 Gestion des horaires d'ouverture</li>
                    <li style="margin-bottom: 8px; font-size: 15px;">📦 Suivi des commandes clients</li>
                    <li style="font-size: 15px;">👥 Gestion des demandes et réservations</li>
                </ul>
            </div>
            
            <!-- Contact -->
            <div style="background: linear-gradient(135deg, #2C2C2C 0%, #1A1A1A 100%); 
                        color: white; 
                        border-radius: 12px; 
                        padding: 24px; 
                        margin: 30px 0 0 0;">
                <h3 style="margin: 0 0 16px 0; font-size: 17px; color: #D4AF37; font-weight: 600;">
                    📞 Besoin d'aide ?
                </h3>
                <p style="margin: 0 0 12px 0; font-size: 15px; color: #FFFFFF; line-height: 1.7;">
                    <strong>José (Administrateur)</strong><br>
                    📧 jose@vite-et-gourmand.fr<br>
                    📱 +33 6 12 34 56 78
                </p>
                <p style="margin: 0; font-size: 14px; color: rgba(255,255,255,0.7); line-height: 1.6;">
                    N'hésitez pas à le contacter pour obtenir votre mot de passe ou si vous avez des questions.
                </p>
            </div>
            
            <!-- Message de bienvenue chaleureux -->
            <div style="text-align: center; margin: 35px 0 20px 0; padding: 25px; background: rgba(212,175,55,0.05); border-radius: 12px;">
                <p style="font-size: 16px; color: #2C2C2C; margin: 0 0 10px 0; line-height: 1.7;">
                    Nous sommes impatients de travailler avec vous pour offrir la meilleure expérience 
                    culinaire à nos clients ! 🍽️✨
                </p>
                <p style="font-size: 16px; color: #1A1A1A; margin: 0; font-weight: 600;">
                    Bienvenue dans la famille Vite & Gourmand ! 🎉
                </p>
            </div>
            
            <p style="margin: 25px 0 0 0; font-size: 15px; color: #2C2C2C;">
                Cordialement,<br>
                <strong style="color: #D4AF37;">L'équipe Vite & Gourmand</strong>
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background: #1A1A1A; padding: 25px 30px; text-align: center; border-top: 3px solid #D4AF37;">
            <p style="margin: 0 0 8px 0; font-size: 13px; color: rgba(255,255,255,0.7);">
                <strong style="color: #D4AF37;">Vite & Gourmand</strong> - Traiteur événementiel haut de gamme
            </p>
            <p style="margin: 0; font-size: 12px; color: rgba(255,255,255,0.5); line-height: 1.5;">
                📍 Paris, France | 📧 contact@vite-et-gourmand.fr | 📱 +33 6 12 34 56 78<br>
                Cet email a été envoyé automatiquement. Merci de ne pas y répondre directement.
            </p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            text_content = f"""
Bonjour {firstname} {lastname},

Nous sommes ravis de vous accueillir au sein de l'équipe Vite & Gourmand !

Votre compte employé a été créé avec succès par notre administrateur.

INFORMATIONS DE CONNEXION
==========================
Identifiant (email) : {email}

⚠️ IMPORTANT POUR VOTRE SÉCURITÉ :
Votre mot de passe temporaire ne vous a PAS été envoyé par email pour des raisons de sécurité.

PROCHAINES ÉTAPES
==================
1. Contactez José (notre administrateur) pour obtenir votre mot de passe temporaire
2. Connectez-vous à l'application avec votre email et le mot de passe fourni
3. Modifiez immédiatement votre mot de passe pour des raisons de sécurité
4. Explorez votre espace employé et familiarisez-vous avec les fonctionnalités

VOS ACCÈS EMPLOYÉ
==================
En tant qu'employé, vous aurez accès à :
- Gestion des menus et des plats
- Gestion des horaires d'ouverture
- Suivi des commandes clients
- Gestion des demandes et réservations

BESOIN D'AIDE ?
===============
José (Administrateur)
Email : jose@vite-et-gourmand.fr
Téléphone : +33 6 12 34 56 78

N'hésitez pas à le contacter pour obtenir votre mot de passe ou si vous avez des questions.

Nous sommes impatients de travailler avec vous pour offrir la meilleure expérience 
culinaire à nos clients !

Bienvenue dans la famille Vite & Gourmand ! 🎉

Cordialement,
L'équipe Vite & Gourmand

---
Vite & Gourmand - Traiteur événementiel haut de gamme
Paris, France | contact@vite-et-gourmand.fr | +33 6 12 34 56 78
Cet email a été envoyé automatiquement. Merci de ne pas y répondre directement.
            """.strip()
            
            return self._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bienvenue employé: {e}")
            return False



    def send_order_confirmation_email(
        self,
        user_email: str,
        user_name: str,
        order_id: int,
        menu_title: str,
        event_date: str,
        event_time: str,
        people_count: int,
        total_price: float,
        delivery_city: str,
    ) -> bool:
        """Envoie un email de confirmation de commande"""
        subject = f"✅ Commande #{order_id} confirmée - Vite & Gourmand"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #D4AF37; text-align: center;">🎉 Commande confirmée !</h1>
                
                <p>Bonjour <strong>{user_name}</strong>,</p>
                
                <p>Merci pour votre confiance ! Nous avons bien reçu votre commande.</p>
                
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h2 style="color: #D4AF37; margin-top: 0;">📋 Récapitulatif</h2>
                    <p><strong>Numéro de commande :</strong> #{order_id}</p>
                    <p><strong>Menu :</strong> {menu_title}</p>
                    <p><strong>Date de l'événement :</strong> {event_date}</p>
                    <p><strong>Heure :</strong> {event_time}</p>
                    <p><strong>Nombre d'invités :</strong> {people_count} personnes</p>
                    <p><strong>Lieu de livraison :</strong> {delivery_city}</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 15px 0;">
                    <p style="font-size: 18px; color: #D4AF37;"><strong>Total estimé : {total_price:.2f}€</strong></p>
                </div>
                
                <h3 style="color: #D4AF37;">🔔 Prochaines étapes</h3>
                <ol style="padding-left: 20px;">
                    <li>Notre équipe examine votre demande sous 24-48h</li>
                    <li>Nous vous contacterons pour confirmer les détails</li>
                    <li>Vous recevrez une notification à chaque étape</li>
                </ol>
                
                <div style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #1565C0; margin: 20px 0;">
                    <p style="margin: 0;">💡 <strong>Besoin d'aide ?</strong><br>
                    Répondez à cet email ou contactez-nous au <strong>05 56 XX XX XX</strong></p>
                </div>
                
                <p style="text-align: center; color: #666; margin-top: 30px;">
                    Merci de faire confiance à <strong style="color: #D4AF37;">Vite & Gourmand</strong> !<br>
                    <em>L'excellence culinaire pour vos événements</em>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, body)


    def send_order_completed_email(
        self,
        user_email: str,
        user_name: str,
        order_id: int,
        menu_title: str,
    ) -> bool:
        """Envoie un email quand la commande est terminée (invitation à laisser un avis)"""
        subject = f"🎉 Commande #{order_id} terminée - Votre avis compte !"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2E7D32; text-align: center;">✨ Merci pour votre confiance !</h1>
                
                <p>Bonjour <strong>{user_name}</strong>,</p>
                
                <p>Votre commande <strong>#{order_id}</strong> pour le menu <em>"{menu_title}"</em> est maintenant terminée.</p>
                
                <p>Nous espérons que vous avez apprécié nos prestations et que votre événement a été une réussite ! 🎊</p>
                
                <div style="background-color: #f0f8f0; padding: 20px; border-radius: 8px; margin: 25px 0; text-align: center;">
                    <h2 style="color: #2E7D32; margin-top: 0;">⭐ Votre avis compte !</h2>
                    <p>Partagez votre expérience avec la communauté et aidez-nous à nous améliorer.</p>
                    <p style="margin: 20px 0;">
                        <a href="https://votreapp.com/orders/{order_id}/review" 
                           style="display: inline-block; padding: 12px 30px; background-color: #D4AF37; color: white; 
                                  text-decoration: none; border-radius: 6px; font-weight: bold;">
                            ✍️ Laisser un avis
                        </a>
                    </p>
                    <p style="font-size: 13px; color: #666;">
                        Votre avis sera publié après validation par notre équipe
                    </p>
                </div>
                
                <div style="background-color: #fff8e1; padding: 15px; border-left: 4px solid #D4AF37; margin: 20px 0;">
                    <p style="margin: 0;">💬 <strong>Une question ? Un souci ?</strong><br>
                    Notre service client est à votre écoute : <a href="mailto:contact@vitegourmand.fr">contact@vitegourmand.fr</a></p>
                </div>
                
                <p style="text-align: center; color: #666; margin-top: 30px;">
                    À très bientôt pour votre prochain événement !<br>
                    <strong style="color: #D4AF37;">L'équipe Vite & Gourmand</strong>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, body)


    def send_password_reset_email(
        self,
        user_email: str,
        user_name: str,
        reset_token: str,
        frontend_url: str = None,
    ) -> bool:
        """Envoie un email de réinitialisation de mot de passe
        
        Args:
            user_email: Email du destinataire
            user_name: Nom de l'utilisateur
            reset_token: Token JWT de réinitialisation
            frontend_url: URL du frontend (optionnel, utilise deep link par défaut)
        """
        # Utiliser le deep link pour l'app mobile ou l'URL web si fournie
        if frontend_url:
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        else:
            # Deep link pour l'application mobile
            reset_link = f"vitegourmand://reset-password?token={reset_token}"
        
        subject = "🔐 Réinitialisation de votre mot de passe - Vite & Gourmand"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #1565C0; text-align: center;">🔐 Réinitialisation mot de passe</h1>
                
                <p>Bonjour <strong>{user_name}</strong>,</p>
                
                <p>Vous avez demandé à réinitialiser votre mot de passe sur <strong>Vite & Gourmand</strong>.</p>
                
                <div style="background-color: #e8f4f8; padding: 20px; border-radius: 8px; margin: 25px 0; text-align: center;">
                    <p style="margin: 20px 0;">Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
                    <p style="margin: 20px 0;">
                        <a href="{reset_link}" 
                           style="display: inline-block; padding: 12px 30px; background-color: #D4AF37; color: white; 
                                  text-decoration: none; border-radius: 6px; font-weight: bold;">
                            Réinitialiser mon mot de passe
                        </a>
                    </p>
                    <p style="font-size: 13px; color: #666;">
                        ⏱️ Ce lien est valide pendant <strong>1 heure</strong>
                    </p>
                </div>
                
                <div style="background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0;">
                    <p style="margin: 0;">⚠️ <strong>Si vous n'avez pas demandé cette réinitialisation :</strong><br>
                    Ignorez cet email. Votre mot de passe actuel reste inchangé.<br>
                    Contactez-nous si vous pensez qu'il y a un problème de sécurité.</p>
                </div>
                
                <p style="font-size: 12px; color: #999; margin-top: 30px;">
                    <strong>Lien alternatif :</strong> Si le bouton ne fonctionne pas, copiez-collez ce lien :<br>
                    <a href="{reset_link}" style="color: #1565C0; word-break: break-all;">{reset_link}</a>
                </p>
                
                <p style="text-align: center; color: #666; margin-top: 30px;">
                    <strong style="color: #D4AF37;">L'équipe Vite & Gourmand</strong><br>
                    <em>Votre sécurité est notre priorité</em>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, body)




# Instance globale
email_service = EmailService()