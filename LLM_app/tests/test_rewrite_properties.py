# # LLM_app/tests/test_rewrite_properties.py
# import pytest
# from unittest.mock import patch, MagicMock
# from django.core.management import call_command
# from django.db import connection
# from LLM_app.management.commands import rewrite_properties
# from io import StringIO
# import os
# from dotenv import load_dotenv

# load_dotenv()

# @pytest.fixture
# def mock_env():
#     with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"}):
#         yield


# @pytest.fixture
# def mock_gemini_model():
#     model_mock = MagicMock()
#     model_mock.generate_content.side_effect = lambda prompt: MagicMock(text=f"Mocked response: {prompt}")
#     return model_mock


# @pytest.fixture
# def mock_db_data():
#     with connection.cursor() as cursor:
#         cursor.execute(
#             '''
#             CREATE TABLE IF NOT EXISTS MOCK_DATA (
#                 property_id VARCHAR(255) PRIMARY KEY,
#                 property_title VARCHAR(255),
#                 description TEXT,
#                 property_type VARCHAR(255),
#                 location VARCHAR(255),
#                 amenities TEXT,
#                 price_per_night INTEGER
#                 )
#             '''
#         )
#         cursor.execute(
#             """
#             INSERT INTO MOCK_DATA (property_id, property_title, description, property_type, location, amenities, price_per_night)
#             VALUES
#             ('1234', 'Old Title', 'Old Description', 'Hotel', 'London', 'wifi', 150),
#             ('5678', 'Old Title2', 'Old Description2', 'Resort', 'Paris', 'gym, spa', 80),
#             ('9101', 'Old Title3', 'Old Description3', 'Apartment', 'New York', 'parking', 300),
#             ('1121', 'Old Title4', 'Old Description4', 'Apartment', 'Tokyo', 'pool', 500)
#             """
#         )
#     yield
#     with connection.cursor() as cursor:
#         cursor.execute('DROP TABLE MOCK_DATA')

# @pytest.mark.django_db
# def test_command_success(mock_gemini_model, mock_env, mock_db_data):
#     with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
#         out = StringIO()
#         call_command('rewrite_properties', stdout=out)
#         assert "Successfully updated hotel 1234" in out.getvalue()
#         assert "Successfully updated hotel 5678" in out.getvalue()
#         assert "Successfully updated hotel 9101" in out.getvalue()
#         assert "Successfully updated hotel 1121" in out.getvalue()

# @pytest.mark.django_db
# def test_command_no_api_key(mock_gemini_model, mock_db_data):
#     with patch.dict(os.environ, {}, clear=True):
#             out = StringIO()
#             call_command('rewrite_properties', stdout=out)
#             assert "Google API key not found in environment variables." in out.getvalue()

# @pytest.mark.django_db
# def test_content_validation_success(mock_gemini_model, mock_env, mock_db_data):
#         command = rewrite_properties.Command()
#         assert command.validate_content("This is a luxury hotel stay with amazing views.") == True
#         assert command.validate_content("Experience the comfort of this hotel.") == True

# @pytest.mark.django_db
# def test_content_validation_medical_terms(mock_gemini_model, mock_env, mock_db_data):
#         command = rewrite_properties.Command()
#         with pytest.raises(ValueError, match="Generated content contains medical terms: \['medical'\]"):
#             command.validate_content("This hotel has a medical spa")

#         with pytest.raises(ValueError, match="Generated content contains medical terms: \['patient', 'healing'\]"):
#              command.validate_content("This is a patient healing center")

# @pytest.mark.django_db
# def test_content_validation_no_hotel_terms(mock_gemini_model, mock_env, mock_db_data):
#         command = rewrite_properties.Command()
#         with pytest.raises(ValueError, match="Generated content lacks hotel-related terms"):
#              command.validate_content("This is a great place to have your birthday party")

# @pytest.mark.django_db
# def test_content_validation_rejects_ids(mock_gemini_model, mock_env, mock_db_data):
#     command = rewrite_properties.Command()
#     with pytest.raises(ValueError, match="Generated content contains an ID or debug-like text."):
#         command.validate_content("This is 12345678-1234-1234-1234-123456789012 text.")
#     with pytest.raises(ValueError, match="Generated content contains an ID or debug-like text."):
#        command.validate_content("this is some text 0f89b3b2-7470-4b6a-b4a7-15e47bf1f296,")

