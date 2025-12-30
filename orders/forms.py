from django import forms
from .models import Address
from django.utils.safestring import mark_safe
import pycountry
import phonenumbers
import re

class PhoneNumberWidget(forms.MultiWidget):
    """Custom widget for phone number with country code and area code."""
    
    def __init__(self, attrs=None):
        # Get country codes with dialing prefixes
        country_choices = [('', '-- Select Country --')]
        for country in sorted(pycountry.countries, key=lambda x: x.name):
            try:
                # Try to get the dialing code
                phone_code = phonenumbers.country_code_for_region(country.alpha_2)
                if phone_code:
                    country_choices.append(
                        (country.alpha_2, f"{country.name} (+{phone_code})")
                    )
            except:
                country_choices.append((country.alpha_2, country.name))
        
        widgets = (
            forms.Select(
                choices=country_choices,
                attrs={'class': 'form-control form-select', 'id': 'id_phone_country'}
            ),
            forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number',
                'id': 'id_phone_number'
            })
        )
        super().__init__(widgets, attrs)
    
    def decompress(self, value):
        """Split phone number into country code and number."""
        if value:
            try:
                parsed = phonenumbers.parse(value, None)
                country_code = phonenumbers.region_code_for_number(parsed)
                national_number = str(parsed.national_number)
                return [country_code, national_number]
            except:
                return [None, value]
        return [None, None]

class CheckoutForm(forms.ModelForm):
    # Override phone field to use custom MultiWidget
    phone = forms.CharField(widget=PhoneNumberWidget(), required=True)
    
    class Meta:
        model = Address
        fields = ['full_name', 'line1', 'line2', 'city', 'state', 'postcode', 'country', 'phone']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province'}),
            'postcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'country': forms.Select(attrs={'class': 'form-control form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add suggestion text below each field
        suggestions = {
            'full_name': 'Enter your full legal name as it appears on official documents',
            'line1': 'Street address, P.O. box, company name',
            'line2': 'Apartment, suite, unit, building, floor, etc.',
            'city': 'Enter your city name',
            'state': 'Enter your state, province, or region',
            'postcode': 'Enter your postal or ZIP code',
            'country': 'Select your country from the list',
            'phone': 'Include country code (e.g., +234 for Nigeria, +1 for USA)'
        }
        
        for field_name, suggestion in suggestions.items():
            self.fields[field_name].help_text = mark_safe(f'<small class="text-muted">{suggestion}</small>')
        
        # Setup country dropdown with pycountry
        country_choices = [(country.alpha_2, country.name) for country in pycountry.countries]
        self.fields['country'] = forms.ChoiceField(
            choices=[('', 'Select Country')] + country_choices,
            widget=forms.Select(attrs={'class': 'form-control'}),
            help_text=self.fields['country'].help_text
        )

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if not full_name:
            raise forms.ValidationError("Full name is required.")
        if len(full_name) < 2:
            raise forms.ValidationError("Full name must be at least 2 characters long.")
        return full_name

    def clean_postcode(self):
        postcode = self.cleaned_data.get('postcode', '').strip()
        if not postcode:
            raise forms.ValidationError("Postal code is required.")
        if not re.match(r'^[A-Za-z0-9\s\-]{2,20}$', postcode):
            raise forms.ValidationError("Postal code format is invalid.")
        return postcode

    def clean_phone(self):
        """Validate phone number using phonenumbers library."""
        phone_data = self.cleaned_data.get('phone')
        
        # phone_data comes from MultiWidget as [country_code, number]
        if isinstance(phone_data, list):
            country_code, phone_number = phone_data[0], phone_data[1]
        else:
            # Fallback for non-widget form data
            country_code = self.cleaned_data.get('country', '').strip()
            phone_number = phone_data if isinstance(phone_data, str) else ''
        
        phone_number = (phone_number or '').strip()
        
        if not phone_number:
            raise forms.ValidationError("Phone number is required.")
        
        # Try to parse the phone number with the selected country
        try:
            if country_code:
                # Parse with country code
                parsed_number = phonenumbers.parse(phone_number, country_code)
            else:
                # Try to parse as international format
                parsed_number = phonenumbers.parse(phone_number, None)
            
            # Validate the parsed number
            if not phonenumbers.is_valid_number(parsed_number):
                raise forms.ValidationError("Phone number is invalid for the selected country.")
            
            # Return formatted number (E.164 format)
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        
        except phonenumbers.NumberParseException as e:
            raise forms.ValidationError(f"Phone number format is invalid: {str(e)}")

    def clean_country(self):
        country = self.cleaned_data.get('country', '').strip()
        if not country:
            raise forms.ValidationError("Country is required.")
        
        # Verify country code exists in pycountry
        try:
            pycountry.countries.get(alpha_2=country)
        except KeyError:
            raise forms.ValidationError("Invalid country code selected.")
        
        return country
    
    def clean_state(self):
        """Clean and validate state/province."""
        state = self.cleaned_data.get('state', '').strip()
        country = self.cleaned_data.get('country', '')
        
        if not state:
            raise forms.ValidationError("State/Province is required.")
        
        # Optional: Validate against pycountry subdivisions if country is provided
        if country:
            try:
                # Get subdivisions for the selected country
                subdivisions = pycountry.subdivisions.get(country_code=country)
                valid_subdivisions = [s.name for s in subdivisions]
                # Note: We allow free text for now, but could enforce list
            except KeyError:
                pass  # Country doesn't have subdivisions in pycountry
        
        return state
    
    def clean_city(self):
        """Clean and validate city."""
        city = self.cleaned_data.get('city', '').strip()
        if not city:
            raise forms.ValidationError("City is required.")
        if len(city) < 2:
            raise forms.ValidationError("City name must be at least 2 characters long.")
        return city
    
    def clean_line1(self):
        """Clean and validate address line 1."""
        line1 = self.cleaned_data.get('line1', '').strip()
        if not line1:
            raise forms.ValidationError("Address is required.")
        if len(line1) < 5:
            raise forms.ValidationError("Address must be at least 5 characters long.")
        return line1