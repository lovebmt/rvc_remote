# Generated by Django 3.2.9 on 2022-01-28 03:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myboard', '0006_board_statusboot'),
    ]

    operations = [
        migrations.RenameField(
            model_name='board',
            old_name='isUsing',
            new_name='lock',
        ),
    ]
