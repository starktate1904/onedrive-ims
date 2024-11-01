# forms.py
from django import forms

class SaleFilterForm(forms.Form):
    search = forms.CharField(required=False)
    date_filter = forms.ChoiceField(required=False, choices=[
        ('', 'All dates'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This week'),
        ('last_week', 'Last week'),
    ])
    money_filter = forms.ChoiceField(required=False, choices=[
        ('', 'All amounts'),
        ('high_to_low', 'High to low'),
        ('low_to_high', 'Low to high'),
    ])