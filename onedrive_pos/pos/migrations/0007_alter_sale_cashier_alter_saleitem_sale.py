# Generated by Django 5.1.1 on 2024-10-02 11:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0006_alter_saleitem_product'),
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='cashier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='staff.employee'),
        ),
        migrations.AlterField(
            model_name='saleitem',
            name='sale',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='pos.sale'),
        ),
    ]
