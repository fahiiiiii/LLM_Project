# LLM_app/management/commands/generate_property_summaries.py
# # LLM_app/management/commands/generate_property_summaries.py
# import os
# import time
# import random
# import google.generativeai as genai
# from django.core.management.base import BaseCommand
# from django.db import connection, transaction
# from dotenv import load_dotenv
# from google.api_core import retry
# from LLM_app.models import PropertySummary
# import re
# import json


# class Command(BaseCommand):
#     help = 'Generates property summaries with summarized inferred amenities using Gemini API'

#     def __init__(self):
#         super().__init__()
#         self.delay = 2
#         self.max_retries = 3
#         self.retry_delay = 60

#     @retry.Retry(predicate=retry.if_exception_type(Exception))
#     def generate_content_with_retry(self, model, prompt):
#         try:
#             response = model.generate_content(prompt)
#             time.sleep(self.delay + random.uniform(0.1, 1.0))
#             return response.text.strip()
#         except Exception as e:
#             if '429' in str(e):
#                 self.stdout.write(self.style.WARNING(f"Rate limit hit. Waiting {self.retry_delay} seconds..."))
#                 time.sleep(self.retry_delay)
#             raise e

#     def generate_amenities(self, model, rating, review, description):
#         """Generates and summarizes potential amenities based on rating, review and description."""
#         amenities_prompt = f"""Based on this property's rating: {rating}, its review: {review}, and the details provided,
#             suggest 3 relevant amenities that a place with these qualities might have.
#             Format your output as a valid json array of strings
#             Example:
#             ["Wi-Fi", "Breakfast included", "Pet Friendly"]

#             Amenities:
#         """
#         # try:
#         #     amenities_response = self.generate_content_with_retry(model, amenities_prompt)
#         #     amenities_list = json.loads(amenities_response)

#         #     summary_prompt = f"""
#         #       Summarize these amenities in short description in one sentence: {amenities_list}
#         #       Summary:
#         #      """

#         #     summary = self.generate_content_with_retry(model, summary_prompt)

#         #     return summary

#         # except Exception as e:
#         #     self.stdout.write(
#         #         self.style.ERROR(f"Failed to generate/summarize amenities {str(e)}")
#         #     )

#         #     return None

#     def handle(self, *args, **options):
#         load_dotenv()
#         GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

#         if not GOOGLE_API_KEY:
#             self.stdout.write(self.style.ERROR("Google API key not found in environment variables."))
#             return

#         genai.configure(api_key=GOOGLE_API_KEY)
#         model = genai.GenerativeModel('gemini-2.0-flash-exp')

#         # Fetch data from MOCK_DATA table
#         with connection.cursor() as cursor:
#             cursor.execute('SELECT property_id, rating,location, review,amenities ,description, property_title FROM "MOCK_DATA"')
#             properties = cursor.fetchall()

#         summaries_to_create = []
        
#         for property_data in properties:
          
#             property_id, rating, review, description, amenities,property_title ,location = property_data
#             retries = 0
#             while retries < self.max_retries:
#                 try:

#                     # amenities = self.generate_amenities(model, rating, review, description)

#                     prompt = f"""
#                        Create a comprehensive summary of a property based on the following information:
#                         Property ID: {property_id}
#                         Property Title: {property_title}
#                         Rating: {rating}
#                         Review: {review}
#                         Location:{location}
#                         Amenities: {amenities}

#                         Rules:
#                             - Focus on providing a summary based on the rating mostly , the the review ,location and  amenities.
#                             - Explain why this property has the rating it has based on the reviews and the amenities.
#                             - Highlight the key positives or negatives mentioned in the review, and inferred amenities.
#                              - Make sure you do not include the word 'description' on the summary.
#                             - Keep the summary concise, around 100-150 words.
#                             - Avoid generic statements like "This is a good hotel." or "This is bad hotel."

#                         Generate only the summary without any prefixes or explanations.
#                         """

#                     summary_text = self.generate_content_with_retry(model, prompt)
#                     summary_text = re.sub(r'^(Summary:|Property Summary:|Hotel Summary:)\s*', '', summary_text,
#                                         flags=re.IGNORECASE).strip()

#                     summaries_to_create.append(PropertySummary(property_id=property_id, summary=summary_text))

