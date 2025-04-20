import os
import subprocess
from datetime import datetime
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

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

@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        # Get the payload from the request
        payload = request.get_json()
        script_name = payload.get('script_name')

        # Validate script name
        if script_name not in SCRIPT_MAP:
            return jsonify({
                'status': 'error',
                'message': 'Invalid script name!'
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
            "INSERT INTO script_logs (timestamp, script_name, output, error) VALUES (%s, %s, %s, %s)",
            (datetime.now(), script_name, output, error)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': f'Script {script_name} executed successfully!',
            'output': output,
            'error': error
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
