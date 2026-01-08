from rest_framework import serializers
from .models import Vendor
import re

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['uuid', 'vendorName', 'phone', 'email', 'fullAddress', 'pincode', 'city', 'GSTN', 'vendorType', 'rating', 'plantId', 'isActive', 'created_At', 'updated_At']

    def validate_phone(self, value):
        if value and not re.match(r'^[0-9]{10,15}$', value):
            raise serializers.ValidationError("Phone must be 10-15 digits.")
        return value

    def validate_pincode(self, value):
        if value and not re.match(r'^[0-9]{4,10}$', value):
            raise serializers.ValidationError("Pincode must be 4-10 digits.")
        return value

    def validate_GSTN(self, value):
        # Updated GSTN pattern for Indian GSTN format: 15 characters
        # Format: 2 digits (state) + 10 characters (PAN) + 1 digit (entity) + 1 character (check) + 1 character (default Z)
        GSTN_REGEX = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
        if value and not re.match(GSTN_REGEX, value):
            raise serializers.ValidationError("GSTN must be a valid 15-character Indian GSTN number (Format: 22AAAAA0000A1Z5).")
        return value

    def validate_rating(self, value):
        if value and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value