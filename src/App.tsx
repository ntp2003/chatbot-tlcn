import React, { useState } from 'react';
import Login from './components/Auth/Login';
import ChatWindow from './components/Chat/ChatWindow';

const App: React.FC = () => {
  const [token, setToken] = useState<string | null>(null);

  if (!token) {
    return <Login onLogin={setToken} />;
  }

  return <ChatWindow />;
};

export default App; 