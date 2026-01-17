from django.contrib import admin
from .models import Transaction, Loan, LoanRepayment

admin.site.register(Transaction)
admin.site.register(Loan)
admin.site.register(LoanRepayment)