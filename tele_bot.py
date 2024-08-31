import os
import telebot
import requests

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(BOT_TOKEN)
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

user_data = {}

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing? Let's start by getting some information from you.")
    ask_age(message)

def ask_age(message):
    sent_message = bot.send_message(message.chat.id, "Please enter your age:")
    bot.register_next_step_handler(sent_message, handle_age)

def handle_age(message):
    try:
        age = int(message.text)
        user_data['age'] = age
        ask_gender(message)
    except ValueError:
        bot.reply_to(message, "Please enter a valid number for age.")
        ask_age(message)

def ask_gender(message):
    sent_message = bot.send_message(message.chat.id, "Please enter your gender (male/female/other):")
    bot.register_next_step_handler(sent_message, handle_gender)

def handle_gender(message):
    gender = message.text.lower()
    if gender in ['male', 'female', 'other']:
        user_data['gender'] = gender
        ask_location(message)
    else:
        bot.reply_to(message, "Please enter a valid gender (male/female/other).")
        ask_gender(message)

def ask_location(message):
    sent_message = bot.send_message(message.chat.id, "Please enter your location:")
    bot.register_next_step_handler(sent_message, handle_location)

def handle_location(message):
    location = message.text
    user_data['location'] = location
    ask_height(message)

def ask_height(message):
    sent_message = bot.send_message(message.chat.id, "Please enter your height in the format feet.inches (e.g., 5.7 for 5 feet 7 inches):")
    bot.register_next_step_handler(sent_message, handle_height)

def handle_height(message):
    try:
        height_parts = message.text.split('.')
        
        if len(height_parts) == 1:
            # User provided only feet, default inches to 0
            feet = int(height_parts[0])
            inches = 0
        elif len(height_parts) == 2:
            # User provided feet and inches
            feet = int(height_parts[0])
            inches = int(height_parts[1])
        else:
            raise ValueError("Height must be in the format feet.inches (e.g., 5.7).")
        
        if inches < 0 or inches >= 12:
            raise ValueError("Inches must be between 0 and 11.")

        user_data['height_feet'] = feet
        user_data['height_inches'] = inches

        height_str = f"{feet} feet {inches} inches"
        prompt = (f"Age: {user_data['age']}, Gender: {user_data['gender']}, "
                  f"Location: {user_data['location']}, Height: {height_str}. "
                  "Provide personalized advice on their dress with the name of the dress in 3D.")

        # Request data for image generation
        data = {
            'prompt': prompt,
            'n': 1,  # Number of images to generate
            'size': '512x512'  # Size of the image
        }
        endpoint = 'https://api.openai.com/v1/images/generations'
        response = requests.post(endpoint, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            image_url = result['data'][0]['url']
            bot.send_message(message.chat.id, f"Generated Image URL: {image_url}")

            # # Download and save the image
            # image_response = requests.get(image_url)
            # if image_response.status_code == 200:
            #     os.makedirs('images', exist_ok=True)
            #     image_path = os.path.join('images', 'generated_image.jpg')
            #     with open(image_path, 'wb') as file:
            #         file.write(image_response.content)
            #     bot.send_message(message.chat.id, "Image downloaded successfully.")
            # else:
            #     bot.reply_to(message, "Failed to download the image.")
        else:
            bot.reply_to(message, f"Error generating image: {response.status_code} - {response.text}")

    except ValueError as e:
        bot.reply_to(message, f"Invalid input for height: {e}. Please enter height in the format feet.inches (e.g., 5.7).")
        ask_height(message)

bot.polling()
