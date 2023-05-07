import os

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, session, flash)
import requests
import pymongo
import bcrypt
import urllib.parse
from bson.objectid import ObjectId
import base64
import uuid
import boto3, botocore
import random
import datetime
import io

import getGeo

# import
# from logging import StreamHandler



# from exif import Image

app = Flask(__name__)

app.config["DEBUG"] = True
app.config['S3_BUCKET'] = os.getenv('S3_BUCKET_NAME')
app.config['S3_KEY'] = os.getenv('AWS_ACCESS_KEY')
app.config['S3_SECRET'] = os.getenv('AWS_ACCESS_SECRET')
app.config['S3_LOCATION'] = 'http://{}.s3.amazonaws.com/'.format(os.getenv('S3_BUCKET_NAME'))

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

mongoUsername = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME'))
mongoPassword =  urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD'))
uri = 'mongodb+srv://' + mongoUsername + ':' + mongoPassword + '@cluster0.zr80h.mongodb.net'
client = pymongo.MongoClient(uri)
db = client.get_database('wildtrekDB')
users = db.user
posts = db.post

# keep stdout/stderr logging using StreamHandler
# streamHandler = StreamHandler()
# app.logger.addHandler(streamHandler)

# appl(logging.Formatter('[FLASK-SAMPLE][%(levelname)s]%(message)s'))



@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    print('Request for signup received')
    return render_template('index.html')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    print('Request for signup received')
    if "username" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username")
        
        password = request.form.get("password")
        
        user_found = users.find_one({"username": username})
        if user_found:
            return render_template('error.html', message='Username already exists.')
        else:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user_input = {'username': username, 'password': hashed, 'profile_picture': '', 'bio': '','posts': []}
            users.insert_one(user_input)
            
            user_data = users.find_one({"username": username})
            new_username = user_data['username']
   
            return redirect(url_for("about"))
    return render_template('signup.html')

@app.route("/login", methods=["POST", "GET"])
def login():
    print('Request for login received')
    if "username" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

       
        user_found = users.find_one({"username": username})
        if user_found:
            user_val = user_found['username']
            passwordcheck = user_found['password']
            
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["username"] = user_val
                return redirect(url_for('home'))
            else:
                if "username" in session:
                    return redirect(url_for("home"))
                return render_template('login.html')
        else:
            return render_template('login.html')
    return render_template('login.html')

@app.route('/home')
def home():
    args = request.args
    print(args.get("index"))
    if "username" in session:
        currentPosts = getposts()
        # print(currentPosts)
        username = session["username"]
        index=0
        if(args.get("index") != None):
            try:
                index =  int(args.get("index"))
            except:
                print("werird index")

        return render_template('home.html', username=username, currentPosts=currentPosts, index=index)
    else:
        return redirect(url_for("index"))


@app.route("/onePost", methods=["GET"])
def onePost():
    args = request.args
    print(args.get("id"))
   
    if(args.get("id") == None):
        return redirect(url_for("index"))
    idStr = args.get("id")
    if "username" in session:

        username = session["username"]
    else:
        username ="join today"
    if(idStr[:4] == "post"):
        currentOnePost = post(idStr[4:])
    else:
        currentOnePost = post(idStr)

    if(currentOnePost == None):
        return render_template('error.html', message='Post not found')
    return render_template('onePost.html', username=username, currentOnePost=currentOnePost)



@app.route("/profile", methods=["GET"])
def profile():
    args = request.args
    print(args.get("username"))

    usernameToLoad = ''
   
    if(args.get("username") == None):
        usernameToLoad = session["username"]
    else:
        usernameToLoad = args.get("username")

    if "username" in session:

        username = session["username"]
    else:
        username ="join today"

    loadedProfile = user_info(usernameToLoad)
    if(loadedProfile == None or loadedProfile =={}):
        return render_template('error.html', message='User not found')
    return render_template('profile.html', username=username, loadedProfile=loadedProfile)



@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for("index"))

@app.route('/about')
def about():

    return render_template('about.html')

    
@app.route('/ageConfirmation')
def ageConfirmation():

    return render_template("ageConfirmation.html")

    
