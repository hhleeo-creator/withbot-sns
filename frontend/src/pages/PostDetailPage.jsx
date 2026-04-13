import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import PostCard from '../components/PostCard'
import { postAPI, commentAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { formatDistanceToNow } from 'date-fns'
import { ko } from 'date-fns/locale'

function CommentItem({ comment, postId, onReply, depth = 0 }) {
  const [showReply, setShowReply] = useState(false)
  const [replyContent, setReplyContent] = useState('')

  const handleSubmitReply = async (e) => {
    e.preventDefault()
    if (!replyContent.trim()) return
    await onReply(replyContent, comment.id)
    setReplyContent('')
    setShowReply(false)
  }

  const timeAgo = comment.created_at
    ? formatDistanceToNow(new Date(comment.created_at), { addSuffix: true, locale: ko })
    : ''

  return (
    <div className="comment" style={{ marginLeft: depth * 24 }}>
      <div className="comment-header">
        <img src={comment.author_avatar || '/default-avatar.png'} alt="" className="avatar-sm" />
        <span className="comment-author">
          {comment.author_name}
          {comment.author_type === 'ai' && <span className="ai-badge">AI</span>}
        </span>
        <span className="comment-time">{timeAgo}</span>
      </div>
      <p className="comment-text">{comment.content}</p>
      <button className="reply-btn" onClick={() => setShowReply(!showReply)}>
        답글
      </button>

      {showReply && (
        <form onSubmit={handleSubmitReply} className="reply-form">
          <input
            type="text"
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            placeholder="답글을 입력하세요..."
            className="input input-sm"
          />
          <button type="submit" className="btn btn-sm btn-primary">전송</button>
        </form>
      )}

      {comment.replies?.map(reply => (
        <CommentItem
          key={reply.id}
          comment={reply}
          postId={postId}
          onReply={onReply}
          depth={depth + 1}
        />
      ))}
    </div>
  )
}

export default function PostDetailPage() {
  const { postId } = useParams()
  const { user } = useAuth()
  const [post, setPost] = useState(null)
  const [comments, setComments] = useState([])
  const [newComment, setNewComment] = useState('')
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    try {
      const [postRes, commentsRes] = await Promise.all([
        postAPI.get(postId),
        commentAPI.list(postId),
      ])
      setPost(postRes.data)
      setComments(commentsRes.data.comments)
    } catch (err) {
      console.error('로딩 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [postId])

  const handleComment = async (e) => {
    e.preventDefault()
    if (!newComment.trim()) return
    try {
      await commentAPI.create(postId, { content: newComment })
      setNewComment('')
      loadData()
    } catch (err) {
      alert('댓글 작성 실패: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleReply = async (content, parentId) => {
    try {
      await commentAPI.create(postId, { content, parent_comment_id: parentId })
      loadData()
    } catch (err) {
      alert('답글 작성 실패')
    }
  }

  if (loading) return <div className="loading">로딩 중...</div>
  if (!post) return <div className="empty-state">포스팅을 찾을 수 없습니다.</div>

  return (
    <div className="post-detail-page">
      <PostCard post={post} onUpdate={setPost} />

      <div className="comments-section">
        <h3>💬 댓글 {comments.length}개</h3>

        {user && (
          <form onSubmit={handleComment} className="comment-form">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="댓글을 입력하세요..."
              className="input"
            />
            <button type="submit" className="btn btn-primary">작성</button>
          </form>
        )}

        <div className="comments-list">
          {comments.map(comment => (
            <CommentItem
              key={comment.id}
              comment={comment}
              postId={postId}
              onReply={handleReply}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
