import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <h1 className="text-xl font-bold text-gray-900">ECP Store</h1>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<div className="p-8"><h2>Welcome to ECP</h2></div>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
