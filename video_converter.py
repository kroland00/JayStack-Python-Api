from flask import Flask, request
import moviepy.editor as moviepy
import os.path
from os import path
from celery import Celery
from waitress import serve

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Create converted videos folder if not exists.
if not os.path.exists('converted_mp4_videos'):
    os.makedirs('converted_mp4_videos')
if not os.path.exists('avi_files'):
    os.makedirs('avi_files')
if not os.path.exists('gif_files'):
    os.makedirs('gif_files')

# Delete stopped converting tmp files.
projectFolder = os.listdir()
for item in projectFolder:
    if item.endswith(".mp3"):
        os.remove(item)

# Convert avi files to mp4 and delete tmp after.
@celery.task
def convertSavedAvi():
    for video in os.listdir('./avi_files'):
        clip = moviepy.VideoFileClip('avi_files/' + video)
        clip.write_videofile('converted_mp4_videos/' + video.split('.')[0] + '.mp4')
        os.remove('avi_files/' + video)
    
# Convert gif files to mp4 and delete tmp after.
@celery.task
def convertSavedGif():
    for video in os.listdir('./gif_files'):
        clip = moviepy.VideoFileClip('gif_files/' + video)
        clip.write_videofile('converted_mp4_videos/' + video.split('.')[0] + '.mp4')
        os.remove('gif_files/' + video)

# Avi to mp4 endpoint.
@celery.task(rate_limit='30/m')
@app.route('/avi_to_mp4', methods=['POST'])
def convertAviToMp4():
    video = request.files['file']
    video.save('./avi_files/' + video.filename)
    clip = moviepy.VideoFileClip('avi_files/' + video.filename)
    clip.write_videofile('converted_mp4_videos/' + video.filename.split('.')[0] + '.mp4')
    os.remove('avi_files/' + video.filename)

    return 'Success'

# Gif to mp4 endpoint.
@celery.task(rate_limit='30/m')
@app.route('/gif_to_mp4', methods=['POST'])
def convertGifToMp4():
    video = request.files['file']
    video.save('./gif_files/' + video.filename)
    clip = moviepy.VideoFileClip('gif_files/' + video.filename)
    clip.write_videofile('converted_mp4_videos/' + video.filename.split('.')[0] + '.mp4')
    os.remove('gif_files/' + video.filename)

    return 'Success'

convertSavedAvi()
convertSavedGif()

serve(app, host='0.0.0.0', port=8080)