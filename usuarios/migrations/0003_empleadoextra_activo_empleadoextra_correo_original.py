# Generated by Django 5.2.1 on 2025-07-03 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_alter_usuario_fecha_nacimiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='empleadoextra',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='empleadoextra',
            name='correo_original',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
