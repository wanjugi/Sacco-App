from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from decimal import Decimal

class Transaction(models.Model):
    """
    Tracks money going IN (Savings) or OUT (Withdrawals).
    """
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Monthly Contribution'),
        ('WITHDRAWAL', 'Savings Withdrawal'),
        ('FINE', 'Late Payment Fine'),
        ('SHARE_TRANSFER', 'Transfer to Share Capital'),
        ('BOND_INVESTMENT', 'Investment in Govt Bonds'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='DEPOSIT')
    date = models.DateTimeField(default=timezone.now)
    reference_code = models.CharField(max_length=20, blank=True, null=True) # e.g., M-Pesa Code
    

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()} - KES {self.amount}"

class Loan(models.Model):
    """
    Tracks a loan request and its lifecycle.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved & Disbursed'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Fully Repaid'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount borrowed")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.0, help_text="Annual Interest Rate in %")
    duration_months = models.IntegerField(default=12, help_text="Repayment period in months")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection (if applicable)")
    
    total_due = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    date_applied = models.DateTimeField(default=timezone.now)
    date_approved = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate total interest automatically before saving
        if not self.total_due:
            # Simple Interest Formula: A = P(1 + rt)
            p = Decimal(self.principal_amount)
            r = Decimal(self.interest_rate)
            t = Decimal(self.duration_months)
            
            interest = p * (r / Decimal(100)) * (t / Decimal(12))
            
            self.total_due = p + interest
            self.balance_due = self.total_due
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Loan #{self.id} - {self.user.username} (KES {self.principal_amount})"

class LoanRepayment(models.Model):
    """
    Tracks payments made towards a specific loan.
    """
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="repayments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Deduct from loan balance automatically
        super().save(*args, **kwargs)
        self.loan.balance_due -= self.amount
        
        # Check if fully paid
        if self.loan.balance_due <= 0:
            self.loan.status = 'PAID'
            self.loan.balance_due = 0
            
        self.loan.save()

    def __str__(self):
        return f"Repayment - KES {self.amount} for Loan #{self.loan.id}"