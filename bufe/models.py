from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


def get_full_name(self):
    """
    Returns the user's full name with last name first, then first name.
    """
    return f"{self.last_name} {self.first_name}"

User.get_full_name = get_full_name

class Bufe(models.Model):
    """
    Búfé - Uniobject model
    Represents the cafeteria/buffet with opening hours and availability
    """
    nev = models.CharField(max_length=100, default="Iskolai Büfé")
    rendkivuli_zarva = models.BooleanField(default=False, verbose_name="Rendkívüli zárva")
    bufeadmin = models.ManyToManyField(
        User,
        related_name='managed_bufes',
        blank=True,
        verbose_name="Büfé adminisztrátorok",
        help_text="Felhasználók, akik kezelhetik a büfé rendeléseit"
    )
    
    class Meta:
        verbose_name = "Büfé"
        verbose_name_plural = "Büfék"

    def __save__(self, *args, **kwargs):
        # Ensure only one Bufe instance exists
        if not self.pk and Bufe.objects.exists():
            raise ValueError("Csak egy Büfé példány létezhet.")
        
        nyitvatartasi_idok = self.opening_hours.all()
        for nap in range(7):
            if not nyitvatartasi_idok.filter(weekday=nap).exists():
                # add default opening hours
                OpeningHours.objects.create(bufe=self, weekday=nap)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nev
    
    def is_open_now(self):
        """Check if the buffet is currently open"""
        if self.rendkivuli_zarva:
            return False
        
        now = timezone.now()
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.time()
        
        opening_hours = self.opening_hours.filter(
            weekday=current_weekday,
            from_hour__lte=current_time,
            to_hour__gte=current_time
        )
        
        return opening_hours.exists()


class OpeningHours(models.Model):
    """
    Opening hours for the buffet
    Multiple entries can exist for the same weekday
    """
    WEEKDAY_CHOICES = [
        (0, 'Hétfő'),
        (1, 'Kedd'),
        (2, 'Szerda'),
        (3, 'Csütörtök'),
        (4, 'Péntek'),
        (5, 'Szombat'),
        (6, 'Vasárnap'),
    ]
    
    bufe = models.ForeignKey(
        Bufe, 
        on_delete=models.CASCADE, 
        related_name='opening_hours',
        verbose_name="Büfé"
    )
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, verbose_name="Hét napja")
    from_hour = models.TimeField(verbose_name="Nyitás")
    to_hour = models.TimeField(verbose_name="Zárás")
    
    class Meta:
        verbose_name = "Nyitvatartás"
        verbose_name_plural = "Nyitvatartások"
        ordering = ['weekday', 'from_hour']
    
    def __str__(self):
        return f"{self.get_weekday_display()}: {self.from_hour} - {self.to_hour}"
    
    def is_closed(self):
        """Check if this represents a closed period (both times null or blank)"""
        return self.from_hour is None or self.to_hour is None


class Kategoria(models.Model):
    """
    Product category model
    """
    nev = models.CharField(max_length=100, verbose_name="Név")
    bufe = models.ForeignKey(
        Bufe, 
        on_delete=models.CASCADE, 
        related_name='kategoriak',
        verbose_name="Büfé"
    )
    
    class Meta:
        verbose_name = "Kategória"
        verbose_name_plural = "Kategóriák"
        ordering = ['nev']
    
    def __str__(self):
        return self.nev


class Termek(models.Model):
    """
    Product model for buffet items
    """
    nev = models.CharField(max_length=200, verbose_name="Név")
    kategoria = models.ForeignKey(
        Kategoria, 
        on_delete=models.CASCADE, 
        related_name='termekek',
        verbose_name="Kategória"
    )
    ar = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Ár (Ft)"
    )
    max_rendelesenkent = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Max rendelésenkénti mennyiség"
    )
    hutve = models.BooleanField(default=False, verbose_name="Hűtve")
    elerheto = models.BooleanField(default=True, verbose_name="Elérhető")
    kisult = models.BooleanField(default=False, verbose_name="Kisült")
    
    class Meta:
        verbose_name = "Termék"
        verbose_name_plural = "Termékek"
        ordering = ['kategoria', 'nev']
    
    def __str__(self):
        return f"{self.nev} - {self.ar} Ft"


class Rendeles(models.Model):
    """
    Order model
    Stores orders with items in JSON format and tracks order states
    """
    ORDER_STATES = [
        ('leadva', 'Rendelés leadva'),
        ('visszavonva', 'Rendelés visszavonva'),
        ('visszaigasolva', 'Rendelés visszaigazolva'),
        ('torolve', 'Rendelés törölve'),
        ('atadva', 'Rendelés átadva'),
    ]
    
    # JSONField format: [{"termek_id": 1, "db": 2}, ...]
    items = models.JSONField(
        verbose_name="Tételek",
        help_text="Rendelés tételei JSON formátumban"
    )
    allapot = models.CharField(
        max_length=20,
        choices=ORDER_STATES,
        default='leadva',
        verbose_name="Állapot"
    )
    leadva = models.DateTimeField(auto_now_add=True, verbose_name="Rendelés leadva")
    idozitve = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Időzítés",
        help_text="Időzítés - nyitvatartási időben csak, min. 10 perccel a rendelés leadása után"
    )
    megjegyzes = models.TextField(blank=True, verbose_name="Megjegyzés")
    archived = models.BooleanField(default=False, verbose_name="Archivált")
    vegosszeg = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Végösszeg (Ft)"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rendelesek',
        verbose_name="Felhasználó"
    )
    
    class Meta:
        verbose_name = "Rendelés"
        verbose_name_plural = "Rendelések"
        ordering = ['-leadva']
    
    def __str__(self):
        return f"Rendelés #{self.id} - {self.user.username} - {self.vegosszeg} Ft"
    
    def calculate_total(self):
        """Calculate total price from items"""
        total = 0
        for item in self.items:
            try:
                termek = Termek.objects.get(id=item['termek_id'])
                total += termek.ar * item['db']
            except Termek.DoesNotExist:
                pass
        return total
    
    def save(self, *args, **kwargs):
        # Auto-calculate vegosszeg if not set
        if self.vegosszeg == 0:
            self.vegosszeg = self.calculate_total()
        super().save(*args, **kwargs)

# Chatfunkció - később lesz implementálva
# class Chatszoba(models.Model):
#     """
#     Chat room model - linked to orders
#     Users can communicate about their orders through messages
#     """
#     rendeles = models.OneToOneField(
#         Rendeles,
#         on_delete=models.CASCADE,
#         related_name='chatszoba',
#         verbose_name="Rendelés"
#     )
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name="Létrehozva")
    
#     class Meta:
#         verbose_name = "Chatszoba"
#         verbose_name_plural = "Chatszobák"
    
#     def __str__(self):
#         return f"Chatszoba - Rendelés #{self.rendeles.id}"


# class Uzenet(models.Model):
#     """
#     Message model for chat rooms
#     """
#     chatszoba = models.ForeignKey(
#         Chatszoba,
#         on_delete=models.CASCADE,
#         related_name='uzenetek',
#         verbose_name="Chatszoba"
#     )
#     szerzo = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         verbose_name="Szerző"
#     )
#     sent = models.DateTimeField(auto_now_add=True, verbose_name="Elküldve")
#     uzenet = models.TextField(max_length=1000, verbose_name="Üzenet")
    
#     class Meta:
#         verbose_name = "Üzenet"
#         verbose_name_plural = "Üzenetek"
#         ordering = ['sent']
    
#     def __str__(self):
#         return f"{self.szerzo.username}: {self.uzenet[:50]}"