#                     self.stdout.write(
#                         self.style.SUCCESS(f"Successfully generated summary for property {property_id}")
#                     )
#                     break
#                 except Exception as e:
#                     retries += 1
#                     if retries >= self.max_retries:
#                         self.stdout.write(
#                             self.style.ERROR(
#                                 f"Failed to generate summary for property {property_id} after {self.max_retries} attempts: {str(e)}")
#                         )
#                     else:
#                         self.stdout.write(
#                             self.style.WARNING(f"Retry {retries}/{self.max_retries} for property {property_id}")
#                         )
#                         time.sleep(self.retry_delay * retries)


#         with transaction.atomic():
#             PropertySummary.objects.bulk_create(summaries_to_create, ignore_conflicts=True)












import os
import time
import random
import google.generativeai as genai
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from dotenv import load_dotenv
from google.api_core import retry
from LLM_app.models import PropertySummary
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

                    summaries_to_create.append(PropertySummary(property_id=property_id, summary=summary_text))

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
            PropertySummary.objects.bulk_create(summaries_to_create, ignore_conflicts=True)


















# LLM_app/management/commands/generate_property_summaries.py
# import os
# import time
# import random
# import google.generativeai as genai
# from django.core.management.base import BaseCommand
# from django.db import connection, transaction
# from dotenv import load_dotenv
# from google.api_core import retry
# from LLM_app.models import PropertySummary  # Import the model
# import re


# class Command(BaseCommand):
#     help = 'Generates property summaries using Gemini API based on ratings and reviews'

#     def __init__(self):
#         super().__init__()
#         self.delay = 2
#         self.max_retries = 3
#         self.retry_delay = 60

#     @retry.Retry(predicate=retry.if_exception_type(Exception))
#     def generate_content_with_retry(self, model, prompt):
#         try:
#             response = model.generate_content(prompt)
#             time.sleep(self.delay + random.uniform(0.1, 1.0))
#             return response.text.strip()
#         except Exception as e:
#             if '429' in str(e):
#                 self.stdout.write(self.style.WARNING(f"Rate limit hit. Waiting {self.retry_delay} seconds..."))
#                 time.sleep(self.retry_delay)
#             raise e

#     def handle(self, *args, **options):
#         load_dotenv()
#         GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

#         if not GOOGLE_API_KEY:
#             self.stdout.write(self.style.ERROR("Google API key not found in environment variables."))
#             return

#         genai.configure(api_key=GOOGLE_API_KEY)
#         model = genai.GenerativeModel('gemini-2.0-flash-exp')

#         # Fetch data from MOCK_DATA table
#         with connection.cursor() as cursor:
#             cursor.execute('SELECT property_id, rating, review, description, property_title FROM "MOCK_DATA"')
#             properties = cursor.fetchall()

#         summaries_to_create = []

#         for property_data in properties:
#             retries = 0
#             while retries < self.max_retries:
#                 try:
#                     property_id, rating, review, description, property_title = property_data

#                     prompt = f"""
#                        Create a comprehensive summary of a hotel property based on the following information:
#                         Property ID: {property_id}
#                         Property Title: {property_title}
#                         Description: {description}
#                         Rating: {rating}
#                         Review: {review}
                        
#                         Rules:
#                             - Focus on providing a summary based on the rating and the review, and the description.
#                             - Explain why this property have the rating it has based on the reviews, descriptions.
#                             - Highlight the key positives or negatives mentioned in the review and description.
#                             - Keep the summary concise, around 100-150 words.
#                             - Avoid generic statements like "This is a good hotel." or "This is bad hotel."

#                         Generate only the summary without any prefixes or explanations.
#                         """


#                     summary_text = self.generate_content_with_retry(model, prompt)
#                     summary_text = re.sub(r'^(Summary:|Property Summary:|Hotel Summary:)\s*', '', summary_text, flags=re.IGNORECASE).strip()

                    
#                     summaries_to_create.append(PropertySummary(property_id=property_id, summary=summary_text))
                    

