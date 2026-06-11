from django.db import models
from slugify import slugify


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Book(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='book')
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    publisher = models.CharField(max_length=255)
    publication_year = models.IntegerField()
    page_count = models.IntegerField()
    language = models.CharField(max_length=50)
    genre = models.CharField(max_length=100)

    class Meta:
        db_table = 'books'


class Electronics(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='electronics')
    brand = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    warranty_period = models.CharField(max_length=50)
    voltage_requirement = models.CharField(max_length=50)
    connectivity = models.CharField(max_length=255)
    technical_specs = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'electronics'


class Fashion(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('U', 'Unisex')]
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='fashion')
    brand = models.CharField(max_length=100)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    season = models.CharField(max_length=50)

    class Meta:
        db_table = 'fashion'
