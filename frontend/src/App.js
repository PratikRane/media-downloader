import React from 'react';

const App = () => {
  const handleRunScript = async () => {
    try {
      const response = await fetch('http://services.dystrophy.homelab.local:5000/run-script', { method: 'POST' });
      const data = await response.json();
      console.log(data);
    } catch (error) {
      console.error("Error running script:", error);
    }
  };

  return (
    <div>
      <button onClick={handleRunScript}>Run Command</button>
    </div>
  );
};

export default App;
