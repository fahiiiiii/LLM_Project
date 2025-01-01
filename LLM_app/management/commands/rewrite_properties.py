

# LLM_app/management/commandsrewrite_properties.py
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
    help = 'Generates unique hotel property titles and descriptions using Gemini API with rate limiting'
    
    def __init__(self):
        super().__init__()
        self.delay = 2
        self.max_retries = 3
        self.retry_delay = 60
        
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
    
    # def validate_content(self, text):
    #     """Check if content contains forbidden medical terms or lacks hotel terms"""
    #     text_lower = text.lower()
        
    #     found_medical_terms = [term for term in self.forbidden_terms if term in text_lower]
    #     if found_medical_terms:
    #         raise ValueError(f"Generated content contains medical terms: {found_medical_terms}")
            
    #     hotel_terms_found = any(term in text_lower for term in self.hotel_keywords)
    #     if not hotel_terms_found:
    #         raise ValueError("Generated content lacks hotel-related terms")
        
    #     return True
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def validate_content(self, text):
        """Check if content contains forbidden medical terms or lacks hotel terms"""
        text_lower = text.lower()
        
        # Reject IDs or irrelevant text
        if re.search(r'^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', text_lower):
            raise ValueError("Generated content contains an ID or debug-like text.")
        
        found_medical_terms = [term for term in self.forbidden_terms if term in text_lower]
        if found_medical_terms:
            raise ValueError(f"Generated content contains medical terms: {found_medical_terms}")
            
        hotel_terms_found = any(term in text_lower for term in self.hotel_keywords)
        if not hotel_terms_found:
            raise ValueError("Generated content lacks hotel-related terms")
        
        return True

    
    # def generate_content_with_retry(self, model, prompt):
    #     try:
    #         response = model.generate_content(prompt)
    #         content = response.text.strip()
            
    #         self.validate_content(content)
            
    #         time.sleep(self.delay + random.uniform(0.1, 1.0))
    #         return content
    #     except Exception as e:
    #         if '429' in str(e):
    #             self.stdout.write(self.style.WARNING(f"Rate limit hit. Waiting {self.retry_delay} seconds..."))
    #             time.sleep(self.retry_delay)
    #         raise e
    def generate_content_with_retry(self, model, prompt):
        try:
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            # Clean unwanted patterns
            content = re.sub(r'^.*?(\|\s*Okay,.*?options:|Name:|Title:).*?$', '', content, flags=re.IGNORECASE | re.MULTILINE).strip()

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
        
        context_prompt = """
        You are a luxury hotel description generator for hotels and resorts. Your task is to create compelling, 
        hospitality-focused content for high-end hotels and resorts. Never generate 
        medical-related content. Focus exclusively on accommodation, amenities, and 
        guest experiences.
        """
        
        model.generate_content(context_prompt)
        
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT property_id, property_title, description, property_type,
                       location, amenities, price_per_night 
                FROM "MOCK_DATA"
            ''')
            rows = cursor.fetchall()
        
        for row in rows:
            retries = 0
            while retries < self.max_retries:
                try:
                    property_id, current_title, current_description, property_type, \
                    location, amenities, price_per_night = row
                    
                    # Convert price_per_night to a price range description
                    if price_per_night < 100:
                        price_range = "Budget-friendly"
                    elif price_per_night < 200:
                        price_range = "Moderate"
                    elif price_per_night < 400:
                        price_range = "Upscale"
                    else:
                        price_range = "Luxury"
                    
                    title_prompt = f"""
                    Generate a luxurious hotel name based on these details:
                    Location: {location}
                    Price Range: {price_range}
                    Property Type: {property_type}
                    Amenities: {amenities}

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
                    # Remove unwanted text like introductions or IDs
                    new_title = re.sub(r'^(Okay.*?:|Here are some options.*?:|Hotel Name:)\s*', '', new_title, flags=re.IGNORECASE).strip()


                    # new_title = self.generate_content_with_retry(model, title_prompt)
                    # new_title = re.sub(r'^(Title:|Name:|Hotel Name:)\s*', '', new_title, flags=re.IGNORECASE).strip()
                    
                    description_prompt = f"""
                    Generate a luxury hotel description for:
                    Hotel Name: {new_title}
                    Location: {location}
                    Property Type: {property_type}
                    Price Range: {price_range}
                    Available Amenities: {amenities}

                    Requirements:
                    - Can add the hotel name in the first sentence
                    - Focus ONLY on hotel features and guest experience
                    - Describe actual amenities mentioned above
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