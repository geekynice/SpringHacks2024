from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Preferences, UserModel
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import os
import pandas as pd
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from groq import Groq
import google.generativeai as genai
from google.generativeai import GenerativeModel, configure
import logging
import pathlib
import os
import google.generativeai as genai
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import re

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')
from django.http import HttpResponseRedirect, HttpResponseServerError
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def index(request):
    return render(request, 'index.html')

def parse_response_recommendation(completion):
    meal_name = ""
    calories = ""
    price = ""
    ai_response = ""

    for chunk in completion:
        ai_response += chunk.choices[0].delta.content or ""

    # Split by lines
    lines = ai_response.split("\n")

    for line in lines:
        if line.startswith("**Meal Name:**"):
            meal_name = line.replace("**Meal Name:**", "").strip('*').strip()
        elif line.startswith("**Calories:**"):
            calories = line.replace("**Calories:**", "").strip('*').strip()
        elif line.startswith("**Price:**"):
            price = line.replace("**Price:**", "").strip('*').strip()
    print(meal_name)
    return meal_name, calories, price





def dashboard_view(request):
    try:
        user_model_instance = UserModel.objects.get(user=request.user)
        user_preferences = user_model_instance.preference

        prompt1 = f"Generate first meal1 suggestion with the following details that includes Meal Name, Calories & Price:\n"
        prompt1 += f"Based on the available dataset and your preferences and height and weight:\n"
        prompt1 += f"Preferences and Body info: {user_preferences}\n"
        prompt1 += "Both should be different"
        
        prompt2 = f"Generate second meal2 suggestion with the following details that includes Meal Name, Calories & Price:\n"
        prompt2 += f"Based on the available dataset and your preferences and height and weight:\n"
        prompt2 += f"Preferences and Body info: {user_preferences}\n"

        prompt2 += "Both should be different"

        # Query the model for both meal suggestions
        completion1 = query_model(prompt1)
        completion2 = query_model(prompt2)

        # Parse model response to get the meal recommendation details
        meal_name, calories, price = parse_response_recommendation(completion1)
        meal_name2, calories2, price2 = parse_response_recommendation(completion2)

        # Prepare context for rendering template
        context = {
            'meal_name': meal_name,
            'calories': calories,
            'price': price, # Assuming this is already in HTML format
            'meal_name2': meal_name2,
            'calories2': calories2,
            'price2': price2,
            'user_preferences': user_preferences,
        }

    except UserModel.DoesNotExist:
        # Handle case where UserModel does not exist for the user
        context = {
            'error_message': "User preferences not found."
        }

    return render(request, 'dashboard.html', context)


@login_required
def meal_from_photo_view(request):
    if request.method == 'POST' and request.FILES['image']:
        try:
            # Handle file upload
            uploaded_file = request.FILES['image']
            file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Read image data
            image_data = pathlib.Path(file_path).read_bytes()

            # Define prompt and generate content
            prompt = "Generate 3 healthy meal from the items in fridge and show calories, instruction, ingridients & health benefits, AND ALWAYS GIVE THE RESPONSE IN SAME STRUCTURE in html <table></table> format"
            response = model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': image_data}])

            # Return raw JSON response
            return render(request, 'meal_from_photo.html', {'response': response.text})

        except Exception as e:
            # Log the exception or handle it appropriately
            print(f"Error generating meals: {str(e)}")
            return HttpResponseServerError("Error generating meals. Please try again later.")

    # Render initial form if GET request or invalid POST
    return render(request, 'meal_from_photo.html')

# Initialize Groq client

# Function to load CSV data
def load_csv(file_path):
    return pd.read_csv(file_path)

