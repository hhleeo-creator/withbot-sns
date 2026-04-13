import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { notificationAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { formatDistanceToNow } from 'date-fns'
import { ko } from 'date-fns/locale'

export default function NotificationsPage() {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    notificationAPI.list(0, 50)
      .then(res => setNotifications(res.data.notifications))
      .catch(err => console.error('알림 로딩 실패:', err))
      .finally(() => setLoading(false))
  }, [user])

  const handleMarkRead = async (id) => {
    try {
      await notificationAPI.markRead(id)
      setNotifications(prev =>
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      )
    } catch (err) {
      console.error('읽음 처리 실패:', err)
    }
  }

  if (!user) return <div className="empty-state">로그인이 필요합니다.</div>
  if (loading) return <div className="loading">알림 로딩 중...</div>

  return (
    <div className="notifications-page">
      <h2>🔔 알림</h2>

      {notifications.length === 0 ? (
        <div className="empty-state">아직 알림이 없습니다.</div>
      ) : (
        <div className="notification-list">
          {notifications.map(n => (
            <div
              key={n.id}
              className={`notification-item ${n.is_read ? 'read' : 'unread'}`}
              onClick={() => !n.is_read && handleMarkRead(n.id)}
            >
              <div className="notification-content">
                <p>{n.message}</p>
                <span className="notification-time">
                  {n.created_at
                    ? formatDistanceToNow(new Date(n.created_at), { addSuffix: true, locale: ko })
                    : ''}
                </span>
              </div>
              {n.related_post_id && (
                <Link to={`/post/${n.related_post_id}`} className="notification-link">
                  보기
                </Link>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
