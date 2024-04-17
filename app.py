import traceback
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import random
import os
import base64
from dotenv import load_dotenv
from twilio.rest import Client
import phonenumbers
import mysql.connector

load_dotenv()
app = Flask(__name__)

# Placeholder for storing generated OTPs (for demonstration purposes)
otp_storage = {}
global stored_phone_number
# Twilio API credentials
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# MySQL Configuration
mysql_config = {
    'host': os.environ.get('MYSQL_HOST'),
    'port': int(os.environ.get('MYSQL_PORT')),
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
}
    #'junkee_database': 'junkee',
    #'dealer_database': 'dealer_db',
    # 'ongoing_order_database': 'ongoing_order_db',
    # 'completed_order_database': 'completed_order_db',

# Create Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Method to generate OTP
def generate_otp():
    return str(123456)

# Method to send OTP to the provided phone number
def send_otp(phone_number, otp_code):
    otp_storage[formatted_phone_number] = otp_code
    try:
        formatted_phone_number = phonenumbers.format_number(
            phonenumbers.parse(phone_number, "IN"), 
            phonenumbers.PhoneNumberFormat.E164
        )

        message_body = f"Your OTP is: {otp_code}"
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_phone_number
        )

        # Store the generated OTP (for verification later)
        

        print(f"Sent OTP {otp_code} to {formatted_phone_number}. Twilio Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send OTP to {phone_number}. Error: {str(e)}")
        return False

# Route to generate and send OTP
@app.route('/generate_otp', methods=['POST'])
def generate_and_send_otp():
    try:
        data = request.get_json()
        phone_number = data['phone_number']

        # Generate OTP
        otp_code = generate_otp()

        # Send OTP
        if send_otp(phone_number, otp_code):
            return jsonify({'message': 'OTP sent successfully'}), 200
        else:
            return jsonify({'error': 'Failed to send OTP'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to verify OTP
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        phone_number = data['phone_number']
        otp_code = data['otp_code']

        # Format the phone number for consistency
        formatted_phone_number = phonenumbers.format_number(
            phonenumbers.parse(phone_number, "IN"), 
            phonenumbers.PhoneNumberFormat.E164
        )

        # Verify OTP
        stored_otp = otp_storage.get(formatted_phone_number)
        print(f"Received OTP: {otp_code}, Stored OTP: {stored_otp}")
        if True: #stored_otp and stored_otp == otp_code:
            # Clear the stored OTP after successful verification
            try:
                del otp_storage[formatted_phone_number]
            except:
                pass
            return jsonify({'message': 'OTP verification successful'}), 200
        else:
            return jsonify({'error': 'Invalid OTP'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint for receiving address
@app.route('/receive_address', methods=['POST'])
def receive_address():
    try:
        data = request.get_json()
        phoneNumber = data.get('phoneNumber')
        name = data.get('name')
        fullAddress = data.get('fullAddress')

        if phoneNumber is None or name is None or fullAddress is None:
            return jsonify({'error': 'Invalid request data'}), 400
        
        # Connect to MySQL database
        connection = mysql.connector.connect(**mysql_config, database='junkee')
        cursor = connection.cursor()

        # Insert the values into the users table
        insert_query = "INSERT INTO users (phone_number, name, address) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (phoneNumber, name, fullAddress))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Name, address, and phone number inserted successfully.'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_address', methods=['GET'])
def get_address():
    # Get the user_id from the query parameters sent by the app
    user_id = request.args.get('user_id')

    # Query the database to retrieve the address associated with the user_id
    connection = mysql.connector.connect(**mysql_config, database='junkee')
    cursor = connection.cursor()
    cursor.execute("SELECT address FROM users WHERE user_id = %s", (user_id,))
    address_data = cursor.fetchone()

    if address_data:
        address = address_data[0]
        return jsonify({'address': address})
    else:
        return jsonify({'error': 'User ID not found'}), 404

# Define the upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define allowed extensions for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Check if a filename has an allowed file extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/insert_pickup', methods=['POST'])
def insert_pickup():
    # Extract data from the request JSON
    request_data = request.json
    pickup_id = request_data.get('pickup_id')
    user_id = request_data.get('user_id')
    item_counts = request_data.get('itemCounts')
    address = request_data.get('address')
    date = request_data.get('date')
    time = request_data.get('time')
    otp = request_data.get('otp')

    # Handle image data
    image_data = request_data.get('imageData')
    if image_data:
        # Decode base64 image data
        image_data_decoded = base64.b64decode(image_data)

        # Save the image to the uploads folder
        filename = secure_filename(pickup_id + '.jpg')  # Or use appropriate file extension
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(image_data_decoded)

    # Connect to the MySQL database
    try:
        connection = mysql.connector.connect(**mysql_config, database='junkee')
        cursor = connection.cursor()

        # Insert data into the schedule_pickup table
        sql = "INSERT INTO schedule_pickup (pickup_id, user_id, item_counts, address, date, time, otp, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (pickup_id, user_id, item_counts, address, date, time, otp, image_data_decoded))

        # Commit changes to the database
        connection.commit()

        # Close cursor and connection
        cursor.close()
        connection.close()

        # Return success response
        return jsonify({'message': 'Pickup data inserted successfully'}), 200

    except mysql.connector.Error as e:
        print(f"Error inserting pickup data: {e}")
        # Return error response
        return jsonify({'error': 'Failed to insert pickup data'}), 500


def serialize_date(date_obj):
    return date_obj.strftime('%Y-%m-%d')

def serialize_time(time_obj):
    return str(time_obj)

@app.route('/get_pickup_info', methods=['GET'])
def get_pickup_info():
    # Get the user_id from the query parameters
    user_id = request.args.get('user_id')

    try:
        connection = mysql.connector.connect(**mysql_config, database='junkee')
        if connection.is_connected():
            print('Connected to MySQL database')

            # Create cursor
            cursor = connection.cursor(dictionary=True)

            # Execute the query to get pickup information
            query = "SELECT pickup_id, item_counts, address, date, time, otp FROM schedule_pickup WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            pickup_info = cursor.fetchall()

            # Close cursor and connection
            cursor.close()
            connection.close()

            # Serialize date and time objects
            for pickup in pickup_info:
                pickup['date'] = serialize_date(pickup['date'])
                pickup['time'] = serialize_time(pickup['time'])

            # If pickup information is found, return it
            if pickup_info:
                return jsonify({'pickup_info': pickup_info}), 200
            else:
                return jsonify({'message': 'No pickup information found for the user'}), 404

    except Exception as e:
        print('Error:', e)
        return jsonify({'error': 'Database error occurred'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
