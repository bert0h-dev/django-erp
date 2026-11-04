from django.db import models

class Status(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Status")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    
    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Statuses"
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def default_pk(cls):
        """Id del estado con el que empieza un registro nuevo: el primer estado activo del catálogo."""
        return cls.objects.filter(is_active=True).order_by('pk').values_list('pk', flat=True).first()

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Country")
    abbreviation = models.CharField(max_length=2, unique=True, verbose_name="Abbreviation")  # ISO 3166-1 alfa-2

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Currency(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Currency")
    code = models.CharField(max_length=3, unique=True, verbose_name="Code")  # ISO 4217: distingue monedas con el mismo símbolo
    symbol = models.CharField(max_length=5, verbose_name="Symbol")

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
