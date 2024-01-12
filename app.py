from flask import Flask, request, jsonify, render_template
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load API keys from .env file
load_dotenv()
google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')

app = Flask(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def index_page():
    return render_template('index.html', google_maps_key=google_maps_key)

# Function to get reviews from Google Maps
def get_reviews(place_id):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,reviews&key={google_maps_key}"
    response = requests.get(url)
    reviews = response.json().get('result', {}).get('reviews', [])
    return reviews

# Function to process reviews with GPT-3.5 Turbo
def process_with_gpt(reviews):
    review_texts = ' '.join([review['text'] for review in reviews])
    prompt = f"Analyze and summarize these reviews: {review_texts}.Write an engaging and reasonably witty brief as if you're texting a friend. The summary should be balanced, covering both positive and negative aspects in a light and humorous way. Avoid focusing on specifics from individual reviews. Instead, provide a general impression that captures the overall sentiment. Use casual language and reasonable amount of emojis to make it fun. Keep it under 5 sentences. Conclude with a brief personal recommendation (go or not). Remember, it should sound like an honest and casual conversation between friends, not a formal review."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "You are a creative and engaging friend."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred while processing the reviews. Please try again later."

@app.route('/get-reviews', methods=['POST'])
def get_reviews_endpoint():
    data = request.json
    place_id = data['place_id']
    if not place_id:
        return jsonify({'error': 'Place ID is required'}), 400
    reviews = get_reviews(place_id)
    summary = process_with_gpt(reviews)
    return jsonify({'summary': summary})

if __name__ == '__main__':
    app.run(debug=True)
