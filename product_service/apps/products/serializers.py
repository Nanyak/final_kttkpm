from rest_framework import serializers
from .models import Category, Product, Book, Electronics, Fashion


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['slug', 'created_at', 'updated_at']


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        exclude = ['product']


class ElectronicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electronics
        exclude = ['product']


class FashionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fashion
        exclude = ['product']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    book = BookSerializer(required=False, allow_null=True)
    electronics = ElectronicsSerializer(required=False, allow_null=True)
    fashion = FashionSerializer(required=False, allow_null=True)
    product_type = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'base_price', 'stock_quantity',
                  'is_active', 'image_url', 'category', 'category_name', 'created_at', 'updated_at',
                  'book', 'electronics', 'fashion', 'product_type']
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_product_type(self, obj):
        if hasattr(obj, 'book'):
            return 'book'
        if hasattr(obj, 'electronics'):
            return 'electronics'
        if hasattr(obj, 'fashion'):
            return 'fashion'
        return 'generic'

    def create(self, validated_data):
        book_data = validated_data.pop('book', None)
        electronics_data = validated_data.pop('electronics', None)
        fashion_data = validated_data.pop('fashion', None)
        product = Product.objects.create(**validated_data)
        if book_data:
            Book.objects.create(product=product, **book_data)
        if electronics_data:
            Electronics.objects.create(product=product, **electronics_data)
        if fashion_data:
            Fashion.objects.create(product=product, **fashion_data)
        return product

    def update(self, instance, validated_data):
        book_data = validated_data.pop('book', None)
        electronics_data = validated_data.pop('electronics', None)
        fashion_data = validated_data.pop('fashion', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if book_data and hasattr(instance, 'book'):
            for attr, value in book_data.items():
                setattr(instance.book, attr, value)
            instance.book.save()
        if electronics_data and hasattr(instance, 'electronics'):
            for attr, value in electronics_data.items():
                setattr(instance.electronics, attr, value)
            instance.electronics.save()
        if fashion_data and hasattr(instance, 'fashion'):
            for attr, value in fashion_data.items():
                setattr(instance.fashion, attr, value)
            instance.fashion.save()
        return instance
