import os

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, session, flash)
import pymongo
import bcrypt
import urllib.parse

app = Flask(__name__)
app.secret_key = "Just a random string"
mongoUsername = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME'))
mongoPassword =  urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD'))
uri = 'mongodb+srv://' + mongoUsername + ':' + mongoPassword + '@cluster0.zr80h.mongodb.net'
client = pymongo.MongoClient(uri)
db = client.get_database('wildtrekDB')
users = db.user

@app.route("/")
def index():
    print('Request for signup received')
    return render_template('index.html')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    print('Request for signup received')
    if "username" in session:
        return redirect(url_for("logged_in"))
    if request.method == "POST":
        username = request.form.get("username")
        
        password = request.form.get("password")
        
        user_found = users.find_one({"username": username})
        if user_found:
            return render_template('error.html', message='Username already exists.')
        else:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user_input = {'username': username, 'password': hashed}
            users.insert_one(user_input)
            
            user_data = users.find_one({"username": username})
            new_username = user_data['username']
   
            return render_template('loggedin.html', username=new_username)
    return render_template('signup.html')

@app.route("/login", methods=["POST", "GET"])
def login():
    print('Request for login received')
    if "username" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

       
        user_found = users.find_one({"username": username})
        if user_found:
            user_val = user_found['username']
            passwordcheck = user_found['password']
            
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["username"] = user_val
                return redirect(url_for('logged_in'))
            else:
                if "username" in session:
                    return redirect(url_for("logged_in"))
                flash('Wrong password')
                return render_template('login.html')
        else:
            flash('Username not found')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logged_in')
def logged_in():
    if "username" in session:
        username = session["username"]
        return render_template('loggedin.html', username=username)
    else:
        return redirect(url_for("login"))



# extra code to get some shops instead of post Temperary
import overpy


def get_shops(latitude, longitude):
    # Initialize the API
    api = overpy.Overpass()
    # Define the query
    query = """(node["shop"](around:500,{lat},{lon});
                node["building"="retail"](around:500,{lat},{lon});
                node["building"="supermarket"](around:500,{lat},{lon});
                node["healthcare"="pharmacy"](around:500,{lat},{lon});
            );out;
            """.format(lat=latitude, lon=longitude)
    # Call the API
    result = api.query(query)
    return result

@app.route('/map')
def map():
    # Get shops data from OpenStreetMap
    shops = get_shops(47.654170, -122.302610)

    # Initialize variables
    id_counter = 0
    markers = ''
    for node in shops.nodes:

        # Create unique ID for each marker
        idd = 'shop' + str(id_counter)
        id_counter += 1

        # Check if shops have name and website in OSM
        try:
            shop_brand = node.tags['brand']
        except:
            shop_brand = 'null'

        try:
            shop_website = node.tags['website']
        except:
            shop_website = 'null'

        # Create the marker and its pop-up for each shop
        markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                    {idd}.addTo(map).bindPopup('{brand}<br>{website}');".format(idd=idd, latitude=node.lat,\
                                                                                longitude=node.lon,
                                                                                brand=shop_brand,\
                                                                                website=shop_website)

    # Render the page with the map
    return render_template('map.html', markers=markers, lat=47.654170, lon=-122.302610)

if __name__ == '__main__':
   app.run()
