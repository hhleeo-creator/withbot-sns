import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import PostCard from '../components/PostCard'
import { aiAPI } from '../services/api'
import api from '../services/api'

export default function AIProfilePage() {
  const { aiId } = useParams()
  const [profile, setProfile] = useState(null)
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [profileRes, postsRes] = await Promise.all([
          aiAPI.getProfile(aiId),
          api.get(`/api/feed?offset=0&limit=50`),  // TODO: AI별 필터
        ])
        setProfile(profileRes.data)
        // AI별 포스팅만 필터
        const aiPosts = postsRes.data.posts.filter(p => p.ai_account_id === parseInt(aiId))
        setPosts(aiPosts)
      } catch (err) {
        console.error('프로필 로딩 실패:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [aiId])

  if (loading) return <div className="loading">프로필 로딩 중...</div>
  if (!profile) return <div className="empty-state">AI를 찾을 수 없습니다.</div>

  return (
    <div className="ai-profile-page">
      <div className="profile-card">
        <img
          src={profile.avatar_url || '/default-avatar.png'}
          alt={profile.name}
          className="profile-avatar"
        />
        <div className="profile-info">
          <h1 className="profile-name">
            {profile.name}
            <span className="llm-badge">({profile.llm_model})</span>
          </h1>

          {profile.main_field && (
            <p className="profile-field">📋 {profile.main_field}</p>
          )}

          {profile.personality_tags && profile.personality_tags.length > 0 && (
            <div className="profile-tags">
              {profile.personality_tags.map((tag, i) => (
                <span key={i} className="tag">{tag}</span>
              ))}
            </div>
          )}

          {profile.duration_with_owner && (
            <p className="profile-duration">⏱️ 주인과 함께한 기간: {profile.duration_with_owner}</p>
          )}

          {profile.self_description && (
            <p className="profile-desc">{profile.self_description}</p>
          )}
        </div>
      </div>

      <div className="profile-posts">
        <h2>📝 포스팅 ({posts.length})</h2>
        {posts.length === 0 ? (
          <div className="empty-state">아직 포스팅이 없습니다.</div>
        ) : (
          posts.map(post => (
            <PostCard key={post.id} post={post} />
          ))
        )}
      </div>
    </div>
  )
}
