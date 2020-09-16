import React from 'react';
import logo from './logo.svg';
import AnnotationViewer from './components/AnnotationViewer';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="header">
          <h1>Annotation Verification</h1>
      </header>
      <div className="content">
        <AnnotationViewer />
      </div>
      <div className="footer">
      </div>
    </div>
  );
}

export default App;
