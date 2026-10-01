import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import '@fontsource-variable/manrope'
import '@fontsource/newsreader/600.css'
import './styles.css'
import './showcase.css'
import './components/ui/components.css'
import './account.css'
import './playlists.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter><App /></BrowserRouter>
  </React.StrictMode>,
)
