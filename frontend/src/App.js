import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import Landing from './pages/Landing';
import Auth from './pages/Auth';
import Dashboard from './pages/Dashboard';
import Recorder from './pages/Recorder';
import TranscriptionDetail from './pages/TranscriptionDetail';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Axios interceptor for auth
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return <div className="loading-screen">Carregando...</div>;
  }

  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={user ? <Navigate to="/dashboard" /> : <Landing />} />
          <Route 
            path="/auth" 
            element={user ? <Navigate to="/dashboard" /> : <Auth onLogin={handleLogin} />} 
          />
          <Route 
            path="/dashboard" 
            element={user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />} 
          />
          <Route 
            path="/recorder" 
            element={user ? <Recorder user={user} /> : <Navigate to="/auth" />} 
          />
          <Route 
            path="/transcription/:id" 
            element={user ? <TranscriptionDetail user={user} /> : <Navigate to="/auth" />} 
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export { API };
export default App;