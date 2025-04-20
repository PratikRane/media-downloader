import os
import time
import subprocess
import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Get DB credentials from environment variables
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME')
DB_HOST = os.environ.get('DB_HOST', 'db')

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    return conn

# Function to log job execution into the database
def log_script_execution(channel_name, script_name, status, output):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO script_logs (channel_name, script_name, execution_timestamp, status, output)
            VALUES (%s, %s, %s, %s, %s)
        """, (channel_name, script_name, datetime.now(), status, output))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error logging execution: {e}")

# Function to run a script for auto-download jobs
def run_script_for_channel(channel_name, script_name):
    try:
        print(f"Running {script_name} for channel: {channel_name}")

        # Assuming you have a command-line script for each job
        # For example: /scripts/video_download.sh, /scripts/shorts_download.sh, etc.
        script_path = f"/scripts/{script_name}.sh"  # Modify according to your script locations
        command = f"bash {script_path} {channel_name}"

        # Run the script
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            status = 'success'
            output = stdout.decode('utf-8')
        else:
            status = 'error'
            output = stderr.decode('utf-8')

        # Log the execution result
        log_script_execution(channel_name, script_name, status, output)
        print(f"Job for {channel_name} completed with status: {status}")

    except Exception as e:
        print(f"Error running script for {channel_name}: {e}")

# Function to fetch channels with auto-download enabled for videos, shorts, or livestream
def fetch_channels_for_auto_download(auto_download_type):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT channel_name FROM channels 
            WHERE %s = 1
        """, (auto_download_type))

        channels = cursor.fetchall()
        cursor.close()
        conn.close()

        print(f"{auto_download_type} is enabled for {channels}")
        return [channel[0] for channel in channels]

    except Exception as e:
        print(f"Error fetching channels: {e}")
        return []

# Function to run the auto-download video job
def auto_download_videos_job():
    print("Running auto-download videos job...")
    channels = fetch_channels_for_auto_download("auto_download_videos")
    for channel in channels:
        run_script_for_channel(channel, "auto_download_videos")

# Function to run the auto-download shorts job
def auto_download_shorts_job():
    print("Running auto-download shorts job...")
    channels = fetch_channels_for_auto_download("auto_download_shorts")
    for channel in channels:
        run_script_for_channel(channel, "auto_download_shorts")

# Function to run the auto-download livestream job
def auto_download_livestream_job():
    print("Running auto-download livestream job...")
    channels = fetch_channels_for_auto_download("auto_download_livestream")
    for channel in channels:
        run_script_for_channel(channel, "auto_download_livestream")

# Function to initialize the scheduler
def initialize_scheduler():
    scheduler = BackgroundScheduler()

    # Add the jobs to be run at specific intervals
    scheduler.add_job(auto_download_videos_job, 'interval', hours=24)  # Runs every 24 hours
    scheduler.add_job(auto_download_shorts_job, 'interval', hours=24)
    scheduler.add_job(auto_download_livestream_job, 'interval', hours=24)

    # Start the scheduler
    scheduler.start()

    # Keep the main thread alive to keep the scheduler running
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Shut down the scheduler gracefully when exiting
        scheduler.shutdown()

if __name__ == '__main__':
    initialize_scheduler()
