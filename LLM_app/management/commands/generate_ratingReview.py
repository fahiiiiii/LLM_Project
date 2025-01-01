# # LLM_app/management/commands/generate_ratingReview.py
import os
import time
import random
import google.generativeai as genai
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from dotenv import load_dotenv
from google.api_core import retry
from LLM_app.models import LLM_app_propertyreview
import json
import re

class Command(BaseCommand):
    help = 'Generates property ratings and reviews using Gemini API'

    def __init__(self):
        super().__init__()
        self.delay = 2
        self.max_retries = 3
        self.retry_delay = 60

    def clean_response(self, response):
        """Clean the API response by removing markdown code blocks."""
        if not response:
            return None
        # Remove markdown code block syntax
        cleaned = re.sub(r'```json\s*|\s*```', '', response)
        return cleaned.strip()

    def validate_review_data(self, rating, review_text):
        """Validate the rating and review text."""
        if rating is not None:
            try:
                rating = float(rating)
                if not 1 <= rating <= 5:
                    raise ValueError(f"Rating {rating} is out of valid range (1-5)")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid rating value: {rating}. Error: {str(e)}")

        if not review_text:
            raise ValueError("Review text is empty")
        
        return rating, review_text

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def generate_content_with_retry(self, model, prompt):
        """Generate content with retry logic and rate limiting."""
        try:
            response = model.generate_content(prompt)
            time.sleep(self.delay + random.uniform(0.1, 1.0))
            return response.text.strip()
        except Exception as e:
            if '429' in str(e):
                self.stdout.write(self.style.WARNING(
                    f"Rate limit hit. Waiting {self.retry_delay} seconds..."
                ))
                time.sleep(self.retry_delay)
            raise e

    def create_review(self, property_id, model, property_data):
        """Create a single review with error handling."""
        property_id, title, location, amenities, description, price, prop_type = property_data
        
        prompt = f"""
            Based on the following property information, generate a rating out of 5 and provide a review explaining the rating.
            Property ID: {property_id}
            Property Title: {title}
            Property Type: {prop_type}
            Location: {location}
            Price per Night: ${price}
            Amenities: {amenities}
            Description: {description}
            
            Instructions:
                - Rate the property on a scale of 1 to 5, where 5 is the best. You can give floating point numbers like 4.2, 3.5, etc.
                - Provide a concise review of why the property received the rating.
                - The rating should be based on amenities, location, property type, price and the overall description
                - Output should always be in JSON format.
                - If you cannot generate a review or rating due to lack of information return the following JSON:
                   {{"rating": null, "review": "Could not generate review."}}
                - Otherwise return your rating and review in the following JSON format:
                   {{"rating": rating_value, "review": "review_text"}}
        """

        try:
            review_response = self.generate_content_with_retry(model, prompt)
            
            if not review_response:
                self.stdout.write(self.style.ERROR(
                    f"Empty response from Gemini API for property {property_id}"
                ))
                return LLM_app_propertyreview(
                    property_id=property_id,
                    rating=None,
                    review="Could not generate review - Empty API response"
                )

            # Clean and parse response
            cleaned_response = self.clean_response(review_response)
            if not cleaned_response:
                raise ValueError("Failed to clean API response")

            review_json = json.loads(cleaned_response)
            rating = review_json.get("rating")
            review_text = review_json.get("review")

            # Validate the data
            rating, review_text = self.validate_review_data(rating, review_text)

            self.stdout.write(self.style.SUCCESS(
                f"Successfully generated review for property {property_id}"
            ))
            
            return LLM_app_propertyreview(
                property_id=property_id,
                rating=rating,
                review=review_text
            )

        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(
                f"JSON parsing error for property {property_id}: {str(e)}"
            ))
            return LLM_app_propertyreview(
                property_id=property_id,
                rating=None,
                review=f"Could not generate review - Invalid JSON response"
            )
        except ValueError as e:
            self.stdout.write(self.style.ERROR(
                f"Validation error for property {property_id}: {str(e)}"
            ))
            return LLM_app_propertyreview(
                property_id=property_id,
                rating=None,
                review=f"Could not generate review - {str(e)}"
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Unexpected error for property {property_id}: {str(e)}"
            ))
            return LLM_app_propertyreview(
                property_id=property_id,
                rating=None,
                review=f"Could not generate review - Unexpected error occurred"
            )

    def handle(self, *args, **options):
        """Main command handler."""
        load_dotenv()
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

        if not GOOGLE_API_KEY:
            self.stdout.write(self.style.ERROR(
                "Google API key not found in environment variables."
            ))
            return

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT property_id, property_title, location, amenities, 
                    description, price_per_night, property_type 
                FROM "MOCK_DATA"
            ''')
            properties = cursor.fetchall()

        reviews_to_create = []
        for property_data in properties:
            review = self.create_review(property_data[0], model, property_data)
            if review:
                reviews_to_create.append(review)

        with transaction.atomic():
            LLM_app_propertyreview.objects.bulk_create(
                reviews_to_create, 
                ignore_conflicts=True
            )


