# models.py
from django.db import models

class Property(models.Model):
    property_id = models.AutoField(primary_key=True)
    property_title = models.CharField(max_length=255)
    rating = models.IntegerField()
    review = models.TextField()
    description = models.TextField()

    class Meta:
        db_table = 'property'  # This will match your existing table name
        
    def __str__(self):
        return f"{self.property_id}: {self.property_title}"

# migrations/0001_initial.py
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Property',
            fields=[
                ('property_id', models.AutoField(primary_key=True)),
                ('property_title', models.CharField(max_length=255)),
                ('rating', models.IntegerField()),
                ('review', models.TextField()),
                ('description', models.TextField()),
            ],
            options={
                'db_table': 'property',
            },
        ),
    ]