# @pytest.mark.django_db
# def test_api_rate_limit(mock_gemini_model, mock_env, mock_db_data):
#         mock_gemini_model.generate_content.side_effect = Exception("429: Rate limit")
#         with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
#             out = StringIO()
#             call_command('rewrite_properties', stdout=out)
#             assert "Rate limit hit. Waiting 60 seconds..." in out.getvalue()
#             assert "Failed to process hotel" in out.getvalue()
# @pytest.mark.django_db
# def test_api_other_error(mock_gemini_model, mock_env, mock_db_data):
#     mock_gemini_model.generate_content.side_effect = Exception("Some other error")
#     with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
#         out = StringIO()
#         call_command('rewrite_properties', stdout=out)
#         assert "Retry 1/3" in out.getvalue()
#         assert "Failed to process hotel" in out.getvalue()

# @pytest.mark.django_db
# def test_api_value_error_in_generate_content(mock_gemini_model, mock_env, mock_db_data):
#      mock_gemini_model.generate_content.side_effect = [
#         MagicMock(text="Mocked response with invalid content"), # Valid response, but will be rejected by validate_content function
#         MagicMock(text="Mocked response with invalid content 2"), # Valid response, but will be rejected by validate_content function
#         MagicMock(text="Mocked response with invalid content 3"), # Valid response, but will be rejected by validate_content function
#         MagicMock(text="Mocked response: Valid response") # Valid response that will pass validation
#     ]

#      with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
#         out = StringIO()
#         call_command('rewrite_properties', stdout=out)
#         assert "Content validation failed" in out.getvalue()
#         assert "Successfully updated hotel" in out.getvalue()

# @pytest.mark.django_db
# def test_generate_content_with_retry_value_error_retry(mock_gemini_model, mock_env, mock_db_data):
#         model_mock = MagicMock()
#         model_mock.generate_content.side_effect = [
#             Exception("429: Rate limit"),
#             MagicMock(text="Mocked response: Valid hotel content"),
#             Exception("429: Rate limit"),
#             Exception("429: Rate limit"),
#             MagicMock(text="Mocked response: Valid hotel content"),
#         ]

#         with patch('google.generativeai.GenerativeModel', return_value=model_mock):
#             out = StringIO()
#             call_command('rewrite_properties', stdout=out)
#             assert "Rate limit hit. Waiting 60 seconds..." in out.getvalue()
#             assert "Successfully updated hotel" in out.getvalue()
#             assert "Retry 1/3" in out.getvalue()
#             assert "Failed to process hotel" in out.getvalue()
# @pytest.mark.django_db
# def test_api_error_exceeds_retries(mock_gemini_model, mock_env, mock_db_data):
#     mock_gemini_model.generate_content.side_effect = Exception("Some error")
#     with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
#         out = StringIO()
#         call_command('rewrite_properties', stdout=out)
#         assert "Failed to process hotel 1234 after 3 attempts" in out.getvalue()
#         assert "Failed to process hotel 5678 after 3 attempts" in out.getvalue()
#         assert "Failed to process hotel 9101 after 3 attempts" in out.getvalue()
#         assert "Failed to process hotel 1121 after 3 attempts" in out.getvalue()

# LLM_app/tests/test_rewrite_properties.py
import pytest
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.db import connection
from LLM_app.management.commands import rewrite_properties
from io import StringIO
import os
from dotenv import load_dotenv
import re

load_dotenv()

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"}):
        yield


@pytest.fixture
def mock_gemini_model():
    model_mock = MagicMock()
    model_mock.generate_content.side_effect = lambda prompt: MagicMock(text=f"Mocked response: {prompt}")
    return model_mock


