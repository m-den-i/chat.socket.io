from django.conf.urls import include, url
from rest_framework import routers

from base.views import UserAuthViewSet, UserViewSet

router = routers.DefaultRouter()
router.register(r'auth', UserAuthViewSet, 'auth')
router.register(r'users', UserViewSet)

base_api_patterns = \
    [
        url(r'', include(router.urls)),
    ]
