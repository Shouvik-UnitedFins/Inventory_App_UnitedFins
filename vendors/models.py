from django.db import models

class Vendor(models.Model):
    vendorName = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    fullAddress = models.CharField(max_length=255)
    pincode = models.CharField(max_length=10)
    city = models.CharField(max_length=50)
    GSTN = models.CharField(max_length=15, unique=True, null=True, blank=True)
    VENDOR_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('service', 'Service'),
        ('scrap', 'Scrap'),
    ]
    vendorType = models.CharField(max_length=10, choices=VENDOR_TYPE_CHOICES, default='purchase')
    rating = models.IntegerField(null=True, blank=True)
    plantId = models.IntegerField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    created_At = models.DateTimeField(auto_now_add=True)
    updated_At = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vendorName