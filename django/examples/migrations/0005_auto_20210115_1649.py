# Generated by Django 2.2.5 on 2021-01-15 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('examples', '0004_person_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='TagsDirect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag_direct', models.CharField(max_length=40)),
            ],
        ),
        migrations.AddField(
            model_name='company',
            name='direct_tag',
            field=models.ManyToManyField(to='examples.TagsDirect'),
        ),
    ]
