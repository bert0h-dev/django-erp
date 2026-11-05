from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
  list_display = ('id_customer', 'name', 'country', 'currency', 'status')
  list_filter = ('status', 'country')
  search_fields = ('id_customer', 'name', 'tax_id')
