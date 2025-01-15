from .serializers import *
from .models import *
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


class OrderAPIView(APIView):
    permission_classes = [IsAdminOrOwner]

    def get(self, request, pk=None):
        if pk:
            try:
                order = Order.objects.get(pk=pk, is_deleted=False)
                serializer = OrderSerializer(order)
                return Response(serializer.data)
            except Order.DoesNotExist:
                return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        status_filter = request.query_params.get('status')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        orders = Order.objects.filter(is_deleted=False)

        if status_filter:
            orders = orders.filter(status=status_filter)
        if min_price:
            orders = orders.filter(total_price__gte=min_price)
        if max_price:
            orders = orders.filter(total_price__lte=max_price)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, is_deleted=False)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, is_deleted=False)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        order.is_deleted = True
        order.save()
        cache.delete(f'order_{order.order_id}')
        return Response({"message":"Your order has been deleted"},status=status.HTTP_200_OK)

class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key})
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)



