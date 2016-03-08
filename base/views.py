from django.contrib.auth import get_user_model
from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from rest_framework import decorators, mixins, permissions, status, viewsets
from rest_framework.response import Response

from base.permissions import IsSelfOrReadOnly, POSTOnlyIfAnonymous
from base.serializers import ResetPasswordByEmailSerializer, UserSerializer, UsernameLoginSerializer


class IndexView(TemplateView):
    template_name = 'index.html'


class ResetPasswordViewMixin(object):
    reset_password_serializer_class = ResetPasswordByEmailSerializer

    @decorators.list_route(methods=['post'], permission_classes=[permissions.AllowAny], url_path='reset-password')
    def reset_password(self, request, **kwargs):
        serializer = self.get_reset_password_serializer()
        serializer.is_valid(raise_exception=True)
        serializer.send_reset_password_email()
        return Response()

    def get_reset_password_serializer(self, **kwargs):
        return self.reset_password_serializer_class(data=self.request.data, **kwargs)


class RetrieveSelfMixin(object):
    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if self.kwargs[lookup_url_kwarg] == 'me':
            obj = self.request.user
            self.check_object_permissions(self.request, obj)
            return obj

        return super(RetrieveSelfMixin, self).get_object()


class UserViewSet(RetrieveSelfMixin,
                  ResetPasswordViewMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = UserSerializer
    queryset = get_user_model().objects
    permission_classes = [IsSelfOrReadOnly, POSTOnlyIfAnonymous]

    def update(self, request, *args, **kwargs):
        kwargs.update({'partial': True})
        return super(UserViewSet, self).update(request, *args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        response = super(UserViewSet, self).create(request, *args, **kwargs)
        response.data = None
        return response

    def perform_create(self, serializer):
        obj = serializer.save()


class UserAuthViewSet(viewsets.ViewSet):
    NEW_TOKEN_HEADER = 'X-Token'

    login_serializer_class = UsernameLoginSerializer

    @decorators.list_route(methods=['post'], permission_classes=[permissions.AllowAny], url_path='login')
    def basic_login(self, request):
        serializer = self.get_login_serializer()
        serializer.is_valid(raise_exception=True)
        self.user = serializer.authenticate()
        return Response(status=status.HTTP_201_CREATED,
                        headers=self.get_success_headers(),
                        data=UserSerializer(instance=self.user).data)

    def get_login_serializer(self, **kwargs):
        return self.login_serializer_class(data=self.request.data, **kwargs)

    def get_success_headers(self):
        return {self.NEW_TOKEN_HEADER: self.user.user_auth_tokens.create()}

    @decorators.list_route(methods=['delete'], permission_classes=[permissions.IsAuthenticated], url_path='logout')
    def logout(self, request):
        auth_token = request._request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        request.user.user_auth_tokens.filter(key=auth_token).delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)
