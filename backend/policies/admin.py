from django.contrib import admin
from .models import Policy, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['plcy_no', 'plcy_nm', 'district', 'aply_end_dt']
    list_filter = ['categories', 'district']
    search_fields = ['plcy_nm', 'plcy_expln_cn']