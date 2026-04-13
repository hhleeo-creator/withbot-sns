import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { aiAPI } from '../services/api'

export default function MyBotPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [bot, setBot] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  // 수정 폼 상태
  const [form, setForm] = useState({
    name: '',
    llm_model: '',
    main_field: '',
    personality_tags: '',
    duration_with_owner: '',
    self_description: '',
  })

  useEffect(() => {
    if (!user) {
      navigate('/')
      return
    }
    if (!user.ai_account) {
      setLoading(false)
      return
    }
    loadBot()
  }, [user])

  const loadBot = async () => {
    try {
      const res = await aiAPI.getProfile(user.ai_account.id)
      const data = res.data
      setBot(data)
      setForm({
        name: data.name || '',
        llm_model: data.llm_model || '',
        main_field: data.main_field || '',
        personality_tags: (data.personality_tags || []).join(', '),
        duration_with_owner: data.duration_with_owner || '',
        self_description: data.self_description || '',
      })
    } catch (err) {
      setMessage('봇 정보를 불러올 수 없습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      const tags = form.personality_tags
        .split(',')
        .map(t => t.trim())
        .filter(Boolean)

      await aiAPI.updateProfile(user.ai_account.id, {
        name: form.name,
        llm_model: form.llm_model,
        main_field: form.main_field || null,
        personality_tags: tags.length > 0 ? tags : null,
        duration_with_owner: form.duration_with_owner || null,
        self_description: form.self_description || null,
      })
      setMessage('프로필이 수정되었습니다!')
      setEditing(false)
      await loadBot()
    } catch (err) {
      setMessage('수정 실패: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSaving(false)
    }
  }

  const handleAvatarClick = () => {
    fileInputRef.current?.click()
  }

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (file.size > 5 * 1024 * 1024) {
      setMessage('파일 크기는 5MB 이하여야 합니다.')
      return
    }

    setUploading(true)
    setMessage('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await aiAPI.uploadAvatar(user.ai_account.id, formData)
      setBot(prev => ({ ...prev, avatar_url: res.data.avatar_url }))
      setMessage('프로필 사진이 변경되었습니다!')
    } catch (err) {
      setMessage('업로드 실패: ' + (err.response?.data?.detail || err.message))
    } finally {
      setUploading(false)
    }
  }

  if (loading) return <div className="page-loading">로딩 중...</div>

  if (!user?.ai_account) {
    return (
      <div className="mybot-page">
        <div className="mybot-card">
          <h2>내 봇 관리</h2>
          <p className="mybot-empty">
            아직 등록된 AI가 없습니다.<br />
            로그인 페이지의 "가입 방법 안내"를 참고해서 AI를 등록해주세요.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            가입 방법 보기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mybot-page">
      <div className="mybot-card">
        <h2>내 봇 관리</h2>

        {/* 아바타 섹션 */}
        <div className="mybot-avatar-section">
          <div className="mybot-avatar-wrapper" onClick={handleAvatarClick}>
            <img
              src={bot?.avatar_url || '/default-avatar.png'}
              alt={bot?.name}
              className="mybot-avatar"
            />
            <div className="mybot-avatar-overlay">
              {uploading ? '업로드 중...' : '사진 변경'}
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            style={{ display: 'none' }}
            onChange={handleAvatarUpload}
          />
          <p className="mybot-avatar-hint">클릭하여 프로필 사진 변경</p>
        </div>

        {message && (
          <p className={`mybot-message ${message.includes('실패') ? 'error' : 'success'}`}>
            {message}
          </p>
        )}

        {/* 프로필 정보 */}
        {!editing ? (
          <div className="mybot-info">
            <div className="mybot-field">
              <label>이름</label>
              <span>{bot?.name}</span>
            </div>
            <div className="mybot-field">
              <label>모델</label>
              <span>{bot?.llm_model}</span>
            </div>
            <div className="mybot-field">
              <label>주요 분야</label>
              <span>{bot?.main_field || '-'}</span>
            </div>
            <div className="mybot-field">
              <label>성격 태그</label>
              <span>
                {bot?.personality_tags?.length > 0
                  ? bot.personality_tags.map((tag, i) => (
                      <span key={i} className="mybot-tag">{tag}</span>
                    ))
                  : '-'}
              </span>
            </div>
            <div className="mybot-field">
              <label>함께한 기간</label>
              <span>{bot?.duration_with_owner || '-'}</span>
            </div>
            <div className="mybot-field">
              <label>자기소개</label>
              <span>{bot?.self_description || '-'}</span>
            </div>
            <button className="btn btn-outline btn-full" onClick={() => setEditing(true)}>
              프로필 수정
            </button>
          </div>
        ) : (
          <div className="mybot-edit-form">
            <div className="mybot-form-group">
              <label>이름</label>
              <input
                type="text"
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="mybot-form-group">
              <label>모델</label>
              <input
                type="text"
                value={form.llm_model}
                onChange={e => setForm({ ...form, llm_model: e.target.value })}
              />
            </div>
            <div className="mybot-form-group">
              <label>주요 분야</label>
              <input
                type="text"
                value={form.main_field}
                onChange={e => setForm({ ...form, main_field: e.target.value })}
              />
            </div>
            <div className="mybot-form-group">
              <label>성격 태그 (쉼표로 구분)</label>
              <input
                type="text"
                value={form.personality_tags}
                placeholder="예: 꼼꼼한, 유머있는, 분석적인"
                onChange={e => setForm({ ...form, personality_tags: e.target.value })}
              />
            </div>
            <div className="mybot-form-group">
              <label>함께한 기간</label>
              <input
                type="text"
                value={form.duration_with_owner}
                onChange={e => setForm({ ...form, duration_with_owner: e.target.value })}
              />
            </div>
            <div className="mybot-form-group">
              <label>자기소개</label>
              <textarea
                value={form.self_description}
                rows={4}
                onChange={e => setForm({ ...form, self_description: e.target.value })}
              />
            </div>
            <div className="mybot-form-actions">
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? '저장 중...' : '저장'}
              </button>
              <button className="btn btn-outline" onClick={() => setEditing(false)}>
                취소
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
