from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User
import uuid
import random

class Payment(models.Model):
    user = models.ForeignKey(
        User,on_delete=models.CASCADE,related_name='building_payments'  
    )
    
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    method = models.CharField(
        max_length=50,
        choices=[('MOMO', 'MTN MoMo'), ('BANK', 'Equity Bank'), ('CARD', 'Credit/Debit Card')],
        default='MOMO'
    )
    building = models.ForeignKey('BUS_SYSTEM.Building',on_delete=models.SET_NULL,null=True,blank=True,
        related_name='payments'  
    )
    vehicle = models.ForeignKey('BUS_SYSTEM.Vehicleinformation',on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'  
    )
    
   
    is_paid = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TXN-{self.transaction_id.hex[:8].upper()} | {self.user.username}"

    def generate_verification_code(self):
        self.verification_code = str(random.randint(100000, 999999))
        self.save()
    
    def verify_code(self, code):
        if self.verification_code == code:
            self.is_paid = True
            self.save()
            return True
        return False