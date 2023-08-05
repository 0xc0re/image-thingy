
import os
import secrets
from flask import Flask, request, send_from_directory, Response
from PIL import Image
import tempfile
import threading
import time
from werkzeug.exceptions import BadRequest

# Configuration from environment variables
UPLOAD_FOLDER = tempfile.mkdtemp()
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '2097152'))  # Default to 2MB

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

    # Place the original image in the four corners
    new_image.paste(original_image, (0, 0))
    new_image.paste(original_image, (original_width, 0))
    new_image.paste(original_image, (0, original_height))
    new_image.paste(original_image, (original_width, original_height))

    # Save the new image
    new_image.save(output_path)
    print(f"Image saved at {output_path}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        raise BadRequest('No file part')
    file = request.files['file']
    if file.filename == '':
        raise BadRequest('No selected file')

    # Check file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    if file_length > MAX_FILE_SIZE:
        raise BadRequest('File size must be under 2MB')

    # Check if file is an image
    file.seek(0)
    try:
        Image.open(file)
    except:
        raise BadRequest('Invalid image file')
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
    app.run(debug=False)