@app.route('/ageSubmit')
def ageSubmit():
    args = request.args
    print(args.get("old"))
    # return render_template('about.html')
    if "username" in session:
        username = session["username"]
        return redirect(url_for("home"))
    else:
        return redirect(url_for("index"))

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



@app.route("/upload", methods=["POST", "GET"])
def upload():
    print('Request for upload received')
    if "username" not in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        print('POSt Request for upload received')
        image = request.files['img']
        image.seek(0)
        image_bytes = image.read()

        # exif_img = Image(image)
        # #Extract coordinates of the taken image
        coordinates = []
        # print(exif_img.has_exif)
        # if(exif_img.has_exif):
        #     try:
        #         gps_latitude =exif_img.gps_latitude
        #         gps_longitude = exif_img.gps_longitude
        #         print(gps_latitude)
        #         print(gps_longitude)
        #         gps_latitude_ref = exif_img.gps_latitude_ref
        #         gps_longitude_ref = exif_img.gps_longitude_ref
        #         print(gps_latitude_ref)
        #         print(gps_longitude_ref)
        #         if gps_latitude and gps_longitude and gps_latitude_ref and gps_longitude_ref:
        #             coordinates = convert_coordinates(gps_latitude, gps_longitude, gps_latitude_ref, gps_longitude_ref)
        #     except Exception as e:
        #         print(e)

        # print(coordinates)
        try:
            photoCO = getGeo.geoGetter(io.BytesIO(image_bytes))
            print(photoCO)
            coordinates.append(photoCO[0])
            coordinates.append(photoCO[1])
        except Exception as e:
            print(e)
        print(coordinates)
        print(len(coordinates))
        if len(coordinates) != 2:
            rand_lat = random.uniform(-0.1, 0.1)
            rand_lon = random.uniform(-0.1, 0.1)
            coordinates = [47.759+rand_lat, -122.189+rand_lon] #uw bothell coordinates
        #generating own id for aws s3 filenames
        id = uuid.uuid4().hex
        image.filename = id

        upload_file_to_s3(image, app.config["S3_BUCKET"])
        fileLocation='http://' + os.getenv('S3_BUCKET_NAME') + '.s3.amazonaws.com/' + image.filename

        caption = request.form.get("caption")

        hashtags = request.form.getlist('hashtags')
        # print(request.form)
        # print(request.form.getlist('hashtags'))
        plant_suggestions = []
        if("wild_plants" in hashtags or "garden_plants" in hashtags):

            suggestions = identify(image_bytes)
            plant_suggestions = suggestions if len(suggestions) > 0 else ['N/A']
        
        # plant_suggestions = []
        post_input = {'_id': id,
                      'timestamp': datetime.datetime.utcnow(),
                      'username':session['username'], 
                      'image': fileLocation, 
                      'caption': caption, 
                      'hashtags': hashtags, 
                      'plant_suggestions': plant_suggestions,
                      'lat': coordinates[0],
                      'lon': coordinates[1],
                      'likes': 0,
                      'liked_users': [],
                      'comments': []
        }
        posts.insert_one(post_input)
        users.find_one_and_update({'username':session['username']}, {'$push': {'posts': post_input}})
        return redirect(url_for('home'))
    return render_template('upload.html')

def upload_file_to_s3(file, bucket_name, acl="public-read"):
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=app.config['S3_KEY'],
            aws_secret_access_key=app.config['S3_SECRET']
        )
        #file_data = file.read()
        file.seek(0)
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type    #Set appropriate content type as per the file
            }
        )
        #s3.put_object(Body=file_data, Bucket=bucket_name, Key=file.filename)
    except Exception as e:
        print("Something Happened: ", e)
    #     return e
    # return "{}{}".format(app.config["S3_LOCATION"], file.filename)




#@app.route("/post", methods=["POST", "GET"])
def post(id):
    post_found = posts.find_one({"_id": id}) 
    if post_found:
        print('Post Found')
        #encoded = base64.b64encode(post_found['image'])
        #return render_template('post.html', message=post_found['image'])
        print(post_found)
        return post_found
    print('Post Not Found')
    return None

