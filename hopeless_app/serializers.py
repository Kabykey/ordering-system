from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *

# Serializers
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['product_id', 'name', 'price', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    class Meta:
        model = Order
        fields = ['order_id', 'customer_name', 'status', 'total_price', 'products']

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for product_data in products_data:
            product, _ = Product.objects.get_or_create(**product_data)
            order.products.add(product)
        cache.set(f'order_{order.order_id}', order)
        return order

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products')
        instance.customer_name = validated_data.get('customer_name', instance.customer_name)
        instance.status = validated_data.get('status', instance.status)
        instance.total_price = validated_data.get('total_price', instance.total_price)
        instance.save()

        instance.products.clear()
        for product_data in products_data:
            product, _ = Product.objects.get_or_create(**product_data)
            instance.products.add(product)
        cache.set(f'order_{instance.order_id}', instance)
        return instance

class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.role == 'Admin' or obj.customer_name == request.user.username

# ViewSets
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.filter(is_deleted=False)
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrOwner]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        cache.delete(f'order_{instance.order_id}')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def filter(self, request):
        status_filter = request.query_params.get('status')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        orders = self.queryset

        if status_filter:
            orders = orders.filter(status=status_filter)
        if min_price:
            orders = orders.filter(total_price__gte=min_price)
        if max_price:
            orders = orders.filter(total_price__lte=max_price)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
