from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import TemplateView, FormView
from drf_secure_token.models import Token
from rest_framework import decorators, mixins, permissions, status, viewsets
from rest_framework.response import Response

from base.forms import LoginForm
from base.permissions import IsSelfOrReadOnly, POSTOnlyIfAnonymous
from base.serializers import ResetPasswordByEmailSerializer, UserSerializer, UsernameLoginSerializer


@login_required(login_url='/login/')
def index(request):
    return render(request, 'index.html')


class LoginView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = '/'

    def form_valid(self, form):
        user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user is not None:
            login(self.request, user)
            return redirect('/')
        else:
            return HttpResponse('Please register.')


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

    @decorators.list_route(methods=['post'], permission_classes=[permissions.AllowAny], url_path='signin')
    def basic_login(self, request):
        serializer = self.get_login_serializer()
        serializer.is_valid(raise_exception=True)
        self.user = serializer.authenticate()
        headers = self.get_success_headers()
        request.session['X-Token'] = headers[self.NEW_TOKEN_HEADER].key
        resp = Response(status=status.HTTP_201_CREATED,
                        headers=headers,
                        data=UserSerializer(instance=self.user).data)
        return resp

    def get_login_serializer(self, **kwargs):
        return self.login_serializer_class(data=self.request.data, **kwargs)

    def get_success_headers(self):
        return {self.NEW_TOKEN_HEADER: self.user.user_auth_tokens.create()}

    @decorators.list_route(methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='token')
    def token(self, request):
        tok = Token.objects.filter(user=request.user).first()
        return Response(data={'X-Token': tok.key if tok else Token.objects.create(user=request.user).key})

    @decorators.list_route(methods=['delete'], permission_classes=[permissions.IsAuthenticated], url_path='logout')
    def logout(self, request):
        auth_token = request._request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        request.user.user_auth_tokens.filter(key=auth_token).delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)
