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

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            'message': 'Vendor created successfully',
            'data': response.data
        }, status=response.status_code)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            'message': 'Vendor updated successfully',
            'data': response.data
        }, status=response.status_code)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            'message': 'Vendor updated successfully',
            'data': response.data
        }, status=response.status_code)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            super().destroy(request, *args, **kwargs)
            return Response({'message': 'Vendor deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except NotFound:
            return Response({'message': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)