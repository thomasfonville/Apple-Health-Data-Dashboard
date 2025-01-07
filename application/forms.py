from django import forms
from django.forms import DateInput
from .models import RunningWorkoutData
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


class UploadFileForm(forms.Form):
    exportXML = forms.FileField(required=False)
    exportGPX = forms.FileField(required=False)


class WorkoutFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'format': 'M. d, Y, g:i a'}))
    end_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date', 'format': 'M. d, Y, g:i a'}))
    min_distance = forms.CharField(required=False)
    min_duration = forms.CharField(required=False)
    min_cals_burned = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(WorkoutFilterForm, self).__init__(*args, **kwargs)
        
        # Get the distinct years from the workout data
        years = RunningWorkoutData.objects.dates('start_date', 'year').distinct()
        year_choices = [(year.year, year.year) for year in years]
        year_choices.insert(0, ('', '----'))  # Add a blank option
        
        self.fields['year'] = forms.ChoiceField(choices=year_choices, required=False, label="Year")

        # Add month choices
        month_choices = [
            ('', '----'),
            (1, 'January'),
            (2, 'February'),
            (3, 'March'),
            (4, 'April'),
            (5, 'May'),
            (6, 'June'),
            (7, 'July'),
            (8, 'August'),
            (9, 'September'),
            (10, 'October'),
            (11, 'November'),
            (12, 'December'),
        ]

        self.fields['month'] = forms.ChoiceField(choices=month_choices, required=False, label="Month")

    DISTANCE_CHOICES = (
        ('', 'Select distance'),
        ('5k', '5k'),
        ('10k', '10k'),
        ('half_marathon', 'Half Marathon'),
        ('marathon', 'Marathon'),
    )
    
    distance_range = forms.ChoiceField(choices=DISTANCE_CHOICES, required=False, label='Distance Range')


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
    

class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=64)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)