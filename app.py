from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import json
import os
import spacy
from spacy.cli import download

try:
    nlp = spacy.load("en_core_web_sm")
except:
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
CORS(app)  # Allow requests from frontend

# Load meals from a JSON file
with open('meals.json') as f:
    meals = json.load(f)

# Load users from a JSON file or create an empty list
if os.path.exists('users.json'):
    with open('users.json') as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            users = []
else:
    users = []

@app.route('/personalizeMeals', methods=['POST'])
def personalize_meals():
    data = request.json
    meal_type = data['mealType']
    calorie_target = data['calorieTarget']
    allergies = data['allergies']
    eco_friendly = data['ecoFriendly'] == 'yes'

    filtered_meals = []

    for meal in meals:
        # Basic rules for filtering
        if meal_type == 'veg' and not meal.get('veg', True):
            continue
        if meal_type == 'non-veg' and meal.get('veg', False):
            continue
        if eco_friendly and not meal.get('ecoFriendly', False):
            continue
        if calorie_target == '<300' and meal['calories'] >= 300:
            continue
        if calorie_target == '300-500' and not (300 <= meal['calories'] <= 500):
            continue
        if calorie_target == '>500' and meal['calories'] <= 500:
            continue
        # Skip meals with allergens (basic keyword match)
        if allergies and allergies.lower() in meal.get('name', '').lower():
            continue

        filtered_meals.append(meal)

    return jsonify(filtered_meals[:5])  # Return max 5 meals

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    user_message = data['message'].lower()

    doc = nlp(user_message)
    keywords = [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'ADJ']]

    suggestions = []

    if 'low' in keywords or 'calorie' in keywords:
        suggestions.append("Grilled Vegetable Salad")
        suggestions.append("Fruit Smoothie Bowl")

    if 'high' in keywords or 'protein' in keywords:
        suggestions.append("Paneer Tikka")
        suggestions.append("Chicken Breast Salad")

    if 'vegan' in keywords:
        suggestions.append("Quinoa Avocado Salad")
        suggestions.append("Vegan Burrito")

    if 'eco' in keywords or 'friendly' in keywords:
        suggestions.append("Lentil Soup")
        suggestions.append("Vegan Tacos")

    if not suggestions:
        reply = "I'm sorry, I couldn't understand your meal preference. You can ask for low calorie, high protein, vegan, or eco-friendly meals!"
    else:
        reply = "Here are some suggestions: " + ", ".join(suggestions)

    return jsonify({"reply": reply})
@app.route('/getMeals', methods=['GET'])
def get_meals():
    recommended_meals = random.sample(meals, 5)  # randomly select 5 meals
    return jsonify(recommended_meals)

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    new_user = {
        "email": data['email'],
        "password": data['password']
    }
    users.append(new_user)
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)
    return jsonify({"message": "Signup successful!"}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    for user in users:
        if user['email'] == data['email'] and user['password'] == data['password']:
            return jsonify({"message": "Login successful!"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(debug=True)
