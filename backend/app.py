import os
import subprocess
from datetime import datetime
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS
 
app = Flask(__name__)
CORS(app, origins=["http://192.168.0.71:3000", "http://192.168.0.71:5000"])
 
# Get DB credentials from environment variables
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME')
DB_HOST = os.environ.get('DB_HOST', 'db')  # default to 'db' service if not set


# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
       dbname=DB_NAME
    )
    return conn

# Dictionary to map script names to their corresponding file paths
SCRIPT_MAP = {
    'script1': '/scripts/script1.sh',
    'script2': '/scripts/script2.sh',
    'script3': '/scripts/script3.sh'
}


# Endpoint to fetch channel names
@app.route('/get-channels', methods=['GET'])
def get_channels():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT channel_name FROM channels order by channel_name")
        channels = cursor.fetchall()
        cursor.close()
        conn.close()

        # Extract channel names from result
        channel_names = [channel[0] for channel in channels]

        return jsonify({'channels': channel_names})
    
    except Exception as e:
        print(str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        # Get the payload from the request
        payload = request.get_json()
        script_name = payload.get('script_name')
        channel_name = payload.get('channel_name')

        # Null check
        if script_name is None or "":
            return jsonify({
                'status': 'error',
                'message': 'No script name provided!'
            }), 400
        
        # Validate script name
        if script_name not in SCRIPT_MAP:
            return jsonify({
                'status': 'error',
                'message': 'Invalid script name!',
                'script_name': script_name,
            }), 400

        # Get the script path based on the provided script name
        script_path = SCRIPT_MAP[script_name]

        # Run the corresponding command-line script
        result = subprocess.run(['bash', script_path], capture_output=True, text=True)
        output = result.stdout
        error = result.stderr

        # Insert the result into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO script_logs (timestamp, script_name, output, error, channel_name) VALUES (%s, %s, %s, %s, %s)",
            (datetime.now(), script_name, output, error, channel_name)
        )
        conn.commit()
        cursor.close()
        conn.close()

        if error is None or "":
         return jsonify({
             'status': 'success',
             'message': f'Script {script_name} executed successfully!',
             'output': output,
             'error': error
         })
        else:
         return jsonify({
             'status': 'Fail',
             'message': f'Script {script_name} failed!',
             'output': output,
             'error': error
         })
    except Exception as e:
        print(str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Endpoint to add a new channel
@app.route('/add-channel', methods=['POST'])
def add_channel():
    try:
        # Get the form data from the request payload
        data = request.get_json()
        channel_name = data.get('channel_name')
        use_filter = data.get('use_filter', 0)  # Default to 0 if not provided
        filter_string = data.get('filter_string', '')
        channel_url = data.get('channel_url')
        auto_download_videos = data.get('auto_download_videos', 0)
        auto_download_shorts = data.get('auto_download_shorts', 0)
        auto_download_livestream = data.get('auto_download_livestream', 0)
        monitor_videos = data.get('monitor_videos', 0)
        monitor_shorts = data.get('monitor_shorts', 0)
        monitor_livestream = data.get('monitor_livestream', 0)


        # Validate required fields
        if not channel_name or not channel_url:
            return jsonify({'status': 'error', 'message': 'Channel name and URL are required.'}), 400

        # Insert the new channel into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO channels (added_timestamp, channel_name, use_filter, filter_string, 
                                  channel_url, auto_download_videos, auto_download_shorts, auto_download_livestream, monitor_videos, monitor_shorts, monitor_livestream)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (datetime.now(), channel_name, use_filter, filter_string, channel_url, 
             auto_download_videos, auto_download_shorts, auto_download_livestream, monitor_videos, monitor_shorts, monitor_livestream)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Channel added successfully.'})

    except Exception as e:
        print(str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Endpoint to get a specific channel by channel_name
@app.route('/get-channel', methods=['GET'])
def get_channel():
    try:
        channel_name = request.args.get('channel_name')

        if not channel_name:
            return jsonify({'status': 'error', 'message': 'Channel name is required.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM channels WHERE channel_name = %s", (channel_name,))
        channel = cursor.fetchone()
        cursor.close()
        conn.close()

        if not channel:
            return jsonify({'status': 'error', 'message': 'Channel not found.'}), 404

        channel_data = {
            'id': channel[0],
            'added_timestamp': channel[1],
            'channel_name': channel[2],
            'use_filter': channel[3],
            'filter_string': channel[4],
            'channel_url': channel[5],
            'auto_download_videos': channel[6],
            'auto_download_shorts': channel[7],
            'auto_download_livestream': channel[8],
            'monitor_videos': channel[9],
            'monitor_shorts': channel[10],
            'monitor_livestream': channel[11]
        }

        return jsonify({'status': 'success', 'channel': channel_data})

    except Exception as e:
        print(str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Endpoint to update a specific channel
@app.route('/update-channel', methods=['POST'])
def update_channel():
    try:
        data = request.get_json()
        channel_name = data.get('channel_name')
        use_filter = data.get('use_filter')
        filter_string = data.get('filter_string')
        channel_url = data.get('channel_url')
        auto_download_videos = data.get('auto_download_videos')
        auto_download_shorts = data.get('auto_download_shorts')
        auto_download_livestream = data.get('auto_download_livestream')
        monitor_videos = data.get('monitor_videos')
        monitor_shorts = data.get('monitor_shorts')
        monitor_livestream = data.get('monitor_livestream')

        if not channel_name:
            return jsonify({'status': 'error', 'message': 'Channel name is required.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE channels 
            SET use_filter = %s, filter_string = %s, channel_url = %s, 
                auto_download_videos = %s, auto_download_shorts = %s, auto_download_livestream = %s,
                monitor_videos = %s, monitor_shorts = %s, monitor_livestream = %s
            WHERE channel_name = %s
        """, (use_filter, filter_string, channel_url, auto_download_videos, auto_download_shorts, auto_download_livestream, monitor_videos, monitor_shorts, monitor_livestream, channel_name))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Channel updated successfully.'})

    except Exception as e:
        print(str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    print('Starting backend. Listening on port 5000')
    app.run(host='0.0.0.0', port=5000)
