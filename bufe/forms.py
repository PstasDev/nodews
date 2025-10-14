from django import forms
from django.core.validators import MinValueValidator
from .models import Rendeles, Termek
import json


class OrderItemForm(forms.Form):
    """Form for a single order item"""
    termek_id = forms.IntegerField(widget=forms.HiddenInput())
    mennyiseg = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
        }),
        label='Mennyiség'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        termek_id = cleaned_data.get('termek_id')
        mennyiseg = cleaned_data.get('mennyiseg')
        
        if termek_id:
            try:
                termek = Termek.objects.get(id=termek_id)
                if not termek.elerheto:
                    raise forms.ValidationError(f"{termek.nev} már nem elérhető.")
                if mennyiseg > termek.max_rendelesenkent:
                    raise forms.ValidationError(
                        f"Maximum {termek.max_rendelesenkent} darab rendelhető ebből a termékből."
                    )
            except Termek.DoesNotExist:
                raise forms.ValidationError("A kiválasztott termék nem található.")
        
        return cleaned_data


class RendelesForm(forms.ModelForm):
    """Form for creating an order"""
    
    BREAK_CHOICES = [
        ('', '--- Válasszon szünetet ---'),
        ('09:10', '1. óra utáni szünet (9:10)'),
        ('10:05', '3. óra utáni szünet (10:05)'),
        ('11:05', '4. óra utáni szünet (11:05)'),
        ('12:00', '5. óra utáni szünet (12:00)'),
        ('13:05', '6. óra utáni szünet (13:05)'),
        ('14:10', '7. óra utáni szünet (14:10)'),
    ]
    
    szunet_valasztas = forms.ChoiceField(
        choices=BREAK_CHOICES,
        required=False,
        label='Szünet választása',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Válasszon a szünetek közül, vagy adjon meg egyedi időpontot alább'
    )
    
    class Meta:
        model = Rendeles
        fields = ['idozitve', 'megjegyzes']
        widgets = {
            'idozitve': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'megjegyzes': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'form-control',
                    'placeholder': 'Opcionális megjegyzés a rendeléshez...'
                }
            ),
        }
        labels = {
            'idozitve': 'Időzítés (kötelező)',
            'megjegyzes': 'Megjegyzés (opcionális)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['idozitve'].required = True
        self.fields['megjegyzes'].required = False
        # Reorder fields to show break selection first
        self.order_fields(['szunet_valasztas', 'idozitve', 'megjegyzes'])
    
    def clean(self):
        """Validate form data"""
        from datetime import datetime, timedelta
        
        cleaned_data = super().clean()
        szunet_valasztas = cleaned_data.get('szunet_valasztas')
        idozitve = cleaned_data.get('idozitve')
        
        # If break is selected, convert it to datetime
        if szunet_valasztas:
            now = datetime.now()
            break_time = datetime.strptime(szunet_valasztas, '%H:%M').time()
            
            # Combine with today's date
            scheduled_datetime = datetime.combine(now.date(), break_time)
            
            # If the time has already passed today, schedule for tomorrow
            if scheduled_datetime < now + timedelta(minutes=10):
                scheduled_datetime += timedelta(days=1)
            
            cleaned_data['idozitve'] = scheduled_datetime
        
        return cleaned_data
    
    def clean_idozitve(self):
        """Validate scheduled time"""
        from datetime import datetime, timedelta
        
        idozitve = self.cleaned_data.get('idozitve')
        
        if idozitve:
            # Must be at least 10 minutes in the future
            min_time = datetime.now() + timedelta(minutes=10)
            if idozitve < min_time:
                raise forms.ValidationError(
                    "Az időzítésnek legalább 10 perccel a rendelés leadása után kell lennie."
                )
        
        return idozitve
