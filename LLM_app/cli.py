from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json
from LLM_app.models import Property

class RewritePropertyCommand(BaseCommand):
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
        url = f'{settings.OLLAMA_HOST}/api/generate'
        
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
        title_prompt = f"""
        Rewrite the following property title to be more engaging and descriptive, 
        while maintaining its core meaning. Keep it concise (max 50 characters):
        
        Original title: {property_item.property_title}
        """
        
        description_prompt = f"""
        Rewrite the following property description to be more detailed and professional,
        maintaining the key information but making it clearer and more engaging:
        
        Original description: {property_item.description}
        """
        
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
                return True
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error saving property {property_item.property_id}: {e}'
                ))
                return False
        return False

    def handle(self, *args, **options):
        model = options['model']
        batch_size = options['batch_size']
        
        properties = Property.objects.all()
        total_properties = properties.count()
        
        self.stdout.write(f'Starting to process {total_properties} properties...')
        
        success_count = 0
        for i in range(0, total_properties, batch_size):
            batch = properties[i:i + batch_size]
            for property_item in batch:
                if self.rewrite_property(property_item, model):
                    success_count += 1
            
            self.stdout.write(f'Processed {min(i + batch_size, total_properties)}/{total_properties} properties')
        
        self.stdout.write(self.style.SUCCESS(
            f'Completed processing with {success_count}/{total_properties} successful rewrites'
        ))