#@app.route("/getposts", methods=["POST", "GET"])
def getposts():
    return list(posts.find({}).sort('timestamp', pymongo.DESCENDING))

def user_info(username):
    user_found = users.find_one({'username': username})
    info = {}
    if user_found:
        info = {}
        info['username'] = user_found['username']
        try:
            info['profile_picture'] = user_found['profile_picture']
            info['bio'] = user_found['bio']
        except:
            info['profile_picture'] = "./https://wildtrekimages.theohal.repl.co/images/profile.png"
            info['bio'] = "No Bio Yet"
        info['posts'] = user_found['posts']
    return info

@app.route("/updatebio", methods=["POST"])
def update_bio():
    if 'username' in session:
        try:
            text = request.form.get("bio")
            users.find_one_and_update({'username': session['username']}, {'$set': {'bio': text}})
        except Exception as e:
            print(e)
    return redirect(url_for('home'))

@app.route("/updateprofilepicture", methods=["POST"])
def update_profile_picture():
    if 'username' in session:
        try:
            image = request.files['img']
            image.filename = session['username'] + 'profile'
            upload_file_to_s3(image, app.config["S3_BUCKET"])
            fileLocation='http://' + os.getenv('S3_BUCKET_NAME') + '.s3.amazonaws.com/' + image.filename
            users.find_one_and_update({'username': session['username']}, {'$set': {'profile_picture': fileLocation}})
        except Exception as e:
            print(e)
    return redirect(url_for('home'))

@app.route("/like", methods=["POST"])
def like():
    if 'username' in session:
        try:
            args = request.args
            if(args.get("id") == None):
                return redirect(url_for("home"))
            id = args.get("id")
            post_found = posts.find_one({"_id": id}) 
            if post_found:
                if session['username'] in post_found['liked_users']:
                    posts.find_one_and_update({"_id": id}, {'$inc': {'likes': -1}, '$pull': { 'liked_users': { '$in': [session['username']]}}})
                else:
                    posts.find_one_and_update({"_id": id}, {'$inc': {'likes': 1}, '$push': {'liked_users': session['username']}})
        except Exception as e:
            print(e)
    return redirect(url_for('home'))

@app.route("/comment", methods=["POST"])
def comment():
    if 'username' in session:
        try:
            args = request.args
            if(args.get("id") == None):
                return redirect(url_for("home"))
            id = args.get("id")
            print(request.json)
            comment = session['username'] + ': ' + request.json["comment"]
            post_found = posts.find_one({"_id": id}) 
            if post_found:
                posts.find_one_and_update({"_id": id}, {'$push': {'comments': comment}})
        except Exception as e:
            print(e)
    return redirect(url_for('home'))

def identify(image_bytes):
    print('Identifying image')
    encoded = base64.b64encode(image_bytes)
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
    mapPosts = getposts()

    # Initialize variables
    markers = ''
    for node in mapPosts:
    # node = mapPosts[0]
    # Create unique ID for each marker
        idd = "post"+str(node["_id"])

        # Check if shops have name and website in OSM
        try:
            image = node["image"]
        except:
            image = 'null'

        try:
            caption = node["caption"]
        except:
            caption = 'null'

        try:
            lat = node["lat"]+ (random.random()-.5)*.001
            lon = node["lon"]+ (random.random()-.5)*.001
        except:
            print("no lat")
            lat = 47.7606092 + (random.random()-.5)*.00001
            lon = -122.188031+ (random.random()-.5)*.00001

        # Create the marker and its pop-up for each shop
        markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                    {idd}.addTo(map).bindPopup(\'<a class=\"mapPost\" href=\"/onePost?id={idd}\"><img src={image}><div class=\"mapPostCaption\">{caption}</div></a>\');".format(idd=idd, latitude=lat,\
                                                                                longitude=lon,\
                                                                                image=image,\
                                                                                caption=caption
                                                                                )

    # Render the page with the map
    return render_template('map.html', markers=markers, lat=47.654170, lon=-122.302610)

if __name__ == '__main__':
   app.run(debug=True)
