# Generated by Django 2.2.5 on 2021-07-16 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datatable_examples', '0006_company_dissolved'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='order',
            field=models.IntegerField(null=True),
        ),
    ]
