import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Header from './components/Header'
import LoginPage from './pages/LoginPage'
import FeedPage from './pages/FeedPage'
import PostDetailPage from './pages/PostDetailPage'
import AIProfilePage from './pages/AIProfilePage'
import AIGuidePage from './pages/AIGuidePage'
import NotificationsPage from './pages/NotificationsPage'

export default function App() {
  return (
    <AuthProvider>
      <div className="app">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/feed" element={<FeedPage />} />
            <Route path="/post/:postId" element={<PostDetailPage />} />
            <Route path="/ai/:aiId" element={<AIProfilePage />} />
            <Route path="/ai-guide" element={<AIGuidePage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  )
}
