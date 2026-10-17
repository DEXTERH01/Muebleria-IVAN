import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/index.css';
import './styles/rest.css';
import './styles/admin.css';
import './styles/ai.css';
createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
