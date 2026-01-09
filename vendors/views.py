from rest_framework import viewsets, permissions
from .models import Vendor
from .serializers import VendorSerializer

from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

@extend_schema_view(
    list=extend_schema(summary="List all vendors", tags=["Vendors"]),
    retrieve=extend_schema(summary="Retrieve a vendor", tags=["Vendors"]),
    create=extend_schema(summary="Create a new vendor", tags=["Vendors"]),
    update=extend_schema(summary="Update a vendor", tags=["Vendors"]),
    partial_update=extend_schema(summary="Partially update a vendor", tags=["Vendors"]),
    destroy=extend_schema(summary="Delete a vendor", tags=["Vendors"]),
)
class VendorViewSet(viewsets.ModelViewSet):
    """API endpoints for managing vendors."""
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admin can access
    lookup_field = 'uuid'
    lookup_url_kwarg = 'id'  # URL parameter name

    def list(self, request, *args, **kwargs):
        """List all vendors with beautiful response format."""
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Vendors retrieved successfully',
            'count': len(response.data),
            'vendors': response.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single vendor with beautiful response format."""
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Vendor retrieved successfully',
            'vendor': response.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create vendor with beautiful response format."""
        response = super().create(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Vendor created successfully',
            'vendor': response.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update vendor with beautiful response format."""
        response = super().update(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Vendor updated successfully',
            'vendor': response.data
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partial update vendor with beautiful response format."""
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Vendor updated successfully',
            'vendor': response.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Delete vendor with beautiful response format."""
        try:
            instance = self.get_object()
            vendor_name = instance.vendorName
            super().destroy(request, *args, **kwargs)
            return Response({
                'success': True,
                'message': f'Vendor "{vendor_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
        except NotFound:
            return Response({
                'success': False,
                'message': 'Vendor not found'
            }, status=status.HTTP_404_NOT_FOUND)