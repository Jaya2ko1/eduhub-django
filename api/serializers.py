from rest_framework import serializers
from django.contrib.auth import get_user_model

from courses.models import Course

User = get_user_model()


class CourseSerializer(serializers.ModelSerializer):

    instructor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='teacher'),
        required=False
    )

    class Meta:
        model = Course
        fields = '__all__'

    def validate(self, attrs):

        request = self.context['request']

        if request.user.role == 'teacher':

            instructor = attrs.get('instructor')

            if instructor and instructor != request.user:
                raise serializers.ValidationError({
                    'instructor': 'You can only create courses under your own identity.'
                })

        elif request.user.role == 'admin':

            if not attrs.get('instructor'):
                raise serializers.ValidationError({
                    'instructor': 'Admin must select an instructor.'
                })

        return attrs