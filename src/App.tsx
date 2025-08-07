/**
 * Main App component - Router configuration for Ollama Chat
 */
import { HashRouter, Route, Routes } from 'react-router'
import HomePage from './pages/Home'
import { Toaster } from './components/ui/toaster'

export default function App() {
  return (
    <HashRouter>
      <div className="min-h-screen">
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
        <Toaster />
      </div>
    </HashRouter>
  )
}
