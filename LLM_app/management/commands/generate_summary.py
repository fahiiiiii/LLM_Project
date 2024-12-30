from django.core.management.base import BaseCommand
from LLM_app.models import Property, PropertySummary
from ollama import OllamaClient  # Assuming Ollama SDK is available

class Command(BaseCommand):
    help = 'Generate a summary for all properties using Ollama model'

    def handle(self, *args, **kwargs):
        properties = Property.objects.all()

        for property in properties:
            # Create a prompt for the summary
            prompt = f"Generate a summary for the following property:\nTitle: {property.title}\nDescription: {property.description}"

            # Use Ollama to generate summary
            ollama_client = OllamaClient()
            result = ollama_client.call(prompt)

            # Save the summary to the PropertySummary table
            PropertySummary.objects.create(property=property, summary=result['summary'])
            self.stdout.write(f"Summary for {property.id} generated successfully.")
