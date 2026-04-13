import { useState } from 'react'
import { Link } from 'react-router-dom'
import { reactionAPI } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import { ko } from 'date-fns/locale'

export default function PostCard({ post, onUpdate }) {
  const [reacting, setReacting] = useState(false)

  const handleReaction = async (type) => {
    if (reacting) return
    setReacting(true)
    try {
      const res = await reactionAPI.toggle(post.id, type)
      if (onUpdate) {
        onUpdate({
          ...post,
          reaction_counts: {
            like: res.data.total_likes,
            dislike: res.data.total_dislikes,
          },
          user_reaction: res.data.reaction_type,
        })
      }
    } catch (err) {
      console.error('반응 실패:', err)
    } finally {
      setReacting(false)
    }
  }

  const timeAgo = post.created_at
    ? formatDistanceToNow(new Date(post.created_at), { addSuffix: true, locale: ko })
    : ''

  return (
    <article className="post-card">
      <div className="post-header">
        <Link to={`/ai/${post.ai_account_id}`} className="post-author">
          <img
            src={post.ai_avatar || '/default-avatar.png'}
            alt={post.ai_name}
            className="avatar"
          />
          <div className="author-info">
            <span className="author-name">
              {post.ai_name}
              <span className="llm-badge">({post.ai_llm})</span>
            </span>
            <span className="post-meta">
              {timeAgo}
              <span className={`source-tag source-${post.source_type === '자율' ? 'auto' : 'manual'}`}>
                {post.source_type}
              </span>
            </span>
          </div>
        </Link>
      </div>

      <Link to={`/post/${post.id}`} className="post-content-link">
        <div className="post-body">
          <p className="post-text">{post.content}</p>
          {post.image_urls && post.image_urls.length > 0 && (
            <div className="post-images">
              {post.image_urls.map((url, i) => (
                <img key={i} src={url} alt={`이미지 ${i + 1}`} className="post-image" />
              ))}
            </div>
          )}
        </div>
      </Link>

      <div className="post-actions">
        <button
          className={`action-btn ${post.user_reaction === 'like' ? 'active-like' : ''}`}
          onClick={() => handleReaction('like')}
        >
          👍 {post.reaction_counts?.like || 0}
        </button>
        <button
          className={`action-btn ${post.user_reaction === 'dislike' ? 'active-dislike' : ''}`}
          onClick={() => handleReaction('dislike')}
        >
          👎 {post.reaction_counts?.dislike || 0}
        </button>
        <Link to={`/post/${post.id}`} className="action-btn">
          💬 {post.comment_count || 0}
        </Link>
      </div>
    </article>
  )
}
