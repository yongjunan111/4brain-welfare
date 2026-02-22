from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyViewSet, CenterViewSet, MapPOIViewSet

router = DefaultRouter()
router.register(r'map/pois', MapPOIViewSet, basename='map-poi') # /api/policies/map/pois/
router.register(r'', PolicyViewSet, basename='policy')

urlpatterns = [
    # [FIX] centers가 policy_id로 인식되지 않도록 순서 보장 (explicit path first)
    path('centers/', CenterViewSet.as_view({'get': 'list'}), name='center-list'),
    path('', include(router.urls)),
]