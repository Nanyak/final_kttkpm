from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .services import reduce_product_stock


def ok(data, http=status.HTTP_200_OK):
    return Response({'status': 'success', 'data': data}, status=http)


def err(message, http=status.HTTP_400_BAD_REQUEST):
    return Response({'status': 'error', 'data': {'message': message}}, status=http)


class CategoryListView(APIView):
    def get(self, request):
        qs = Category.objects.all()
        is_active = request.query_params.get('is_active')
        parent_id = request.query_params.get('parent_id')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        if parent_id is not None:
            if parent_id in ('', '0', 'null', 'root'):
                qs = qs.filter(parent__isnull=True)
            else:
                qs = qs.filter(parent_id=parent_id)
        return ok(CategorySerializer(qs, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ok(serializer.data, status.HTTP_201_CREATED)
        return err(serializer.errors)


class CategoryDetailView(APIView):
    def get(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        return ok(CategorySerializer(cat).data)

    def patch(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(cat, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return ok(serializer.data)
        return err(serializer.errors)

    def delete(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        cat.delete()
        return ok({'deleted': True}, status.HTTP_204_NO_CONTENT)


class ProductListView(APIView):
    def get(self, request):
        qs = Product.objects.select_related('category', 'category__parent', 'category__parent__parent').all()
        category_id = request.query_params.get('category_id')
        is_active = request.query_params.get('is_active')
        search = request.query_params.get('search')
        ids = request.query_params.get('ids')
        if ids:
            try:
                product_ids = [int(pid.strip()) for pid in ids.split(',') if pid.strip()]
            except ValueError:
                return err('ids must be a comma-separated list of integers')
            qs = qs.filter(id__in=product_ids)
        if category_id:
            category = get_object_or_404(Category, pk=category_id)
            category_ids = _category_with_descendants(category)
            qs = qs.filter(category_id__in=category_ids)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        if search:
            qs = qs.filter(name__icontains=search)
        return ok(ProductSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ok(serializer.data, status.HTTP_201_CREATED)
        return err(serializer.errors)


class ProductDetailView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related('category', 'category__parent', 'category__parent__parent'),
            pk=pk,
        )
        return ok(ProductSerializer(product).data)

    def patch(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return ok(serializer.data)
        return err(serializer.errors)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return ok({'deleted': True}, status.HTTP_204_NO_CONTENT)


class ReduceStockView(APIView):
    def patch(self, request, pk):
        try:
            quantity = int(request.data.get('quantity', 0))
        except (TypeError, ValueError):
            return err('Invalid quantity')
        if quantity <= 0:
            return err('Quantity must be positive')
        try:
            product = reduce_product_stock(pk, quantity)
        except Product.DoesNotExist:
            return err('Product not found', status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return err(str(e))
        return ok(ProductSerializer(product).data)


def _category_with_descendants(category):
    ids = [category.id]
    children = list(category.children.all())
    for child in children:
        ids.extend(_category_with_descendants(child))
    return ids
