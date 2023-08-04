import json
from flask import Flask, request, send_from_directory, Response, after_this_request
from PIL import Image
import os
import secrets
import tempfile
import shutil
import threading
import time

# Read configuration from JSON file
with open('config.json') as f:
    config = json.load(f)

UPLOAD_FOLDER = config['upload_folder']
MAX_FILE_SIZE = config['max_file_size']

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

def delayed_delete(file_path, delay_seconds=10):
    time.sleep(delay_seconds)
    os.remove(file_path)

def duplicate_image(image_path, output_path):
    # Open the original image
    original_image = Image.open(image_path)
    original_width, original_height = original_image.size

    # Create a new image with twice the width and height of the original image
    new_image = Image.new('RGB', (original_width * 2, original_height * 2))

    # Place the original image in the top-left corner
    new_image.paste(original_image, (0, 0))

    # Place the original image in the top-right corner
    new_image.paste(original_image, (original_width, 0))

    # Place the original image in the bottom-left corner
    new_image.paste(original_image, (0, original_height))

    # Place the original image in the bottom-right corner
    new_image.paste(original_image, (original_width, original_height))

    # Save the new image
    new_image.save(output_path)
    print(f"Image saved at {output_path}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    if file_length > MAX_FILE_SIZE:
        return 'File size must be under 2MB', 400

    # Check if file is an image
    file.seek(0)
    try:
        Image.open(file)
    except:
        return 'Invalid image file', 400
    file.seek(0)

    # Generate a secure random filename
    input_filename = secrets.token_hex(8) + os.path.splitext(file.filename)[1]
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
    output_filename = 'output_' + input_filename
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    file.save(input_path)
    duplicate_image(input_path, output_path)

    # Delete the input file immediately
    os.remove(input_path)

    # Schedule the delayed deletion of the output file
    threading.Thread(target=delayed_delete, args=(output_path,)).start()

    # Determine the MIME type based on the file extension
    mimetype = None
    if output_path.lower().endswith('.png'):
        mimetype = 'image/png'
    elif output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
        mimetype = 'image/jpeg'
    elif output_path.lower().endswith('.gif'):
        mimetype = 'image/gif'

    return send_from_directory(app.config['UPLOAD_FOLDER'], output_filename, as_attachment=True, download_name='output_image.jpg', mimetype=mimetype)

if __name__ == '__main__':
    app.run(debug=True)