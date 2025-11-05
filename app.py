import traceback
from flask import Flask, request, jsonify
import os
import mysql.connector

app = Flask(__name__)

# ---------- MYSQL CONFIGURATION ----------
mysql_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'q1p0!@#)(*WASD',
    'database': 'junkee'
}


# ---------- ADDRESS ENDPOINTS ----------

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
        connection = mysql.connector.connect(**mysql_config)
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
    try:
        user_id = request.args.get('user_id')
        connection = mysql.connector.connect(**mysql_config)
        cursor = connection.cursor()
        cursor.execute("SELECT address FROM users WHERE user_id = %s", (user_id,))
        address_data = cursor.fetchone()

        cursor.close()
        connection.close()

        if address_data:
            address = address_data[0]
            return jsonify({'address': address})
        else:
            return jsonify({'error': 'User ID not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------- PICKUP ENDPOINTS ----------

@app.route('/insert_pickup', methods=['POST'])
def insert_pickup():
    try:
        request_data = request.json
        pickup_id = request_data.get('pickup_id')
        user_id = request_data.get('user_id')
        item_counts = request_data.get('itemCounts')
        address = request_data.get('address')
        date = request_data.get('date')
        time = request_data.get('time')
        otp = request_data.get('otp')  # Optional — keeping in schema

        # Insert into database (no image)
        connection = mysql.connector.connect(**mysql_config)
        cursor = connection.cursor()

        sql = """INSERT INTO schedule_pickup (pickup_id, user_id, item_counts, address, date, time, otp) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (pickup_id, user_id, item_counts, address, date, time, otp))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Pickup data inserted successfully'}), 200

    except mysql.connector.Error as e:
        print(f"Error inserting pickup data: {e}")
        return jsonify({'error': 'Failed to insert pickup data'}), 500


def serialize_date(date_obj):
    return date_obj.strftime('%Y-%m-%d')


def serialize_time(time_obj):
    return str(time_obj)


@app.route('/get_pickup_info', methods=['GET'])
def get_pickup_info():
    user_id = request.args.get('user_id')

    try:
        connection = mysql.connector.connect(**mysql_config)
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = """ SELECT pickup_id, item_counts, address, date, time, otp FROM schedule_pickup WHERE user_id = %s"""
            cursor.execute(query, (user_id,))
            pickup_info = cursor.fetchall()

            cursor.close()
            connection.close()

            # Format date/time
            for pickup in pickup_info:
                pickup['date'] = serialize_date(pickup['date'])
                pickup['time'] = serialize_time(pickup['time'])

            if pickup_info:
                return jsonify({'pickup_info': pickup_info}), 200
            else:
                return jsonify({'message': 'No pickup information found for the user'}), 404

    except Exception as e:
        print('Error:', e)
        return jsonify({'error': 'Database error occurred'}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
