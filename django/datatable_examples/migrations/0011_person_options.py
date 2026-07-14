from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datatable_examples', '0010_alter_company_direct_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='options',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
