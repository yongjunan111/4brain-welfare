from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyViewSet

router = DefaultRouter()
router.register(r'policies', PolicyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]