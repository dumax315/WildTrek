import os

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

app = Flask(__name__)


@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

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
