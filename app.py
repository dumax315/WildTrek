import os

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, session, flash)
import requests
import pymongo
import bcrypt
import urllib.parse
from bson.objectid import ObjectId
import base64

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = "Just a random string"
mongoUsername = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME'))
mongoPassword =  urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD'))
uri = 'mongodb+srv://' + mongoUsername + ':' + mongoPassword + '@cluster0.zr80h.mongodb.net'
client = pymongo.MongoClient(uri)
db = client.get_database('wildtrekDB')
users = db.user
posts = db.post

@app.route("/")
def index():
    print('Request for signup received')
    return render_template('index.html')
    #   return render_template('about.html')

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


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
   name = request.form.get('name')

   if name:
       print('Request for hello page received with name=%s' % name)
       return render_template('hello.html', name = name)
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))


def identify(image_id):
    post_found = posts.find_one({"_id": image_id})
    if post_found:
        encoded = base64.b64encode(post_found['image'][1])
        encoded_string = encoded.decode("ascii")
        #print(encoded_string)
        params = {
            "api_key": os.getenv('PLANTID_API_KEY'),
            "images": [encoded_string]
        }
        headers = {
            "Content-Type": "application/json",
        }
        response = requests.post("https://api.plant.id/v2/identify",
                            json=params,
                            headers=headers)
        print(response.status_code)
        if response.status_code >= 200 and response.status_code < 300:
            suggestions = response.json()['suggestions'] #list of dict suggestions
            max_suggestion = len(suggestions) if len(suggestions) <= 3 else 3
            name_list = []
            for i in range(max_suggestion):
                name_list.append(suggestions[i]['plant_name'])
            print(name_list)
            return name_list  
    return []

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
