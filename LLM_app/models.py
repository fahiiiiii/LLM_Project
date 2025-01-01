# models.py
from django.db import models



# class MockData(models.Model):
#      property_title = models.CharField(max_length=255)
#      rating = models.IntegerField()
#      review = models.TextField()
#      description = models.TextField()

#      class Meta:
#        db_table = 'MOCK_DATA' #  this is your table name

#      def __str__(self):
#          return self.property_title

# migrations/0001_initial.py
# from django.db import models

# class PropertySummary(models.Model):
#     property_id = models.UUIDField(primary_key=True)
#     summary = models.TextField()
    

#     class Meta:
#         db_table = 'LLM_app_propertysummary'

# # from django.db import models

# class PropertySummary(models.Model):
#     property_id = models.IntegerField(primary_key=True)
#     summary = models.TextField(blank=True, null=True)  # Allow empty summaries

#     def __str__(self):
#         return f"Summary for Property ID: {self.property_id}"
# # LLM_app/models.py
# from django.db import models










class LLM_app_propertysummary(models.Model):
    property_id = models.UUIDField(primary_key=True)
    summary = models.TextField()

    class Meta:
        db_table = 'LLM_app_propertysummary'  # Custom table name

    def __str__(self):
        return f"Summary for Property ID: {self.property_id}"


# class LLM_app_propertyreview(models.Model):
#     property_id = models.IntegerField(unique=True, primary_key=True)
#     rating = models.IntegerField()  # Rating out of 5
#     review = models.TextField()


class LLM_app_propertyreview(models.Model):
    property_id = models.UUIDField(primary_key=True, unique=True, editable=False)  # Set as primary key, remove unique
    rating = models.FloatField(null=True)
    review = models.TextField()


    class Meta:
        db_table = 'LLM_app_propertyreview'
        
    def __str__(self):
        return f"Rating and Review for for Property ID: {self.property_id}"
