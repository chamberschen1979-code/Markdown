const { spawn } = require('child_process');
const path = require('path');

exports.handler = async (event, context) => {
  // Start the Streamlit server
  const streamlitProcess = spawn('python3', [
    '-m', 'streamlit', 'run', 'streamlit_app.py',
    '--server.port', '8080',
    '--server.address', '0.0.0.0',
    '--server.headless', 'true'
  ], {
    cwd: path.resolve(__dirname, '../../'),
    env: {
      ...process.env,
      PYTHONPATH: path.resolve(__dirname, '../../')
    }
  });

  // Wait for the server to start
  await new Promise((resolve) => {
    streamlitProcess.stdout.on('data', (data) => {
      if (data.toString().includes('Local URL')) {
        resolve();
      }
    });
  });

  // Return a 302 redirect to the Streamlit server
  return {
    statusCode: 302,
    headers: {
      Location: 'http://localhost:8080'
    }
  };
};
