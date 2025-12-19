# DigiRobe: Digital Wardrobe Manager

DigiRobe is a web application that helps students digitally manage their wardrobe, generate outfit suggestions, and promote sustainable fashion purchases by reducing unnecessary clothing purchases. The application allows users to catalog their clothing items, filter them in various ways, and receive random outfit suggestions to maximize the use of their existing wardrobe pieces. 

# Installation steps
### This application is currently designed to run locally. Instructions to run the app locally are provided below.
1. Install dependencies
    pip install -r requirements.txt

2. Run the application
    python main.py

3. Access the application locally:
    In your web browser, navigate to http://127.0.0.1:8000.

    Register a new account 

# How to test the application
### First time setup: 
1. Go to http://127.0.0.1:8000/ in your browser.
- Click Register button to create a new account. 
- Fill in username, full name, email, and password
- Submit to create an account and get redirected to your wardrobe. 

# Managing wardrobe:
## Add items:
1. Fill out the "Add New Item" form with:
    - Item name
    - Category (Tops, Bottoms, Dresses, Shoes, Accessories)
    - Color
    - Season (Spring, Summer, Fall, Winter, All)
2. Click "Add to wardrobe"
3. Item appears instantly in your grid

## Filter items
1. Use the dropdown in the "Filter Items" section
2. Select a category to view
3. Grid automatically updates to show items that match filter

## Delete Items:
1. Click the Delete button on any item card
2. Confirm deletion
3. Item is removed instantly

## Generate Outfit:
1. Click "Generate Random Outfit" button
2. Application randomly selects 2-3 items from wardrobe
3. Use suggestions to discover new outfit combinations 
