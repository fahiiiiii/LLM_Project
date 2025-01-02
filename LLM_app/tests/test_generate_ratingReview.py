# test_generate_ratingReview.py

#import json
# import os
# from unittest import mock
# from django.core.management import call_command
# from django.test import TestCase, override_settings
# from django.db import connection
# from LLM_app.models import LLM_app_propertyreview
# from google.generativeai import GenerativeModel
# from google.api_core import retry
# from LLM_app.management.commands.generate_ratingReview import Command
# import time
# from django.test import TestCase  # Import TestCase from django
# from unittest import mock # keep unittest.mock since this is not django specific
from django.test import TestCase, override_settings # Removed override settings
from unittest import mock
from django.core.management import call_command
from django.db import connection
from LLM_app.models import LLM_app_propertyreview
from google.generativeai import GenerativeModel
from google.api_core import retry
from LLM_app.management.commands.generate_ratingReview import Command
import time
import random


# @override_settings(
#     DATABASES={
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': ':memory:'
#         }
#     }
# )
class GenerateRatingReviewTests(TestCase):

    def setUp(self):
        self.command = Command()
        
        with connection.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE "MOCK_DATA" (
                property_id INTEGER PRIMARY KEY,
                property_title VARCHAR(255),
                location VARCHAR(255),
                amenities TEXT,
                description TEXT,
                price_per_night DECIMAL,
                property_type VARCHAR(255)
            );
            """)
            cursor.execute("""
                INSERT INTO "MOCK_DATA" (property_id, property_title, location, amenities, description, price_per_night, property_type)
                VALUES
                (1, 'Cozy Cabin', 'Mountains', 'WiFi, Fireplace', 'A great cabin in the woods', 150.00, 'cabin'),
                (2, 'Beach House', 'Beach', 'Pool, Ocean View', 'Beautiful house by the beach', 300.00, 'house'),
                (3, 'City Apartment', 'Downtown', 'Gym, Balcony', 'Modern apartment in the city center', 200.00, 'apartment')
            """)


    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE "MOCK_DATA";')
        

    def test_clean_response(self):
        self.assertEqual(self.command.clean_response("```json\n{\"key\": \"value\"}\n```"), '{"key": "value"}')
        self.assertEqual(self.command.clean_response("  {\"key\": \"value\"}  "), '{"key": "value"}')
        self.assertEqual(self.command.clean_response("{\"key\": \"value\"}"), '{"key": "value"}')
        self.assertIsNone(self.command.clean_response(None))
        self.assertEqual(self.command.clean_response(""), '')
        self.assertEqual(self.command.clean_response(" ```json {\"key\": \"value\"} ``` "), '{"key": "value"}')


    def test_validate_review_data(self):
        # Valid case
        rating, review = self.command.validate_review_data(4.5, "This is a good review.")
        self.assertEqual(rating, 4.5)
        self.assertEqual(review, "This is a good review.")

        # Invalid rating (out of range)
        with self.assertRaises(ValueError) as context:
            self.command.validate_review_data(6, "Review text")
        self.assertIn("Rating 6 is out of valid range (1-5)", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.command.validate_review_data(0, "Review text")
        self.assertIn("Rating 0 is out of valid range (1-5)", str(context.exception))

        # Invalid rating (not a number)
        with self.assertRaises(ValueError) as context:
            self.command.validate_review_data("invalid", "Review text")
        self.assertIn("Invalid rating value: invalid", str(context.exception))
        
        # No review
        with self.assertRaises(ValueError) as context:
            self.command.validate_review_data(4, "")
        self.assertEqual(str(context.exception), "Review text is empty")

        # Null Rating
        rating, review = self.command.validate_review_data(None, "Some review")
        self.assertIsNone(rating)
        self.assertEqual("Some review", review)
        

    @mock.patch("LLM_app.management.commands.generate_ratingReview.time.sleep")
    def test_generate_content_with_retry(self, mock_sleep):
        mock_model = mock.MagicMock()
        mock_model.generate_content.return_value.text = "Test Response"
        
        response = self.command.generate_content_with_retry(mock_model, "Test Prompt")
        self.assertEqual(response, "Test Response")
        mock_model.generate_content.assert_called_once_with("Test Prompt")
        mock_sleep.assert_called()
        
        mock_model.generate_content.side_effect = Exception("429 Rate Limit")
        
        with self.assertRaises(Exception) as context:
            self.command.generate_content_with_retry(mock_model, "Test Prompt")
        self.assertIn("429 Rate Limit", str(context.exception))
        mock_sleep.assert_called()  # Check that sleep was called after rate limit


    @mock.patch("LLM_app.management.commands.generate_ratingReview.Command.generate_content_with_retry")
    def test_create_review_success(self, mock_generate_content):
        mock_generate_content.return_value = '```json\n{"rating": 4.2, "review": "Good place"}\n```'
        
        review = self.command.create_review(1, mock.MagicMock(), (1, 'Test Title', 'Test Loc', 'Test Am', 'Test Desc', 100.00, 'Test Type'))
        
        self.assertEqual(review.property_id, 1)
        self.assertEqual(review.rating, 4.2)
        self.assertEqual(review.review, "Good place")
        mock_generate_content.assert_called()
    

    @mock.patch("LLM_app.management.commands.generate_ratingReview.Command.generate_content_with_retry")
    def test_create_review_empty_response(self, mock_generate_content):
        mock_generate_content.return_value = None

        review = self.command.create_review(1, mock.MagicMock(), (1, 'Test Title', 'Test Loc', 'Test Am', 'Test Desc', 100.00, 'Test Type'))

        self.assertEqual(review.property_id, 1)
        self.assertIsNone(review.rating)
        self.assertEqual(review.review, "Could not generate review - Empty API response")
        mock_generate_content.assert_called()

    @mock.patch("LLM_app.management.commands.generate_ratingReview.Command.generate_content_with_retry")
    def test_create_review_invalid_json(self, mock_generate_content):
       mock_generate_content.return_value = 'Invalid JSON'

       review = self.command.create_review(1, mock.MagicMock(), (1, 'Test Title', 'Test Loc', 'Test Am', 'Test Desc', 100.00, 'Test Type'))

       self.assertEqual(review.property_id, 1)
       self.assertIsNone(review.rating)
       self.assertEqual(review.review, "Could not generate review - Invalid JSON response")
       mock_generate_content.assert_called()
    

    @mock.patch("LLM_app.management.commands.generate_ratingReview.Command.generate_content_with_retry")
    def test_create_review_validation_error(self, mock_generate_content):
       mock_generate_content.return_value = '```json\n{"rating": 6, "review": "Invalid review"}\n```'

       review = self.command.create_review(1, mock.MagicMock(), (1, 'Test Title', 'Test Loc', 'Test Am', 'Test Desc', 100.00, 'Test Type'))

       self.assertEqual(review.property_id, 1)
       self.assertIsNone(review.rating)
       self.assertIn("Could not generate review - Rating 6 is out of valid range (1-5)", review.review)
       mock_generate_content.assert_called()
    

    @mock.patch("LLM_app.management.commands.generate_ratingReview.Command.generate_content_with_retry")
    def test_create_review_unexpected_error(self, mock_generate_content):
        mock_generate_content.side_effect = Exception("Unexpected Error")
        review = self.command.create_review(1, mock.MagicMock(), (1, 'Test Title', 'Test Loc', 'Test Am', 'Test Desc', 100.00, 'Test Type'))
        
        self.assertEqual(review.property_id, 1)
        self.assertIsNone(review.rating)
        self.assertEqual(review.review, "Could not generate review - Unexpected error occurred")
        mock_generate_content.assert_called()


    @mock.patch('LLM_app.management.commands.generate_ratingReview.os.getenv')
    @mock.patch('LLM_app.management.commands.generate_ratingReview.genai.configure')
    @mock.patch('LLM_app.management.commands.generate_ratingReview.genai.GenerativeModel')
    @mock.patch('LLM_app.management.commands.generate_ratingReview.Command.create_review')
    @mock.patch('LLM_app.management.commands.generate_ratingReview.transaction.atomic')
    def test_handle_command_success(self, mock_transaction, mock_create_review, mock_genai_model, mock_genai_config, mock_getenv):
        mock_getenv.return_value = "test_api_key"
        mock_model_instance = mock.MagicMock()
        mock_genai_model.return_value = mock_model_instance
        
        mock_review1 = mock.MagicMock(spec=LLM_app_propertyreview)
        mock_review2 = mock.MagicMock(spec=LLM_app_propertyreview)

        mock_create_review.side_effect = [mock_review1, mock_review2, None]

        call_command('generate_ratingReview')

        mock_getenv.assert_called_once_with("GOOGLE_API_KEY")
        mock_genai_config.assert_called_once_with(api_key="test_api_key")
        mock_genai_model.assert_called_once_with('gemini-2.0-flash-exp')
        self.assertEqual(mock_create_review.call_count, 3)
        mock_transaction.assert_called_once()
        LLM_app_propertyreview.objects.bulk_create.assert_called_once_with([mock_review1, mock_review2], ignore_conflicts=True)

    
    @mock.patch('LLM_app.management.commands.generate_ratingReview.os.getenv')
    def test_handle_command_no_api_key(self, mock_getenv):
        mock_getenv.return_value = None

        call_command('generate_ratingReview')
        
        mock_getenv.assert_called_once_with("GOOGLE_API_KEY")
        self.assertFalse(LLM_app_propertyreview.objects.exists())