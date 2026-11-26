from django.db import models


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customers'

    def __str__(self):
        return self.name


class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.DO_NOTHING,
        db_column='customer_id'
    )
    account_number = models.BigIntegerField(unique=True)
    account_type = models.CharField(max_length=20)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'accounts'

    def __str__(self):
        return str(self.account_number)


class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(
        Account,
        on_delete=models.DO_NOTHING,
        db_column='account_id'
    )
    transaction_type = models.CharField(max_length=20)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    related_account = models.ForeignKey(
        Account,
        on_delete=models.DO_NOTHING,
        related_name='related_transactions',
        db_column='related_account_id',
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    transaction_date = models.DateTimeField(
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'transactions'

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"


class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.DO_NOTHING,
        db_column='customer_id'
    )
    loan_type = models.CharField(max_length=50)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    duration_months = models.IntegerField(
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'loans'


class Beneficiary(models.Model):
    beneficiary_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.DO_NOTHING,
        db_column='customer_id'
    )
    beneficiary_name = models.CharField(max_length=100)
    account_number = models.BigIntegerField()
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    ifsc_code = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'beneficiaries'