# Function to query the model
def query_model(prompt):
    messages = [{
        "role": "user",
        "content": prompt
    }]
    print("Querying model with prompt:")
    print(prompt)
    completion = client.chat.completions.create(
        model="llama3-70b-8192",  # Replace with your desired model
        messages=messages,
        temperature=1,  # Adjust temperature for more creative or conservative response
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    print("Completion: ",completion)
    return completion

def parse_response(completion):
    ai_response = ""
    ingredients = []
    recipe_steps = []
    instructions = []
    health_benefits = []
    current_section = None
    
    # Join all chunks into a single string
    for chunk in completion:
        ai_response += chunk.choices[0].delta.content or ""
    
    # Split by lines
    lines = ai_response.split("\n")
    
    # Process each line
    for line in lines:
        if line.startswith("**Health Benefits:**"):
            current_section = "health benefits"
        elif line.startswith("**Recipe:**"):
            current_section = "instructions"
        elif current_section == "health benefits" and line.strip().startswith("* "):
            health_benefits.append(line.strip("* ").strip())
        elif line.startswith("Instructions:"):
            current_section = "instructions"
        elif current_section == "instructions":
            if line.strip().startswith(("1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ")):
                recipe_steps.append(line.strip())
                instructions.append(line.strip())
                ingredients.append(line.strip("* ").strip())



    ingredients = [ingredient.strip() for ingredient in ingredients]
    instructions = [instruction.strip() for instruction in instructions]
    recipe_steps = [recipe.strip() for recipe in recipe_steps]
    health_benefits = [benefit.strip('*').strip() for benefit in health_benefits]
    print(ingredients)
    print(recipe_steps)
    print(instructions)
    print("Health Benefits: ", health_benefits)
    
    return ai_response.strip(), ingredients, recipe_steps, instructions, health_benefits

@login_required
def MealSuggestionView(request):
    csv_file_path = r'cleaned-data.csv'
    df = load_csv(csv_file_path)

    if request.method == 'POST':
        # Get form data
        diet_option = request.POST.get('diet_option')
        nut_allergic = request.POST.get('nut_allergic')
        goal = request.POST.get('goal')

        # Create the prompt for the model
        prompt = f"Generate a meal suggestion with the following details:\n"
        prompt += f"Meal Name:\n"
        prompt += f"Calories:\n"
        prompt += f"Price:\n"
        prompt += f"Health Benefits: []\n"
        prompt += f"Recipe: []\n\n"
        prompt += f"Based on the available dataset and your preferences:\n"
        prompt += f"Diet Option: {diet_option}\n"
        prompt += f"Nut Allergic: {nut_allergic}\n"
        prompt += f"Goal: {goal}\n"
        prompt += f"Dataset Preview:\n{df.head().to_string()}"

        print("Generated prompt:")
        print(prompt)

        # Query the model
        completion = query_model(prompt)

        print("Model completion received:")
        print(completion)

        # Parse model response
        related_data, ingredients, recipe_steps, instructions, health_benefits = parse_response(completion)

        print("Parsed response:")
        print(f"Related Data:\n{related_data}")
        print(f"Ingredients:\n{ingredients}")
        print(f"Recipe Steps:\n{recipe_steps}")
        print(f"Instructions:\n{instructions}")
        print(f"Health Benefits:\n{health_benefits}")

        # Extract meal details
        meal_name = ""
        calories = ""
        price = ""
        for line in related_data.splitlines():
            clean_line = line.strip()
            if clean_line.startswith("**Meal Name:**"):
                meal_name = clean_line.replace("**Meal Name:**", "").strip('*').strip()
            elif clean_line.startswith("**Calories:**"):
                calories = clean_line.replace("**Calories:**", "").strip('*').strip()
            elif clean_line.startswith("**Price:**"):
                price = clean_line.replace("**Price:**", "").strip('*').strip()

        print(f"Extracted Meal Name: {meal_name}")
        print(f"Extracted Calories: {calories}")
        print(f"Extracted Price: {price}")

        # Prepare context for rendering template
        context = {
            'meal_name': meal_name,
            'calories': calories,
            'price': price,
            'ingredients': ingredients,
            'recipe_steps': recipe_steps,
            'instructions': instructions,
            'health_benefits': health_benefits,
            'diet_option': diet_option,
            'nut_allergic': nut_allergic,
            'goal': goal,
            'dataset_preview': df.head().to_html(),  
        }

        return render(request, 'meal.html', context)

    # Return the initial page or handle GET request if not POST
    context = {
        'dataset_preview': df.head().to_html(),
    }

    print("Rendering initial page with dataset preview:")
    print(context)

    return render(request, 'meal.html', context)


User = get_user_model()

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        date_of_birth = request.POST['date_of_birth']
        profile_photo = request.FILES.get('profile_photo', None)
        weight = request.POST['weight']
        height = request.POST['height']

        user = User.objects.create_user(username=username, password=password, first_name= first_name, last_name=last_name, email = email)

        custom_user = UserModel.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            profile_photo=profile_photo,
            weight=weight,
            height=height
        )

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('preferences')  

    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'login.html')

@login_required
def preferences_view(request):
    if request.method == 'POST':
        diet_option = request.POST.get('diet_option')
        nut_allergic = request.POST.get('nut_allergic') == 'on'
        goal = request.POST.get('goal')

        # Ensure the logged-in user has a CustomUser instance
        custom_user = UserModel.objects.get(user=request.user.id)

        # Save preferences for the user
        Preferences.objects.create(
            user=custom_user,
            diet_option=diet_option,
            nut_allergic=nut_allergic,
            goal=goal
        )
        height = custom_user.height
        weight = custom_user.weight

        custom_user.preference = f"Diet Option:{diet_option}, Nut Allergy:{nut_allergic}, Goal:{goal}, height:{height}cm, weight:{weight}kg"
        custom_user.save()
        return redirect('index')  # Redirect to a home page or another appropriate page

    return render(request, 'preferences.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')









from django.views.decorators.csrf import csrf_exempt
import json

import asyncio
import asyncio

async def query_model_chat(prompt):
    messages = [{
        "role": "user",
        "content": prompt
    }]
    
    print("Querying model with prompt:")
    print(prompt)
    
    try:
        completion = await client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        
        response_text = ''
        
        async for chunk in completion:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                for choice in chunk.choices:
                    if hasattr(choice, 'text'):
                        response_text += choice.text
        
        response_text = response_text.strip()
        
        print("Response text:")
        print(response_text)  # Print the final response text for debugging
        
        return response_text  # Return the response text
    
    except Exception as e:
        print(f"Error querying model: {str(e)}")
        return ""  # Return empty string in case of any errors

# Example usage in a script or module
async def main():
    prompt = "Who is the world's richest person?"
    response_text = await query_model_chat(prompt)
    print("Final Response:", response_text)

if __name__ == "__main__":
    asyncio.run(main())

@csrf_exempt
async def chatbot_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '')
            
            # Call the asynchronous function directly
            response_text = await query_model_chat(prompt)
            
            # Print the response for debugging purposes
            print("Final Response:", response_text)
            
            return JsonResponse({'response': response_text})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)
    
def chat_page(request):
    return render(request, 'chat.html')