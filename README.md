# Hotel Property Management System with LLM Integration

This project is a Django-based CLI application that uses Large Language Models (LLM) to generate and manage hotel property information, including descriptions, summaries, ratings, and reviews.

## Features

- Rewrite property titles and descriptions
- Generate property summaries
- Create property ratings and reviews
- Uses Gemini 2.0 Flash Exp model
- Database integration with PostgreSQL
- Docker containerization

## Prerequisites

- Docker and Docker Compose
- Git
- PostgreSQL
- Python 3.x

## Installation & Setup

1. Clone the repository:
```bash
git clone https://github.com/fahiiiiii/LLM_Project.git
cd LLM_Project
```

2. Build and start the Docker containers:
```bash
docker-compose build
docker-compose up
```

## Data Generation and Upload

1. Start the Django container in detached mode:
```bash
docker-compose up django -d
```

2. Access the Django container shell:
```bash
docker exec -it django_app bash
```

3. Generate sample hotel data:
```bash
python generate_hotel_data.py
```
Note: You can modify the number of records by changing the parameter in `hotel_data=generate_hotel_data(your_required_number_of_data)`

4. Upload the generated data:
```bash
python db_uploader.py
python manage.py makemigrations or python manage.py makemigrations LLM_app
python manage.py migrate or python manage.py migrate LLM_app

```

## Running the Commands

### 1. Rewrite Property Information
```bash
python manage.py rewrite_properties.py
```

To view updated properties in database:
```bash
docker exec -it ollama_db psql fahimah -d llm_db
SELECT * FROM "MOCK_DATA";
```

### 2. Generate Property Summaries
```bash
python manage.py generate_property_summaries.py
```

To view summaries in database:
```bash
docker exec -it ollama_db psql fahimah -d llm_db
SELECT * FROM "LLM_app_propertysummary";
```

### 3. Generate Ratings and Reviews
```bash
python manage.py generate_ratingReview.py
```

To view ratings and reviews in database:
```bash
docker exec -it ollama_db psql fahimah -d llm_db
SELECT * FROM "LLM_app_propertyreview";
```

## Database Schema

### Main Property Table (MOCK_DATA)
- property_id
- property_title
- description
- property_type
- location
- amenities
- price_per_night

### Property Summary Table (LLM_app_propertysummary)
- property_id
- summary

### Property Review Table (LLM_app_propertyreview)
- property_id
- rating
- review

## Error Handling

The application includes robust error handling for:
- API rate limiting
- Content validation
- Database transactions
- Retry mechanisms for failed operations

## Important Notes

- The application uses Gemini 2.0 Flash Exp model for text generation
- Each command includes rate limiting and retry mechanisms
- All database operations are performed within transactions for data integrity
- Content validation ensures generated text meets hospitality industry standards

## Troubleshooting

If you encounter any issues:
1. Check Docker container status: `docker-compose ps`
2. View Docker logs: `docker-compose logs`
3. Ensure database connections are properly configured
4. Verify environment variables are set correctly



## Testing

### Setting up Test Environment

1. Create a virtual environment:
```bash
python -m venv llmenv or python3 -m venv llmenv 
```

2. Activate the virtual environment:
```bash
source llmenv/bin/activate
```

3. Install test dependencies:
```bash
pip install pytest pytest-django
pip install google-generativeai google-api-core
pip install django pytest-django
pip install python-dotenv
pip install psycopg
pip install pytest-cov
```

### Running Tests

To run all tests:
```bash
pytest LLM_app/tests
```

### Test Coverage

To generate test coverage report:
```bash
pytest LLM_app/tests --cov=LLM_app
```

This will display a coverage report showing:
- The percentage of code covered by tests
- Which lines of code were executed
- Which lines were missed


## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details