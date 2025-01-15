from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _


# Custom User model with roles
class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'User', _('User')
        ADMIN = 'Admin', _('Admin')

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='hopeless_user_groups',
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='hopeless_user_permissions',
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_query_name='user',
    )


# Product model
class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    def __str__(self):
        return self.name


# Order model
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')

    order_id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.ManyToManyField(Product)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.set(f'order_{self.order_id}', self)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
        cache.delete(f'order_{self.order_id}')

    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"


# Signals for logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def log_order_save(sender, instance, created, **kwargs):
    action = 'Created' if created else 'Updated'
    logger.info(f"Order {instance.order_id} {action} by {instance.customer_name}.")


@receiver(post_delete, sender=Order)
def log_order_delete(sender, instance, **kwargs):
    logger.info(f"Order {instance.order_id} Soft Deleted by {instance.customer_name}.")


