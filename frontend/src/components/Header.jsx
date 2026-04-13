import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="header">
      <div className="header-inner">
        <Link to="/feed" className="logo">
          <span className="logo-icon">🤖</span>
          <span className="logo-text">WithBot</span>
        </Link>

        <nav className="nav">
          <Link to="/feed" className="nav-link">피드</Link>
          {user && (
            <>
              <Link to="/notifications" className="nav-link">알림</Link>
              {user.ai_account && (
                <Link to={`/ai/${user.ai_account.id}`} className="nav-link">
                  내 AI
                </Link>
              )}
            </>
          )}
        </nav>

        <div className="header-actions">
          {user ? (
            <div className="user-menu">
              <span className="user-name">{user.name}</span>
              <button onClick={logout} className="btn btn-sm">로그아웃</button>
            </div>
          ) : (
            <button onClick={() => navigate('/')} className="btn btn-primary btn-sm">
              로그인
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
