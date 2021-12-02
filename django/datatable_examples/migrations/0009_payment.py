# Generated by Django 3.2.7 on 2021-12-02 15:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datatable_examples', '0008_tally'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('amount', models.IntegerField()),
                ('quantity', models.IntegerField(default=1)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datatable_examples.company')),
            ],
        ),
    ]
