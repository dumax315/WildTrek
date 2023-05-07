# WildTrek

A pwa that motivates you to get outside, explore the wilderness, and learn more about the nature all around you. It allows users to upload pictures and if you are 13+, you can share them with people around you.

- Goals of the project: 
Create a functioning prototype of a pwa where users can upload pictures on their account, view others (if 13+), and learn more about the environment.
Desired user experience: Have the users be able to interact with the functions we implemented in the basic web app. Have them create an account, upload pictures, and view location information.
- Implementation details: 
We used Figma to create the design of how each page will look and to plan the flow of where certain features went, and how things are triggered. We used Visual Studio Code to implement our code, using css, html, Jinja rendering engine to do the front-end, Python (Flask) on the backend, MongoDB and AWS S3 for storage and Azure Web Apps for Deployment. For plant detection, we used Plant.id API.  
- Issues encountered:
bugs fixed or still present: One of the issues we encountered is the picture didn’t upload properly and it was fixed by pointing the read cursor to the start of the file before every upload. Another main issue was it was more difficult than anticipated to extract GPS metadata from the uploaded images and we decided to use the ‘exif’ Python package. 
- Future work to be done: 
Implement profile photos, replies to comments, thumbnails for faster loading times, friends/following, provide more accessibility, include more languages, and expand outside of the U.S.
