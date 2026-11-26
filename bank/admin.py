from django.contrib import admin
from .models import Customer, Account, Transaction, Loan, Beneficiary


admin.site.register(Customer)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Loan)
admin.site.register(Beneficiary)