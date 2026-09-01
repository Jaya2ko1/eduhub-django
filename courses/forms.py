from django import forms
from .models import Course
from django.contrib.auth import get_user_model


User = get_user_model()

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = "__all__"
        widgets = {
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'full_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), 
        }

    def __init__(self, *args, user=None,**kwargs):
        super().__init__(*args, **kwargs)
        if user:
            if user.role == user.TEACHER:
            
                self.fields["instructor"].queryset = User.objects.filter(id=user.id)
                
            else:
                self.fields["instructor"].queryset = User.objects.filter(role="teacher")
            
