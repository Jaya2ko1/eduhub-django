from django import forms
from .models import Lesson,Course
from django.contrib.auth import get_user_model

User = get_user_model()


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = "__all__"
        widgets = {
            'title' : forms.TextInput(attrs={'class':'form-control'}),
            'course':forms.Select(attrs={'class':'form-select'}),
            'instructor':forms.Select(attrs={'class':'form-select'}),
            'lesson_type':forms.Select(attrs={'class':'form-select'}),
            'content': forms.Textarea(attrs={'class':'form-control'}),
            'video_url':forms.TextInput(attrs={'class':'form-control'}),
            'pdf_file' : forms.FileInput(attrs={'class':'form-control'}),
            'order_number': forms.NumberInput(attrs={'class':'form-control'}),
            'status' : forms.Select(attrs={'class':'form-select'}),
        }

    def __init__(self, *args, user=None,**kwargs):
        super().__init__(*args, **kwargs)

        if user:
            if user.role == user.TEACHER:
                self.fields['course'].queryset = Course.objects.filter(instructor=user)
                self.fields['instructor'].queryset = User.objects.filter(username=user)
            else:
                self.fields['course'].queryset = Course.objects.all()
