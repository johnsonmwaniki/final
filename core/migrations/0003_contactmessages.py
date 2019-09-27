# Generated by Django 2.2 on 2019-09-10 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_item_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactMessages',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=100)),
                ('phone', models.IntegerField()),
                ('message', models.CharField(max_length=250)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
