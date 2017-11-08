# Generated by Django 2.0b1 on 2017-11-08 12:42

import _socket
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edc_sync_files', '0003_auto_20170518_1233'),
    ]

    operations = [
        migrations.AddField(
            model_name='exportedtransactionfilehistory',
            name='device_created',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='exportedtransactionfilehistory',
            name='device_modified',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='importedtransactionfilehistory',
            name='device_created',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='importedtransactionfilehistory',
            name='device_modified',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='exportedtransactionfilehistory',
            name='hostname_created',
            field=models.CharField(blank=True, default=_socket.gethostname, help_text='System field. (modified on create only)', max_length=60),
        ),
        migrations.AlterField(
            model_name='importedtransactionfilehistory',
            name='hostname_created',
            field=models.CharField(blank=True, default=_socket.gethostname, help_text='System field. (modified on create only)', max_length=60),
        ),
    ]
