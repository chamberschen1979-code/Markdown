import subprocess
import os

# Set the port for Streamlit
PORT = os.environ.get('PORT', 8000)

def handler(event, context):
    # Start the Streamlit app
    subprocess.run([
        'streamlit', 'run', 'streamlit_app.py',
        '--server.port', str(PORT),
        '--server.address', '0.0.0.0'
    ])
