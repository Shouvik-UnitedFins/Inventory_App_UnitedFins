from django.db import models
import uuid

class Vendor(models.Model):
    # Basic vendor information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
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
    
    # Rating fields - storing as string values like "5.0 - Excellent"
    RATING_CHOICES = [
        ('5.0 - Excellent', '5.0 - Excellent'),
        ('4.5 - Very Good', '4.5 - Very Good'),
        ('4.0 - Good', '4.0 - Good'),
        ('3.5 - Average', '3.5 - Average'),
        ('3.0 - Below Average', '3.0 - Below Average'),
        ('2.0 - Poor', '2.0 - Poor'),
        ('Not Rated', 'Not Rated'),
    ]
    
    quality_price_rating = models.CharField(
        max_length=25, 
        choices=RATING_CHOICES, 
        default='Not Rated',
        help_text="Quality and price rating"
    )
    delivery_time_rating = models.CharField(
        max_length=25, 
        choices=RATING_CHOICES, 
        default='Not Rated',
        help_text="Delivery time rating"
    )
    overall_avg_rating = models.CharField(
        max_length=25, 
        choices=RATING_CHOICES, 
        default='Not Rated',
        help_text="Overall average rating"
    )
    
    # Legacy rating field - keeping for backward compatibility
    rating = models.IntegerField(null=True, blank=True)
    plantId = models.BigIntegerField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    created_At = models.DateTimeField(auto_now_add=True)
    updated_At = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vendorName