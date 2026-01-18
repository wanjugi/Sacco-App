from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_loan_rejection_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(choices=[('DEPOSIT', 'Monthly Contribution'), ('WITHDRAWAL', 'Savings Withdrawal'), ('FINE', 'Late Payment Fine'), ('SHARE_TRANSFER', 'Transfer to Share Capital')], default='DEPOSIT', max_length=20),
        ),
    ]
