
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category
from .serializers import CategorySerializer
from users.permissions import IsAdminRole
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

@extend_schema_view(
    list=extend_schema(
        summary="List all categories",
        description="Retrieve a list of all categories. Supports filtering by categoryName.",
        tags=["Categories"]
    ),
    retrieve=extend_schema(
        summary="Retrieve a category",
        description="Get details of a specific category by its UUID.",
        tags=["Categories"],
        parameters=[
            OpenApiParameter(name='id', description='Category UUID', required=True, type=OpenApiTypes.UUID)
        ]
    ),
    create=extend_schema(
        summary="Create a new category",
        description="Create a new category. Requires a unique categoryName (2-50 chars) and optional description.",
        tags=["Categories"]
    ),
    update=extend_schema(
        summary="Update a category",
        description="Update all fields of a category by its UUID.",
        tags=["Categories"],
        parameters=[
            OpenApiParameter(name='id', description='Category UUID', required=True, type=OpenApiTypes.UUID)
        ]
    ),
    partial_update=extend_schema(
        summary="Partially update a category",
        description="Update one or more fields of a category by its UUID.",
        tags=["Categories"],
        parameters=[
            OpenApiParameter(name='id', description='Category UUID', required=True, type=OpenApiTypes.UUID)
        ]
    ),
    destroy=extend_schema(
        summary="Delete a category",
        description="Delete a category by its UUID.",
        tags=["Categories"],
        parameters=[
            OpenApiParameter(name='id', description='Category UUID', required=True, type=OpenApiTypes.UUID)
        ]
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """API endpoints for managing categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminRole]  # Use custom admin role permission
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categoryName']
    lookup_field = 'id'  # Using id (UUID primary key) as lookup field

    def list(self, request, *args, **kwargs):
        """List all categories with beautiful response format."""
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Categories retrieved successfully',
            'count': len(response.data),
            'categories': response.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single category with beautiful response format."""
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Category retrieved successfully',
            'category': response.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create category with beautiful response format."""
        response = super().create(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Category created successfully',
            'category': response.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update category with beautiful response format."""
        response = super().update(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Category updated successfully',
            'category': response.data
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partial update category with beautiful response format."""
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Category updated successfully',
            'category': response.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Delete category with beautiful response format."""
        instance = self.get_object()
        category_name = instance.categoryName
        super().destroy(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': f'Category "{category_name}" deleted successfully'
        }, status=status.HTTP_200_OK)
