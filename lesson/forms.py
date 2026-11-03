from django import forms
from django.core.validators import FileExtensionValidator
from .models import Lesson,Course
from django.contrib.auth import get_user_model

User = get_user_model()


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "course",
            "title",
            "lesson_type",
            "content",
            "video_url",
            "pdf_file",
            "order_number",
            "status",
        ]
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
        self.fields['pdf_file'].validators.append(FileExtensionValidator(['pdf']))
        
        if user:
        
            if user.role == user.TEACHER:
                self.fields['course'].queryset = Course.objects.filter(instructor=user)
                
            elif user.role == user.ADMIN:
                self.fields['course'].queryset = Course.objects.all()

            else:
                self.fields['course'].queryset = Course.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        lesson_type = cleaned_data.get('lesson_type')
        if lesson_type == 'video' and not cleaned_data.get('video_url'):
            self.add_error('video_url', 'A video lesson needs a video URL.')
        # An existing PDF on the lesson counts when editing without a new upload.
        if lesson_type == 'pdf' and not (cleaned_data.get('pdf_file') or self.instance.pdf_file):
            self.add_error('pdf_file', 'A PDF lesson needs a PDF file.')
        return cleaned_data
