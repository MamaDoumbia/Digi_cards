import string
import random
from django.db import models
from django.urls import reverse
from django.core.validators import URLValidator


def generate_unique_code():
    """Génère un code unique de 8 caractères alphanumériques"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Client.objects.filter(code_unique=code).exists():
            return code


class Client(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom du client")
    code_unique = models.CharField(
        max_length=8,
        unique=True,
        default=generate_unique_code,
        verbose_name="Code unique",
        editable=False
    )
    actif = models.BooleanField(default=True, verbose_name="Profil actif")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} ({self.code_unique})"

    def get_public_url(self):
        return reverse('liens:profil_public', kwargs={'code_unique': self.code_unique})

    def get_absolute_url(self):
        return reverse('liens:client_detail', kwargs={'pk': self.pk})

    @property
    def liens_count(self):
        return self.lien_set.count()


class Lien(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Client")
    titre = models.CharField(max_length=100, verbose_name="Titre du lien")
    url = models.CharField(max_length=500, verbose_name="URL")
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lien"
        verbose_name_plural = "Liens"
        ordering = ['ordre', 'date_creation']

    def __str__(self):
        return f"{self.titre} - {self.client.nom}"

    def get_icon(self):
        """Retourne l'icône appropriée basée sur l'URL"""
        url_lower = self.url.lower()

        if 'linkedin.com' in url_lower:
            return 'liens/icons/linkedin.png'
        elif 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'liens/icons/facebook.png'
        elif 'tiktok.com' in url_lower:
            return 'liens/icons/tik-tok.png'
        elif 'whatsapp.com' in url_lower or 'wa.me' in url_lower:
            return 'liens/icons/whatsapp.png'
        elif 'instagram.com' in url_lower:
            return 'liens/icons/instagram.png'
        elif 'snapchat.com' in url_lower or 'snap.com' in url_lower or 'snapchat' in url_lower:
            return 'liens/icons/snapchat.png'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'liens/icons/twitter.png'
        elif 'telegram.org' in url_lower or 't.me' in url_lower or 'telegram.me' in url_lower:
            return 'liens/icons/telegram.png'
        elif url_lower.startswith('mailto:') and ('@gmail.com' in url_lower or '@googlemail.com' in url_lower):
            return 'liens/icons/gmail.png'
        elif url_lower.startswith('mailto:') and any(
                domain in url_lower for domain in ['@outlook.com', '@hotmail.com', '@live.com', '@msn.com']):
            return 'liens/icons/outlook.png'
        elif url_lower.startswith('mailto:') and any(
                domain in url_lower for domain in ['@yahoo.com', '@yahoo.fr', '@ymail.com', '@rocketmail.com']):
            return 'liens/icons/yahoo.png'
        elif 'gmail.com' in url_lower or 'mail.google.com' in url_lower:
            return 'liens/icons/gmail.png'
        elif 'outlook.com' in url_lower or 'hotmail.com' in url_lower or 'live.com' in url_lower or 'office.com' in url_lower:
            return 'liens/icons/outlook.png'
        elif 'yahoo.com' in url_lower or 'yahoo.fr' in url_lower or 'ymail.com' in url_lower:
            return 'liens/icons/yahoo.png'
        else:
            return None

    def get_platform_name(self):
        """Retourne le nom de la plateforme basé sur l'URL"""
        url_lower = self.url.lower()

        # Gestion des liens mailto:
        if url_lower.startswith('mailto:'):
            # Extraire l'adresse email
            email_part = url_lower.replace('mailto:', '')
            email_address = email_part.strip()

            if '@gmail.com' in email_address or '@googlemail.com' in email_address:
                return 'Gmail'
            elif any(domain in email_address for domain in ['@outlook.com', '@hotmail.com', '@live.com', '@msn.com']):
                return 'Outlook'
            elif any(
                    domain in email_address for domain in ['@yahoo.com', '@yahoo.fr', '@ymail.com', '@rocketmail.com']):
                return 'Yahoo Mail'
            else:
                return 'Email'

        if 'linkedin.com' in url_lower:
            return 'LinkedIn'
        elif 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'Facebook'
        elif 'tiktok.com' in url_lower:
            return 'TikTok'
        elif 'whatsapp.com' in url_lower or 'wa.me' in url_lower:
            return 'WhatsApp'
        elif 'instagram.com' in url_lower:
            return 'Instagram'
        elif 'snapchat.com' in url_lower or 'snap.com' in url_lower or 'snapchat' in url_lower:
            return 'Snapchat'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'Twitter/X'
        elif 'telegram.org' in url_lower or 't.me' in url_lower or 'telegram.me' in url_lower:
            return 'Telegram'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'YouTube'
        else:
            return 'Site web'

    def get_profile_username(self):
        """Extrait le nom d'utilisateur ou l'ID du profil depuis l'URL"""
        import re
        url = self.url.lower()

        # Gestion des liens mailto:
        if url.startswith('mailto:'):
            # Extraire l'adresse email
            email_part = url.replace('mailto:', '')
            email_address = email_part.strip()
            return email_address

        # Instagram
        elif 'instagram.com' in url:
            match = re.search(r'instagram\.com/([^/?]+)', url)
            if match:
                username = match.group(1)
                if username not in ['p', 'reel', 'tv', 'stories']:
                    return f"@{username}"

        # TikTok
        elif 'tiktok.com' in url:
            match = re.search(r'tiktok\.com/@([^/?]+)', url)
            if match:
                return f"@{match.group(1)}"

        # Facebook
        elif 'facebook.com' in url or 'fb.com' in url:
            # Facebook pages ou profils
            match = re.search(r'(?:facebook\.com|fb\.com)/([^/?]+)', url)
            if match:
                username = match.group(1)
                if username not in ['pages', 'groups', 'events', 'profile.php']:
                    return username

        # LinkedIn
        elif 'linkedin.com' in url:
            # LinkedIn profils
            match = re.search(r'linkedin\.com/in/([^/?]+)', url)
            if match:
                return match.group(1)
            # LinkedIn entreprises
            match = re.search(r'linkedin\.com/company/([^/?]+)', url)
            if match:
                return match.group(1)

        # Snapchat
        elif 'snapchat.com' in url or 'snap.com' in url:
            match = re.search(r'(?:snapchat\.com/add/|snap\.com/)([^/?]+)', url)
            if match:
                return f"@{match.group(1)}"

        # Twitter/X
        elif 'twitter.com' in url or 'x.com' in url:
            match = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', url)
            if match:
                username = match.group(1)
                if username not in ['i', 'home', 'explore', 'notifications']:
                    return f"@{username}"

        # YouTube
        elif 'youtube.com' in url:
            # Canal YouTube
            match = re.search(r'youtube\.com/(?:c/|channel/|user/|@)([^/?]+)', url)
            if match:
                username = match.group(1)
                return f"@{username}" if not username.startswith('@') else username

        # WhatsApp
        elif 'wa.me' in url:
            match = re.search(r'wa\.me/(\d+)', url)
            if match:
                return match.group(1)

        # Telegram
        elif 't.me' in url or 'telegram.me' in url:
            match = re.search(r'(?:t\.me|telegram\.me)/([^/?]+)', url)
            if match:
                username = match.group(1)
                if username not in ['joinchat', 'addstickers', 's']:
                    return f"@{username}"

        # Gmail
        elif 'gmail.com' in url or 'mail.google.com' in url:
            # Extraire l'adresse email si présente dans l'URL
            match = re.search(r'mailto:([^?&]+)', url)
            if match:
                return match.group(1)

        # Outlook/Hotmail
        elif 'outlook.com' in url or 'hotmail.com' in url or 'live.com' in url:
            # Extraire l'adresse email si présente dans l'URL
            match = re.search(r'mailto:([^?&]+)', url)
            if match:
                return match.group(1)

        # Yahoo Mail
        elif 'yahoo.com' in url or 'yahoo.fr' in url or 'ymail.com' in url:
            # Extraire l'adresse email si présente dans l'URL
            match = re.search(r'mailto:([^?&]+)', url)
            if match:
                return match.group(1)

        return None