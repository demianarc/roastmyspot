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
def process_with_gpt(reviews, language):
    print("Language in process_with_gpt:", language)  # Debugging
    review_texts = ' '.join([review['text'] for review in reviews])

    if language == 'fr':
        # French version of the prompt and role
        prompt = f"D'après ces avis : {review_texts}, créez un 'roast' hilarant et exagéré sur le lieu en français. Rendez-le drôle et sans retenue, comme un roast comique (sans être offensant). Utilisez des emojis si possible (mais pas trop, un ou deux maximum par message). Concentrez-vous sur les taquineries amusantes et mélangez les aspects réels mentionnés dans les avis avec une touche humoristique. Max 5 phrases."
        role_message = "Tu es un comédien et humoriste, habitué à faire des roasts hilarants."
    else:
        # English version of the prompt and role
        prompt = f"Drawing from the content of these reviews: {review_texts}, your role is to craft an amusing and exaggerated roast about the establishment in question. Aim for humor that is sharp yet inoffensive, capturing the essence of a comedy roast. You are encouraged to use emojis to add a touch of whimsy, but please keep them to a minimum (one or two maximum per response). Your primary focus should be on light-hearted teasing, blending the actual details mentioned in the reviews with a comedic spin. Ensure that your roast is succinct, ideally confined to a maximum of five sentences."
        role_message = "You are a witty and humorous comedian, skilled at making hilarious roasts."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": role_message},
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
    language = data.get('lang', 'en')
    print("Received language:", language)  # Debugging

    if not place_id:
        return jsonify({'error': 'Place ID is required'}), 400

    reviews = get_reviews(place_id)
    summary = process_with_gpt(reviews, language)  # Pass language to the processing function
    return jsonify({'summary': summary})

if __name__ == '__main__':
    app.run(debug=True)