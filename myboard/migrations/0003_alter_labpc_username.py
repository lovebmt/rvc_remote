# Generated by Django 3.2.9 on 2022-01-21 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myboard', '0002_rename_location_labpc_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='labpc',
            name='username',
            field=models.CharField(blank=True, default=None, editable=False, max_length=255),
        ),
    ]
