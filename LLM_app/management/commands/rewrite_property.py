# LLM_app/management/commands/rewrite_property.py

from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json
from ...models import Property  # Updated import path

class Command(BaseCommand):
    help = 'Rewrites property titles and descriptions using Ollama'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            default='llama2',
            help='Ollama model to use for rewriting'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of properties to process in each batch'
        )

    def get_ollama_response(self, prompt, model):
        """Send request to Ollama API and get response."""
        url = 'http://ollama:11434/api/generate'
        
        data = {
            'model': model,
            'prompt': prompt,
            'stream': False
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error calling Ollama API: {e}'))
            return None

    def rewrite_property(self, property_item, model):
        """Rewrite title and description for a single property."""
        # Prompt for title rewriting
        title_prompt = f"""
        Rewrite the following property title to be more engaging and descriptive, 
        while maintaining its core meaning. Keep it concise (max 50 characters):
        
        Original title: {property_item.property_title}
        """
        
        # Prompt for description rewriting
        description_prompt = f"""
        Rewrite the following property description to be more detailed and professional,
        maintaining the key information but making it clearer and more engaging:
        
        Original description: {property_item.description}
        """
        
        # Get new title and description from Ollama
        new_title = self.get_ollama_response(title_prompt, model)
        new_description = self.get_ollama_response(description_prompt, model)
        
        if new_title and new_description:
            try:
                # Store original values
                original_title = property_item.property_title
                original_description = property_item.description
                
                # Update property
                property_item.property_title = new_title.strip()
                property_item.description = new_description.strip()
                property_item.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully rewrote property {property_item.property_id}:\n'
                    f'Title: {original_title} -> {new_title}\n'
                    f'Description: {original_description} -> {new_description}'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error saving property {property_item.property_id}: {e}'
                ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Skipping property {property_item.property_id} due to API error'
            ))

    def handle(self, *args, **options):
        model = options['model']
        batch_size = options['batch_size']
        
        # Get all properties
        properties = Property.objects.all()
        total_properties = properties.count()
        
        self.stdout.write(f'Starting to process {total_properties} properties...')
        
        # Process properties in batches
        for i in range(0, total_properties, batch_size):
            batch = properties[i:i + batch_size]
            for property_item in batch:
                self.rewrite_property(property_item, model)
            
            self.stdout.write(f'Processed {min(i + batch_size, total_properties)}/{total_properties} properties')
# from django.core.management.base import BaseCommand
# from django.db import transaction
# from LLM_app.models import Property
# import requests

# class Command(BaseCommand):
#     help = 'Re-write property titles and descriptions using the Ollama model'

#     def handle(self, *args, **kwargs):
#         properties = Property.objects.all()  # Or apply some filters

#         for property in properties:
#             original_title = property.title
#             original_description = property.description

#             # Re-write title and description with Ollama API
#             new_title, new_description = self.rewrite_property(original_title, original_description)

#             # Update the property in the database with the new title and description
#             with transaction.atomic():
#                 property.title = new_title
#                 property.description = new_description
#                 property.save()

#             self.stdout.write(f"Updated property {property.id}.")

#     def rewrite_property(self, title, description):
#         url = "http://ollama_container:11434/llama_api_endpoint"
#         headers = {"Content-Type": "application/json"}
#         data = {
#             "title": title,
#             "description": description
#         }

#         try:
#             response = requests.post(url, json=data, headers=headers)
#             response.raise_for_status()
#             rewritten_data = response.json()
#             return rewritten_data.get("new_title", title), rewritten_data.get("new_description", description)
#         except requests.exceptions.RequestException as e:
#             self.stderr.write(f"Error rewriting property: {e}")
#             return title, description  # Return original values if error

# ---------------------------------------------------
# from django.core.management.base import BaseCommand
# from LLM_app.models import Property
# from ollama import OllamaClient  # Assuming Ollama SDK for Python is available

# class Command(BaseCommand):
#     help = 'Rewrite property title and description using Ollama model'

#     def handle(self, *args, **kwargs):
#         # Fetch properties that need to be updated
#         properties = Property.objects.all()

#         for property in properties:
#             # Prepare the prompt using property title and description
#             prompt = f"Rewrite the following property title and description:\nTitle: {property.title}\nDescription: {property.description}"

#             # Call Ollama to generate rewritten text
#             ollama_client = OllamaClient()
#             result = ollama_client.call(prompt)

#             # Update property with rewritten title and description
#             property.title = result['title']
#             property.description = result['description']
#             property.save()

#             self.stdout.write(f"Property {property.id} rewritten successfully.")
# ---------------------------------------------