#                     self.stdout.write(
#                         self.style.SUCCESS(f"Successfully generated summary for property {property_id}")
#                     )
#                     break
#                 except Exception as e:
#                     retries += 1
#                     if retries >= self.max_retries:
#                         self.stdout.write(
#                             self.style.ERROR(f"Failed to generate summary for property {property_id} after {self.max_retries} attempts: {str(e)}")
#                         )
#                     else:
#                          self.stdout.write(
#                             self.style.WARNING(f"Retry {retries}/{self.max_retries} for property {property_id}")
#                         )
#                          time.sleep(self.retry_delay * retries)

#         with transaction.atomic():
#            PropertySummary.objects.bulk_create(summaries_to_create, ignore_conflicts=True)



# import os
# import time
# import random
# import google.generativeai as genai
# from django.core.management.base import BaseCommand
# from django.db import connection, transaction
# from dotenv import load_dotenv
# import re
# from google.api_core import retry
# from LLM_app.models import PropertySummary  # Import your new model

# class Command(BaseCommand):
#     help = 'Generates property summaries using Gemini API and stores them in a new table'
    
#     def __init__(self):
#         super().__init__()
#         self.delay = 2  # Base delay between requests in seconds
#         self.max_retries = 3
#         self.retry_delay = 60  # Delay in seconds after hitting rate limit
    
#     @retry.Retry(predicate=retry.if_exception_type(Exception))
#     def generate_content_with_retry(self, model, prompt):
#         try:
#             response = model.generate_content(prompt)
#             time.sleep(self.delay + random.uniform(0.1, 1.0))  # Add jitter
#             return response.text.strip()
#         except Exception as e:
#             if '429' in str(e):  # Rate limit error
#                 self.stdout.write(self.style.WARNING(f"Rate limit hit. Waiting {self.retry_delay} seconds..."))
#                 time.sleep(self.retry_delay)
#             raise e
    
#     def handle(self, *args, **options):
#         # Load environment variables and configure API
#         load_dotenv()
#         GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        
#         if not GOOGLE_API_KEY:
#             self.stdout.write(self.style.ERROR("Google API key not found in environment variables."))
#             return
        
#         # Configure Gemini AI
#         genai.configure(api_key=GOOGLE_API_KEY)
#         model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
#         # Fetch all properties from MOCK_DATA table
#         with connection.cursor() as cursor:
#             cursor.execute('SELECT property_id, property_title, description, rating, review FROM "MOCK_DATA"')
#             rows = cursor.fetchall()
        
#         # Process each property
#         for row in rows:
#             retries = 0
#             while retries < self.max_retries:
#                 try:
#                     property_id, property_title, description, rating, review = row
                    
#                     # Create context-aware prompt for summary generation
#                     summary_prompt = f"""
#                     Generate a concise summary of the following property details:
#                     Property Title: {property_title}
#                     Description: {description}
#                     Rating: {rating}
#                     Reviews: {review}
                    
#                     Rules:
#                     - Highlight the key features and selling points
#                     - Keep it factual and engaging.
#                     - Aim for approximately 100 to 150 words.
#                     - Combine the information and write it as a paragraph.
                    
#                     Generate only the summary without any prefixes or explanations.
#                     """
                    
#                     # Generate new summary with retry logic
#                     new_summary = self.generate_content_with_retry(model, summary_prompt)
#                     new_summary = re.sub(r'^(Summary:|New Summary:|Property Summary:)\s*', '', new_summary, flags=re.IGNORECASE).strip()
                    
#                    # Save the summary to the new table
#                     with transaction.atomic():
#                         try:
#                            PropertySummary.objects.update_or_create(
#                                 property_id=property_id,
#                                 defaults={'summary': new_summary}
#                             )
#                            self.stdout.write(
#                                 self.style.SUCCESS(f"Successfully updated summary for property {property_id}")
#                            )
#                         except Exception as e:
#                             self.stdout.write(
#                                 self.style.ERROR(f"Failed to save summary for property {property_id}: {str(e)}")
#                                 )
                                                        
#                     break  # Success, move to next property

#                 except Exception as e:
#                     retries += 1
#                     if retries >= self.max_retries:
#                          self.stdout.write(
#                               self.style.ERROR(f"Failed to process property {property_id} after {self.max_retries} attempts: {str(e)}")
#                          )
#                     else:
#                          self.stdout.write(
#                               self.style.WARNING(f"Retry {retries}/{self.max_retries} for property {property_id}")
#                          )
#                          time.sleep(self.retry_delay * retries)  # Exponential backoff