@pytest.fixture
def mock_db_data():
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS MOCK_DATA (
                property_id VARCHAR(255) PRIMARY KEY,
                property_title VARCHAR(255),
                description TEXT,
                property_type VARCHAR(255),
                location VARCHAR(255),
                amenities TEXT,
                price_per_night INTEGER
                )
            '''
        )
        cursor.execute(
            """
            INSERT INTO MOCK_DATA (property_id, property_title, description, property_type, location, amenities, price_per_night)
            VALUES
            ('1234', 'Old Title', 'Old Description', 'Hotel', 'London', 'wifi', 50),
            ('5678', 'Old Title2', 'Old Description2', 'Resort', 'Paris', 'gym, spa', 150),
            ('9101', 'Old Title3', 'Old Description3', 'Apartment', 'New York', 'parking', 350),
            ('1121', 'Old Title4', 'Old Description4', 'Apartment', 'Tokyo', 'pool', 500)
            """
        )
    yield
    with connection.cursor() as cursor:
        cursor.execute('DROP TABLE MOCK_DATA')

@pytest.mark.django_db
def test_command_success(mock_gemini_model, mock_env, mock_db_data):
    with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model) as model_mock:
        out = StringIO()
        call_command('rewrite_properties', stdout=out)
        assert "Successfully updated hotel 1234" in out.getvalue()
        assert "Successfully updated hotel 5678" in out.getvalue()
        assert "Successfully updated hotel 9101" in out.getvalue()
        assert "Successfully updated hotel 1121" in out.getvalue()

        # Verify the context prompt was called at least once
        context_prompt = """
        You are a luxury hotel description generator for hotels and resorts. Your task is to create compelling, 
        hospitality-focused content for high-end hotels and resorts. Never generate 
        medical-related content. Focus exclusively on accommodation, amenities, and 
        guest experiences.
        """
        model_mock.return_value.generate_content.assert_any_call(context_prompt)

@pytest.mark.django_db
def test_command_no_api_key(mock_gemini_model, mock_db_data):
    with patch.dict(os.environ, {}, clear=True):
            out = StringIO()
            call_command('rewrite_properties', stdout=out)
            assert "Google API key not found in environment variables." in out.getvalue()

@pytest.mark.django_db
def test_content_validation_success(mock_gemini_model, mock_env, mock_db_data):
        command = rewrite_properties.Command()
        assert command.validate_content("This is a luxury hotel stay with amazing views.") == True
        assert command.validate_content("Experience the comfort of this hotel.") == True
        assert command.validate_content("This is a luxury hotel with spa") == True

@pytest.mark.django_db
def test_content_validation_medical_terms(mock_gemini_model, mock_env, mock_db_data):
        command = rewrite_properties.Command()
        with pytest.raises(ValueError, match="Generated content contains medical terms: \['medical'\]"):
            command.validate_content("This hotel has a medical spa")

        with pytest.raises(ValueError, match="Generated content contains medical terms: \['patient', 'healing'\]"):
             command.validate_content("This is a patient healing center")

@pytest.mark.django_db
def test_content_validation_no_hotel_terms(mock_gemini_model, mock_env, mock_db_data):
        command = rewrite_properties.Command()
        with pytest.raises(ValueError, match="Generated content lacks hotel-related terms"):
             command.validate_content("This is a great place to have your birthday party")

@pytest.mark.django_db
def test_content_validation_rejects_ids(mock_gemini_model, mock_env, mock_db_data):
    command = rewrite_properties.Command()
    with pytest.raises(ValueError, match="Generated content contains an ID or debug-like text."):
        command.validate_content("This is 12345678-1234-1234-1234-123456789012 text.")
    with pytest.raises(ValueError, match="Generated content contains an ID or debug-like text."):
       command.validate_content("this is some text 0f89b3b2-7470-4b6a-b4a7-15e47bf1f296,")

@pytest.mark.django_db
def test_api_rate_limit(mock_gemini_model, mock_env, mock_db_data):
        mock_gemini_model.generate_content.side_effect = Exception("429: Rate limit")
        with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
            out = StringIO()
            call_command('rewrite_properties', stdout=out)
            assert "Rate limit hit. Waiting 60 seconds..." in out.getvalue()
            assert "Failed to process hotel" in out.getvalue()

@pytest.mark.django_db
def test_api_other_error(mock_gemini_model, mock_env, mock_db_data):
    mock_gemini_model.generate_content.side_effect = Exception("Some other error")
    with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
        out = StringIO()
        call_command('rewrite_properties', stdout=out)
        assert "Retry 1/3" in out.getvalue()
        assert "Failed to process hotel" in out.getvalue()

@pytest.mark.django_db
def test_api_value_error_in_generate_content(mock_gemini_model, mock_env, mock_db_data):
     mock_gemini_model.generate_content.side_effect = [
        MagicMock(text="Mocked response with invalid content"), # Valid response, but will be rejected by validate_content function
        MagicMock(text="Mocked response with invalid content 2"), # Valid response, but will be rejected by validate_content function
        MagicMock(text="Mocked response with invalid content 3"), # Valid response, but will be rejected by validate_content function
        MagicMock(text="Mocked response: Valid response") , # Valid response that will pass validation
        MagicMock(text="Mocked response: | Okay, Here are some options for you: Valid response"), # Valid response that will pass validation with regex matching string
        MagicMock(text="Mocked response: Title: Valid title"),  # Valid response that will pass validation
    ]

     with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
        out = StringIO()
        call_command('rewrite_properties', stdout=out)
        assert "Content validation failed" in out.getvalue()
        assert "Successfully updated hotel" in out.getvalue()
@pytest.mark.django_db
def test_generate_content_with_retry_value_error_retry(mock_gemini_model, mock_env, mock_db_data):
        model_mock = MagicMock()
        model_mock.generate_content.side_effect = [
            Exception("429: Rate limit"),
            MagicMock(text="Mocked response: Valid hotel content"),
            Exception("429: Rate limit"),
            Exception("429: Rate limit"),
            MagicMock(text="Mocked response: Valid hotel content"),
        ]

        with patch('google.generativeai.GenerativeModel', return_value=model_mock):
            out = StringIO()
            call_command('rewrite_properties', stdout=out)
            assert "Rate limit hit. Waiting 60 seconds..." in out.getvalue()
            assert "Successfully updated hotel" in out.getvalue()
            assert "Retry 1/3" in out.getvalue()
            assert "Failed to process hotel" in out.getvalue()
@pytest.mark.django_db
def test_api_error_exceeds_retries(mock_gemini_model, mock_env, mock_db_data):
    mock_gemini_model.generate_content.side_effect = Exception("Some error")
    with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
        out = StringIO()
        call_command('rewrite_properties', stdout=out)
        assert "Failed to process hotel 1234 after 3 attempts" in out.getvalue()
        assert "Failed to process hotel 5678 after 3 attempts" in out.getvalue()
        assert "Failed to process hotel 9101 after 3 attempts" in out.getvalue()
        assert "Failed to process hotel 1121 after 3 attempts" in out.getvalue()
@pytest.mark.django_db
def test_empty_database(mock_gemini_model, mock_env):
    out = StringIO()
    call_command('rewrite_properties', stdout=out)
    assert "Successfully updated hotel" not in out.getvalue()
    assert "No data to process" in out.getvalue()  # Update the command to handle this message.

@pytest.mark.django_db
def test_invalid_api_key(mock_env, mock_db_data):
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "invalid_api_key"}):
        out = StringIO()
        call_command('rewrite_properties', stdout=out)
        assert "Google API key is invalid or failed during initialization" in out.getvalue()

@pytest.mark.django_db
def test_generate_content_with_empty_response(mock_gemini_model, mock_env, mock_db_data):
    mock_gemini_model.generate_content.return_value = MagicMock(text="")
    with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
        out = StringIO()
        call_command('rewrite_properties', stdout=out)
        assert "Generated content is empty" in out.getvalue()

@pytest.mark.django_db
def test_generate_content_invalid_regex(mock_gemini_model, mock_env, mock_db_data):
    mock_gemini_model.generate_content.return_value = MagicMock(
        text="Invalid: 12345678-1234-1234-1234-123456789012"
    )
    with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
        out = StringIO()
        call_command('rewrite_properties', stdout=out)
        assert "Generated content contains an ID or debug-like text." in out.getvalue()

@pytest.mark.django_db
def test_transaction_rollback_on_error(mock_gemini_model, mock_env, mock_db_data):
    mock_gemini_model.generate_content.side_effect = [
        MagicMock(text="Mocked valid title"),
        Exception("Test exception during description generation"),
    ]
    with patch('google.generativeai.GenerativeModel', return_value=mock_gemini_model):
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM MOCK_DATA WHERE property_title = %s', ["Mocked valid title"])
            assert cursor.fetchone()[0] == 0  # Ensure no partial updates occurred.

@pytest.mark.django_db
def test_price_range_conversion(mock_env, mock_db_data):
    command = rewrite_properties.Command()
    test_cases = [
        (50, "Budget-friendly"),
        (150, "Moderate"),
        (350, "Upscale"),
        (500, "Luxury"),
    ]
    for price, expected_range in test_cases:
        assert command.get_price_range(price) == expected_range  # Implement `get_price_range` helper.
