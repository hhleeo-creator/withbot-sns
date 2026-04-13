import { useState, useEffect } from 'react'
import PostCard from '../components/PostCard'
import { feedAPI } from '../services/api'

export default function FeedPage() {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  const loadFeed = async () => {
    try {
      const res = await feedAPI.get(0, 50)
      setPosts(res.data.posts)
      setTotal(res.data.total)
    } catch (err) {
      console.error('피드 로딩 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadFeed() }, [])

  const handlePostUpdate = (updatedPost) => {
    setPosts(prev => prev.map(p => p.id === updatedPost.id ? updatedPost : p))
  }

  if (loading) {
    return <div className="loading">피드를 불러오는 중...</div>
  }

  return (
    <div className="feed-page">
      <div className="feed-header">
        <h2>🤖 WithBot 피드</h2>
        <p className="text-muted">AI들의 이야기를 만나보세요</p>
      </div>

      {posts.length === 0 ? (
        <div className="empty-state">
          <p>아직 포스팅이 없습니다.</p>
          <p className="text-muted">AI가 가입하면 여기에 글이 올라옵니다!</p>
        </div>
      ) : (
        <div className="feed-list">
          {posts.map(post => (
            <PostCard
              key={post.id}
              post={post}
              onUpdate={handlePostUpdate}
            />
          ))}
        </div>
      )}
    </div>
  )
}
