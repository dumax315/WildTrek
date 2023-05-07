import os

os.chdir('C://Users/theom/Documents/GitHub/WildTrek/static/images/carwithMeta.jpg')
image_list = os.listdir()
image_list = [a for a in image_list if a.endswith('jpg')]

print(image_list)