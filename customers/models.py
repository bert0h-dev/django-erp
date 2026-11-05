from django.db import models
from django.conf import settings
from core.models import Status, Country, Currency

class Customer(models.Model):
  id_customer = models.CharField(max_length=20, unique=True, verbose_name="ID Cliente")
  name = models.CharField(max_length=150, verbose_name="Nombre")
  tax_id = models.CharField(max_length=50, verbose_name="ID Fiscal")
  country = models.ForeignKey(Country, on_delete=models.PROTECT, verbose_name="País")
  state = models.CharField(max_length=100, blank=True, verbose_name="Estado/Provincia")
  city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
  address = models.CharField(max_length=200, blank=True, verbose_name="Dirección")
  zip_code = models.CharField(max_length=20, blank=True, verbose_name="Código Postal")
  phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
  email = models.EmailField(max_length=100, blank=True, verbose_name="Email")
  payment_terms = models.CharField(max_length=100, blank=True, verbose_name="Términos de Pago")
  currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name="Moneda")
  payment_method = models.CharField(max_length=100, blank=True, verbose_name="Método de Pago")
  bank_account = models.CharField(max_length=100, blank=True, verbose_name="Cuenta Bancaria")

  status = models.ForeignKey(Status, on_delete=models.PROTECT, verbose_name="Status")

  created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado En")
  updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado En")
  created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers_created', verbose_name="Creado Por")

  class Meta:
    verbose_name = "Customer"
    verbose_name_plural = "Customers"
    ordering = ['-created_at', '-id']

  def __str__(self):
    return self.name