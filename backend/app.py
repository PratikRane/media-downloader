from flask import Flask, jsonify
import subprocess
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASS', 'password'),
        dbname=os.environ.get('DB_NAME', 'mydb')
    )
    return conn

@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        result = subprocess.run(['bash', '/path/to/script.sh'], capture_output=True, text=True)
        output = result.stdout
        error = result.stderr

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO script_logs (timestamp, output, error) VALUES (%s, %s, %s)",
            (datetime.now(), output, error)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': 'Script executed successfully!',
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
