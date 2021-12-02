# Generated by Django 3.2.7 on 2021-12-02 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datatable_examples', '0007_company_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tally',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('cars', models.IntegerField()),
                ('vans', models.IntegerField()),
                ('buses', models.IntegerField()),
                ('lorries', models.IntegerField()),
                ('motor_bikes', models.IntegerField()),
                ('push_bikes', models.IntegerField()),
                ('tractors', models.IntegerField()),
            ],
            options={
                'verbose_name_plural': 'Tallies',
            },
        ),
    ]
