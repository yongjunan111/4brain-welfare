from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date, timedelta
from .models import Policy, Category
from .serializers import PolicyListSerializer, PolicyDetailSerializer, CategorySerializer


class PolicyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    정책 조회 API
    - GET /api/policies/          : 목록
    - GET /api/policies/{plcy_no}/ : 상세
    """
    queryset = Policy.objects.prefetch_related('categories').all()

    # 필터링/검색/정렬 추가
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['district', 'categories__name']  # 필터 가능한 필드
    search_fields = ['plcy_nm', 'plcy_expln_cn']         # 검색 가능한 필드
    ordering_fields = ['aply_end_dt', 'frst_reg_dt']     # 정렬 가능한 필드
    ordering = ['-frst_reg_dt']                          # 기본 정렬: 최신순
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PolicyListSerializer
        return PolicyDetailSerializer
    
    @action(detail=False, methods=['get'])
    def deadline_soon(self, request):
        """마감임박 정책 (7일 이내, 최대 6개)"""
        today = date.today()
        week_later = today + timedelta(days=7)
        
        policies = Policy.objects.filter(
            aply_end_dt__gte=today,
            aply_end_dt__lte=week_later
        ).order_by('aply_end_dt')[:6]
        
        serializer = PolicyListSerializer(policies, many=True)
        return Response(serializer.data)