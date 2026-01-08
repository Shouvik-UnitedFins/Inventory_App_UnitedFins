
from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category
from .serializers import CategorySerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(
        summary="List all categories",
        description="Retrieve a list of all categories. Supports filtering by categoryName.",
    ),
    retrieve=extend_schema(
        summary="Retrieve a category",
        description="Get details of a specific category by its UUID.",
    ),
    create=extend_schema(
        summary="Create a new category",
        description="Create a new category. Requires a unique categoryName (2-50 chars) and optional description.",
    ),
    update=extend_schema(
        summary="Update a category",
        description="Update all fields of a category by its UUID.",
    ),
    partial_update=extend_schema(
        summary="Partially update a category",
        description="Update one or more fields of a category by its UUID.",
    ),
    destroy=extend_schema(
        summary="Delete a category",
        description="Delete a category by its UUID.",
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categoryName']
