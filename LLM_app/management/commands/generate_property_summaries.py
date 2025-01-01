# LLM_app/management/commands/generate_property_summaries.py

import os
import time
import random
import google.generativeai as genai
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from dotenv import load_dotenv
from google.api_core import retry
from LLM_app.models import LLM_app_propertysummary
import re
import json


class Command(BaseCommand):
    help = 'Generates property summaries with summarized inferred amenities using Gemini API'

    def __init__(self):
        super().__init__()
        self.delay = 2
        self.max_retries = 3
        self.retry_delay = 60

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def generate_content_with_retry(self, model, prompt):
        try:
            response = model.generate_content(prompt)
            time.sleep(self.delay + random.uniform(0.1, 1.0))
            return response.text.strip()
        except Exception as e:
            if '429' in str(e):
                self.stdout.write(self.style.WARNING(f"Rate limit hit. Waiting {self.retry_delay} seconds..."))
                time.sleep(self.retry_delay)
            raise e

    def handle(self, *args, **options):
        load_dotenv()
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

        if not GOOGLE_API_KEY:
            self.stdout.write(self.style.ERROR("Google API key not found in environment variables."))
            return

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Updated SQL query to match actual database schema
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT property_id, property_title, location, amenities, 
                       description, price_per_night, property_type 
                FROM "MOCK_DATA"
            ''')
            properties = cursor.fetchall()

        summaries_to_create = []
        
        for property_data in properties:
            property_id, property_title, location, amenities, description, price_per_night, property_type = property_data
            retries = 0
            while retries < self.max_retries:
                try:
                    prompt = f"""
                       Create a comprehensive summary of a property based on the following information:
                        Property ID: {property_id}
                        Property Title: {property_title}
                        Property Type: {property_type}
                        Location: {location}
                        Price per Night: ${price_per_night}
                        Amenities: {amenities}

                        Rules:
                            - Focus on providing a summary based on the rating mostly , the the review ,location and  amenities.
                            - Focus on providing a summary based on the property type, location, and amenities
                            - Highlight the value proposition considering the price per night
                            - Emphasize unique features or amenities that set this property apart
                            - Make sure you do not include the word 'description' in the summary
                            - Keep the summary concise, around 100-150 words
                            - Avoid generic statements

                        Generate only the summary without any prefixes or explanations.
                        """

                    summary_text = self.generate_content_with_retry(model, prompt)
                    summary_text = re.sub(r'^(Summary:|Property Summary:|Hotel Summary:)\s*', '', summary_text,
                                        flags=re.IGNORECASE).strip()

                    summaries_to_create.append(LLM_app_propertysummary(property_id=property_id, summary=summary_text))

                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully generated summary for property {property_id}")
                    )
                    break
                except Exception as e:
                    retries += 1
                    if retries >= self.max_retries:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to generate summary for property {property_id} after {self.max_retries} attempts: {str(e)}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Retry {retries}/{self.max_retries} for property {property_id}")
                        )
                        time.sleep(self.retry_delay * retries)

        with transaction.atomic():
            LLM_app_propertysummary.objects.bulk_create(summaries_to_create, ignore_conflicts=True)






