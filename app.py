from flask import Flask, request, jsonify, render_template
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

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
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,reviews,url&key={google_maps_key}"
    response = requests.get(url)
    result = response.json().get('result', {})
    reviews = result.get('reviews', [])
    place_name = result.get('name', '')
    place_url = result.get('url', '')
    return {
        'reviews': reviews,
        'place_name': place_name,
        'place_url': place_url
    }

# Function to process reviews with GPT-4 and extract insights
def process_with_gpt(reviews, language):
    print("Language in process_with_gpt:", language)  # Debugging
    review_texts = ' '.join([review['text'] for review in reviews])

    if language == 'fr':
        # French version of the prompt and role
        roast_prompt = f"D'après ces avis : {review_texts}, créez un 'roast' hilarant et exagéré sur le lieu en français. Rendez-le drôle et sans retenue, comme un roast comique (sans être offensant). Utilisez des emojis si possible (mais pas trop, un ou deux maximum par message). Concentrez-vous sur les taquineries amusantes et mélangez les aspects réels mentionnés dans les avis avec une touche humoristique. Max 5 phrases."
        
        insights_prompt = f"Analysez ces avis de restaurant : {review_texts}. Extrayez exactement 3 mots-clés ou phrases courtes (2-3 mots max) qui résument les aspects les plus importants - positifs ou négatifs. Répondez UNIQUEMENT avec un array JSON de 3 strings en français, sans autre texte. Exemple: [\"Service lent\", \"Nourriture délicieuse\", \"Ambiance bruyante\"]"
        
        role_message = "Tu es un comédien et humoriste, habitué à faire des roasts hilarants."
    else:
        # English version of the prompt and role
        roast_prompt = f"Drawing from the content of these reviews: {review_texts}, your role is to craft an amusing and exaggerated roast about the establishment in question. Aim for humor that is sharp yet inoffensive, capturing the essence of a comedy roast. You are encouraged to use emojis to add a touch of whimsy, but please keep them to a minimum (one or two maximum per response). Your primary focus should be on light-hearted teasing, blending the actual details mentioned in the reviews with a comedic spin. Ensure that your roast is succinct, ideally confined to a maximum of five sentences."
        
        insights_prompt = f"Analyze these restaurant reviews: {review_texts}. Extract exactly 3 keywords or short phrases (2-3 words max) that summarize the most important aspects - positive or negative. Respond ONLY with a JSON array of 3 strings, no other text. Example: [\"Slow service\", \"Great food\", \"Noisy atmosphere\"]"
        
        role_message = "You are a witty and humorous comedian, skilled at making hilarious roasts."

    try:
        # Get the roast
        roast_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": role_message},
                {"role": "user", "content": roast_prompt}
            ]
        )
        roast = roast_response.choices[0].message.content.strip()
        
        # Get the insights
        insights_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing restaurant reviews and extracting key insights. Always respond with valid JSON only."},
                {"role": "user", "content": insights_prompt}
            ]
        )
        
        try:
            insights_text = insights_response.choices[0].message.content.strip()
            # Clean up the response to ensure it's valid JSON
            if insights_text.startswith('```json'):
                insights_text = insights_text.replace('```json', '').replace('```', '').strip()
            insights = json.loads(insights_text)
            
            # Ensure we have exactly 3 insights
            if len(insights) != 3:
                insights = insights[:3] if len(insights) > 3 else insights + ["No data"] * (3 - len(insights))
                
        except (json.JSONDecodeError, KeyError):
            # Fallback insights if JSON parsing fails
            if language == 'fr':
                insights = ["Analyse difficile", "Données limitées", "Avis variés"]
            else:
                insights = ["Mixed reviews", "Limited data", "Varied opinions"]
        
        return {
            'roast': roast,
            'insights': insights
        }
        
    except Exception as e:
        print(f"An error occurred: {e}")
        error_msg = "Une erreur s'est produite lors du traitement des avis. Veuillez réessayer plus tard." if language == 'fr' else "An error occurred while processing the reviews. Please try again later."
        fallback_insights = ["Erreur", "Données indisponibles", "Réessayer"] if language == 'fr' else ["Error", "Data unavailable", "Try again"]
        
        return {
            'roast': error_msg,
            'insights': fallback_insights
        }


@app.route('/get-reviews', methods=['POST'])
def get_reviews_endpoint():
    data = request.json
    place_id = data['place_id']
    language = data.get('lang', 'en')
    print("Received language:", language)  # Debugging

    if not place_id:
        return jsonify({'error': 'Place ID is required'}), 400

    reviews_data = get_reviews(place_id)
    reviews = reviews_data['reviews']
    place_name = reviews_data['place_name']
    place_url = reviews_data['place_url']

    result = process_with_gpt(reviews, language)  # This now returns both roast and insights
    
    return jsonify({
        'summary': result['roast'],
        'insights': result['insights'],
        'place_name': place_name,
        'place_url': place_url
    })

if __name__ == '__main__':
    app.run(debug=True)
