from faker import Faker
import random
import csv

# Initialize Faker
fake = Faker()

# Generate mock hotel data
def generate_hotel_data(num_records=100):
    data = []
    for _ in range(num_records):
        hotel = {
            "property_id": fake.uuid4(),
            "property_title": f"{fake.word().capitalize()} {fake.word().capitalize()} Hotel",
            "description": fake.text(max_nb_chars=200),
            "property_type": random.choice(["Luxury", "Boutique", "Budget", "Resort", "Business"]),
            "location": fake.city(),
            "amenities": ", ".join(random.sample(["Pool", "Spa", "Free WiFi", "Parking", "Restaurant", "Gym"], 3)),
            "price_per_night": random.randint(50, 500),
        }
        data.append(hotel)
    return data

# Save to CSV
def save_to_csv(data, filename="data/MOCK_DATA.csv"):
    keys = data[0].keys()
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

# Generate and save mock data
hotel_data = generate_hotel_data(10)
save_to_csv(hotel_data)
