from django.core.management.base import BaseCommand
from LLM_app.models import Property, PropertyReview
from ollama import OllamaClient  # Assuming Ollama SDK is available

class Command(BaseCommand):
    help = 'Generate ratings and reviews for all properties using LLM model'

    def handle(self, *args, **kwargs):
        properties = Property.objects.all()

        for property in properties:
            # Create a prompt for generating ratings and reviews
            prompt = f"Generate a rating and review for the following property:\nTitle: {property.title}\nDescription: {property.description}"

            # Use Ollama/LLM to generate the review
            ollama_client = OllamaClient()
            result = ollama_client.call(prompt)

            # Save the rating and review to the PropertyReview table
            PropertyReview.objects.create(property=property, rating=result['rating'], review=result['review'])
            self.stdout.write(f"Review for {property.id} generated successfully.")
