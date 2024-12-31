# # LLM_app/management/commandsrewrite_properties.py
# import os
# import time
# import random
# import google.generativeai as genai
# from django.core.management.base import BaseCommand
# from django.db import connection
# from dotenv import load_dotenv
# import re
# from google.api_core import retry

# class Command(BaseCommand):
#     help = 'Generates unique property titles and descriptions using Gemini API with rate limiting'
    
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
#             return response.text.strip()import os
import time
import random
import google.generativeai as genai
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from dotenv import load_dotenv
import re
from google.api_core import retry

class Command(BaseCommand):
    help = 'Generates unique hotel property titles and descriptions using Gemini API with rate limiting'
    
    def __init__(self):
        super().__init__()
        self.delay = 2
        self.max_retries = 3
        self.retry_delay = 60
        
        # Define hotel-specific terms and forbidden terms
        self.hotel_keywords = [
            'hotel', 'resort', 'suite', 'room', 'accommodation', 'stay', 'vacation',
            'hospitality', 'lodging', 'guest', 'amenities', 'comfort'
        ]
        
        self.forbidden_terms = [
            'medical', 'patient', 'diagnosis', 'treatment', 'injury', 'healing',
            'fracture', 'clinical', 'symptoms', 'disease', 'hospital', 'doctor',
            'surgery', 'therapeutic', 'rehabilitation', 'wound', 'care'
        ]
        
        self.hotel_amenities = [
            'swimming pool', 'spa', 'restaurant', 'fitness center', 'business center',
            'conference rooms', 'beach access', 'room service', 'concierge',
            'valet parking', 'bar/lounge', 'wifi', 'tennis court', 'golf course'
        ]
        
        self.hotel_features = [
            'ocean view', 'mountain view', 'city view', 'private balcony',
            'luxury bedding', 'gourmet kitchen', 'marble bathroom', 'walk-in shower',
            'king-size bed', 'mini bar', 'entertainment system'
        ]
    
    def validate_content(self, text):
        """Check if content contains forbidden medical terms or lacks hotel terms"""
        text_lower = text.lower()
        
        # Check for forbidden medical terms
        found_medical_terms = [term for term in self.forbidden_terms if term in text_lower]
        if found_medical_terms:
            raise ValueError(f"Generated content contains medical terms: {found_medical_terms}")
            
        # Check for presence of hotel-related terms
        hotel_terms_found = any(term in text_lower for term in self.hotel_keywords)
        if not hotel_terms_found:
            raise ValueError("Generated content lacks hotel-related terms")
        
        return True
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def generate_content_with_retry(self, model, prompt):
        try:
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            # Validate the generated content
            self.validate_content(content)
            
            time.sleep(self.delay + random.uniform(0.1, 1.0))
            return content
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
        
        # Add clear hotel context to model
        context_prompt = """
        You are a luxury hotel description generator. Your task is to create compelling, 
        hospitality-focused content for high-end hotels and resorts. Never generate 
        medical-related content. Focus exclusively on accommodation, amenities, and 
        guest experiences.
        """
        
        model.generate_content(context_prompt)
        
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT property_id, property_title, description, property_type,
                       location, star_rating, price_range 
                FROM "MOCK_DATA"
            ''')
            rows = cursor.fetchall()
        
        for row in rows:
            retries = 0
            while retries < self.max_retries:
                try:
                    property_id, current_title, current_description, property_type, \
                    location, star_rating, price_range = row
                    
                    # Enhanced hotel-specific title prompt
                    title_prompt = f"""
                    Generate a luxurious hotel name based on these details:
                    Location: {location}
                    Star Rating: {star_rating}
                    Price Range: {price_range}
                    Property Type: {property_type}

                    Requirements:
                    - Create an upscale HOTEL name only
                    - Must include words like "Hotel", "Resort", "Suites", or similar
                    - Highlight luxury and comfort
                    - Maximum 60 characters
                    - NO medical terms or references
                    - Must sound like a real hotel name

                    Example names:
                    - Grand Pacific Resort & Spa
                    - The Royal Peninsula Hotel
                    - Oceanview Luxury Suites
                    """

                    new_title = self.generate_content_with_retry(model, title_prompt)
                    new_title = re.sub(r'^(Title:|Name:|Hotel Name:)\s*', '', new_title, flags=re.IGNORECASE).strip()
                    
                    # Enhanced hotel-specific description prompt
                    description_prompt = f"""
                    Generate a luxury hotel description for:
                    Hotel Name: {new_title}
                    Location: {location}
                    Star Rating: {star_rating}
                    Price Range: {price_range}

                    Requirements:
                    - Can add the hotel name in the first 
                    - Focus ONLY on hotel features and guest experience
                    - Describe luxury amenities like: {', '.join(random.sample(self.hotel_amenities, 3))}
                    - Highlight room features like: {', '.join(random.sample(self.hotel_features, 3))}
                    - Mention nearby attractions and location benefits
                    - Use sophisticated hospitality language
                    - 150-200 words
                    - NO medical terms or healthcare references
                    - Must sound like a real hotel description

                    Example tone:
                    "Experience unparalleled luxury at our beachfront resort, where 
                    breathtaking ocean views meet world-class amenities..."
                    """
                    
                    new_description = self.generate_content_with_retry(model, description_prompt)
                    new_description = re.sub(r'^(Description:|Hotel Description:)\s*', '', new_description, flags=re.IGNORECASE).strip()
                    
                    with transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute(
                                'UPDATE "MOCK_DATA" SET property_title = %s, description = %s WHERE property_id = %s',
                                [new_title, new_description, property_id]
                            )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully updated hotel {property_id}:\nNew Title: {new_title}\n"
                            f"New Description: {new_description}\n"
                        )
                    )
                    break
                    
                except ValueError as ve:
                    self.stdout.write(self.style.WARNING(f"Content validation failed: {str(ve)}. Retrying..."))
                    retries += 1
                except Exception as e:
                    retries += 1
                    if retries >= self.max_retries:
                        self.stdout.write(
                            self.style.ERROR(f"Failed to process hotel {property_id} after {self.max_retries} attempts: {str(e)}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Retry {retries}/{self.max_retries} for hotel {property_id}")
                        )
                        time.sleep(self.retry_delay * retries)











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
#             cursor.execute('SELECT property_id, property_title, description FROM "MOCK_DATA"')
#             rows = cursor.fetchall()
        
#         # Process each property
#         for row in rows:
#             retries = 0
#             while retries < self.max_retries:
#                 try:
#                     property_id, current_title, current_description = row
                    
#                     # Create context-aware prompt for title generation
#                     title_prompt = f"""
#                     Generate a unique and attractive property title based on this information:
#                     Current Title: {current_title}
#                     Current Description: {current_description}
                    
#                     Rules:
#                     - Make it catchy and unique
#                     - Include a distinctive feature or selling point
#                     - Keep it under 60 characters
#                     - Don't use generic terms like 'property' or 'home'
#                     - Emphasize unique characteristics from the description
                    
#                     Generate only the title without any prefixes or explanations.
#                     """
                    
#                     # Generate new title with retry logic
#                     new_title = self.generate_content_with_retry(model, title_prompt)
#                     new_title = re.sub(r'^(Title:|New Title:|Property Title:)\s*', '', new_title, flags=re.IGNORECASE).strip()
                    
#                     # Create context-aware prompt for description generation
#                     description_prompt = f"""
#                     Generate an engaging property description based on this information:
#                     Property Title: {new_title}
#                     Current Description: {current_description}
                    
#                     Rules:
#                     - Highlight unique features and benefits
#                     - Include emotional appeal and lifestyle benefits
#                     - Keep it professional and factual
#                     - Incorporate key elements from the current description
#                     - Aim for 150-200 words
                    
#                     Generate only the description without any prefixes or explanations.
#                     """
                    
#                     # Generate new description with retry logic
#                     new_description = self.generate_content_with_retry(model, description_prompt)
#                     new_description = re.sub(r'^(Description:|New Description:|Property Description:)\s*', '', new_description, flags=re.IGNORECASE).strip()
                    
#                     # Update the database
#                     with connection.cursor() as cursor:
#                         cursor.execute(
#                             'UPDATE "MOCK_DATA" SET property_title = %s, description = %s WHERE property_id = %s',
#                             [new_title, new_description, property_id]
#                         )
                    
#                     self.stdout.write(
#                         self.style.SUCCESS(
#                             f"Successfully updated property {property_id}:\nNew Title: {new_title}\n"
#                         )
#                     )
#                     break  # Success, move to next property
                    
#                 except Exception as e:
#                     retries += 1
#                     if retries >= self.max_retries:
#                         self.stdout.write(
#                             self.style.ERROR(f"Failed to process property {property_id} after {self.max_retries} attempts: {str(e)}")
#                         )
#                     else:
#                         self.stdout.write(
#                             self.style.WARNING(f"Retry {retries}/{self.max_retries} for property {property_id}")
#                         )
#                         time.sleep(self.retry_delay * retries)  # Exponential backoff














# # import os
# # import google.generativeai as genai
# # from django.core.management.base import BaseCommand
# # from django.db import connection
# # from dotenv import load_dotenv
# # import re

# # class Command(BaseCommand):
# #     help = 'Generates unique property titles and descriptions using Gemini API'
    
# #     def handle(self, *args, **options):
# #         # Load environment variables and configure API
# #         load_dotenv()
# #         GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        
# #         if not GOOGLE_API_KEY:
# #             self.stdout.write(self.style.ERROR("Google API key not found in environment variables."))
# #             return
        
# #         # Configure Gemini AI
# #         genai.configure(api_key=GOOGLE_API_KEY)
# #         model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
# #         # Fetch all properties from MOCK_DATA table
# #         with connection.cursor() as cursor:
# #             cursor.execute('SELECT property_id, property_title, description FROM "MOCK_DATA"')
# #             rows = cursor.fetchall()
        
# #         # Process each property
# #         for row in rows:
# #             try:
# #                 property_id, current_title, current_description = row
                
# #                 # Create context-aware prompt for title generation
# #                 title_prompt = f"""
# #                 Generate a unique and attractive property title based on this information:
# #                 Current Title: {current_title}
# #                 Current Description: {current_description}
                
# #                 Rules:
# #                 - Make it catchy and unique
# #                 - Include a distinctive feature or selling point
# #                 - Keep it under 60 characters
# #                 - Don't use generic terms like 'property' or 'home'
# #                 - Emphasize unique characteristics from the description
                
# #                 Generate only the title without any prefixes or explanations.
# #                 """
                
# #                 # Generate new title
# #                 title_response = model.generate_content(title_prompt)
# #                 new_title = title_response.text.strip()
                
# #                 # Clean up any potential prefixes or formatting
# #                 new_title = re.sub(r'^(Title:|New Title:|Property Title:)\s*', '', new_title, flags=re.IGNORECASE).strip()
                
# #                 # Create context-aware prompt for description generation
# #                 description_prompt = f"""
# #                 Generate an engaging property description based on this information:
# #                 Property Title: {new_title}
# #                 Current Description: {current_description}
                
# #                 Rules:
# #                 - Highlight unique features and benefits
# #                 - Include emotional appeal and lifestyle benefits
# #                 - Keep it professional and factual
# #                 - Incorporate key elements from the current description
# #                 - Aim for 150-200 words
                
# #                 Generate only the description without any prefixes or explanations.
# #                 """
                
# #                 # Generate new description
# #                 description_response = model.generate_content(description_prompt)
# #                 new_description = description_response.text.strip()
                
# #                 # Clean up any potential prefixes or formatting
# #                 new_description = re.sub(r'^(Description:|New Description:|Property Description:)\s*', '', new_description, flags=re.IGNORECASE).strip()
                
# #                 # Update the database
# #                 with connection.cursor() as cursor:
# #                     cursor.execute(
# #                         'UPDATE "MOCK_DATA" SET property_title = %s, description = %s WHERE property_id = %s',
# #                         [new_title, new_description, property_id]
# #                     )
                
# #                 self.stdout.write(
# #                     self.style.SUCCESS(
# #                         f"Successfully updated property {property_id}:\nNew Title: {new_title}\n"
# #                     )
# #                 )
                
# #             except Exception as e:
# #                 self.stdout.write(
# #                     self.style.ERROR(f"Error processing property {property_id}: {str(e)}")
# #                 )
import os
import time
import random
import google.generativeai as genai
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from dotenv import load_dotenv
import re
from google.api_core import retry

class Command(BaseCommand):
    help = 'Generates unique property titles and descriptions using Gemini API with rate limiting'
    
    def __init__(self):
        super().__init__()
        self.delay = 2  # Base delay between requests in seconds
        self.max_retries = 3
        self.retry_delay = 60  # Delay in seconds after hitting rate limit
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def generate_content_with_retry(self, model, prompt):
        try:
            response = model.generate_content(prompt)
            time.sleep(self.delay + random.uniform(0.1, 1.0))  # Add jitter
            return response.text.strip()
        except Exception as e:
            if '429' in str(e):  # Rate limit error
                self.stdout.write(self.style.WARNING(f"Rate limit hit. Waiting {self.retry_delay} seconds..."))
                time.sleep(self.retry_delay)
            raise e
    
    def handle(self, *args, **options):
        # Load environment variables and configure API
        load_dotenv()
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        
        if not GOOGLE_API_KEY:
            self.stdout.write(self.style.ERROR("Google API key not found in environment variables."))
            return
        
        # Configure Gemini AI
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Fetch all properties from MOCK_DATA table
        with connection.cursor() as cursor:
            cursor.execute('SELECT property_id, property_title, description FROM "MOCK_DATA"')
            rows = cursor.fetchall()
        
        # Process each property
        for row in rows:
            retries = 0
            while retries < self.max_retries:
                try:
                    property_id, current_title, current_description = row
                    
                    # Create context-aware prompt for title generation
                    title_prompt = f"""
                    Generate a unique and attractive property title based on this information:
                    Current Title: {current_title}
                    Current Description: {current_description}
                    
                    Rules:
                    - Make it catchy and unique
                    - Include a distinctive feature or selling point
                    - Keep it under 60 characters
                    - Don't use generic terms like 'property' or 'home'
                    - Emphasize unique characteristics from the description
                    
                    Generate only the title without any prefixes or explanations.
                    """
                    
                    # Generate new title with retry logic
                    new_title = self.generate_content_with_retry(model, title_prompt)
                    new_title = re.sub(r'^(Title:|New Title:|Property Title:)\s*', '', new_title, flags=re.IGNORECASE).strip()
                    
                    # Create context-aware prompt for description generation
                    description_prompt = f"""
                    Generate an engaging property description based on this information:
                    Property Title: {new_title}
                    Current Description: {current_description}
                    
                    Rules:
                    - Highlight unique features and benefits
                    - Include emotional appeal and lifestyle benefits
                    - Keep it professional and factual
                    - Incorporate key elements from the current description
                    - Aim for 150-200 words
                    
                    Generate only the description without any prefixes or explanations.
                    """
                    
                    # Generate new description with retry logic
                    new_description = self.generate_content_with_retry(model, description_prompt)
                    new_description = re.sub(r'^(Description:|New Description:|Property Description:)\s*', '', new_description, flags=re.IGNORECASE).strip()
                    
                    # Update the database
                    with transaction.atomic():  # Start a transaction
                        with connection.cursor() as cursor:
                            cursor.execute(
                                'UPDATE "MOCK_DATA" SET property_title = %s, description = %s WHERE property_id = %s',
                                [new_title, new_description, property_id]
                            )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully updated property {property_id}:\nNew Title: {new_title}\n"
                            f"Successfully updated property {property_id}:\nNew Description: {new_description}\n"
                        )
                    )
                    break  # Success, move to next property
                    
                except Exception as e:
                    retries += 1
                    if retries >= self.max_retries:
                        self.stdout.write(
                            self.style.ERROR(f"Failed to process property {property_id} after {self.max_retries} attempts: {str(e)}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Retry {retries}/{self.max_retries} for property {property_id}")
                        )
                        time.sleep(self.retry_delay * retries)  # Exponential backoff