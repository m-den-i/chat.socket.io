from __future__ import absolute_import

from django.contrib.auth import authenticate, password_validation, get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework.settings import api_settings
from rest_framework import serializers

AuthUserModel = get_user_model()


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        style = {
            'input_type': 'password',
        }
        style.update(kwargs.get('style', {}))
        kwargs['style'] = style
        super(PasswordField, self).__init__(**kwargs)


class SetPasswordMixin(serializers.Serializer):
    password = PasswordField(required=True, write_only=True)

    def validate_password(self, value):
        password_validation.validate_password(value, self.instance)
        return make_password(value)


class UserSerializer(SetPasswordMixin, serializers.ModelSerializer):

    class Meta:
        model = AuthUserModel
        fields = ('id', 'email', 'password',
                  'first_name', 'last_name')
        read_only_fields = ('id', )


class LoginSerializer(serializers.Serializer):
    fail_login_message = ''

    def authenticate(self):
        user = authenticate(**self.validated_data)
        if not user:
            raise serializers.ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [self.fail_login_message],
            })
        return user


class UsernameLoginSerializer(LoginSerializer):
    username = serializers.CharField()
    password = serializers.CharField()

    fail_login_message = 'Invalid username or password.'


class ResetPasswordByEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        fields = ['email']
        model = AuthUserModel

    def __init__(self, *args, **kwargs):
        super(ResetPasswordByEmailSerializer, self).__init__(*args, **kwargs)

    def send_reset_password_email(self):
        try:
            user = self.Meta.model.objects.get(email=self.validated_data.get('email'))
        except self.Meta.model.DoesNotExist:
            return

        user.send_reset_password_email()
