"""랜덤 아바타 생성 유틸리티.

프로필 이미지가 없는 AI를 위해 고유한 기하학적 아바타를 생성한다.
"""
import hashlib
import os
from PIL import Image, ImageDraw
from app.config import settings


# AI 아바타용 파스텔 컬러 팔레트
COLORS = [
    (255, 107, 107),  # 코랄
    (78, 205, 196),   # 민트
    (69, 183, 209),   # 스카이블루
    (150, 111, 214),  # 퍼플
    (247, 183, 49),   # 옐로우
    (255, 154, 139),  # 살몬
    (106, 176, 76),   # 그린
    (255, 138, 101),  # 오렌지
    (149, 175, 192),  # 슬레이트
    (186, 104, 200),  # 라벤더
]


def generate_random_avatar(ai_name: str, size: int = 256) -> str:
    """AI 이름을 시드로 사용하여 고유한 기하학적 아바타를 생성한다.

    Args:
        ai_name: AI 이름 (해시 시드로 사용)
        size: 이미지 크기 (정사각형)

    Returns:
        저장된 이미지 파일 경로
    """
    # 이름으로 해시 생성 → 일관된 색상/패턴
    hash_val = hashlib.md5(ai_name.encode()).hexdigest()
    hash_int = int(hash_val, 16)

    # 배경색과 전경색 선택
    bg_idx = hash_int % len(COLORS)
    fg_idx = (hash_int // len(COLORS)) % len(COLORS)
    if fg_idx == bg_idx:
        fg_idx = (fg_idx + 1) % len(COLORS)

    bg_color = COLORS[bg_idx]
    fg_color = COLORS[fg_idx]

    # 이미지 생성
    img = Image.new("RGB", (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    # 5x5 대칭 패턴 생성 (왼쪽 절반 → 오른쪽 미러링)
    grid = 5
    cell_size = size // grid
    pattern_bits = bin(hash_int)[2:].zfill(15)  # 15비트 = 5x3 패턴

    for row in range(grid):
        for col in range(3):  # 왼쪽 절반 + 중앙
            bit_idx = row * 3 + col
            if bit_idx < len(pattern_bits) and pattern_bits[bit_idx] == "1":
                # 왼쪽
                x1 = col * cell_size
                y1 = row * cell_size
                draw.rectangle([x1, y1, x1 + cell_size, y1 + cell_size], fill=fg_color)
                # 오른쪽 미러
                mirror_col = grid - 1 - col
                mx1 = mirror_col * cell_size
                draw.rectangle([mx1, y1, mx1 + cell_size, y1 + cell_size], fill=fg_color)

    # 이니셜 추가
    initial = ai_name[0].upper() if ai_name else "?"
    # 중앙에 큰 글자
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 3)
    except (OSError, ImportError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initial, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (size - text_w) // 2
    text_y = (size - text_h) // 2 - bbox[1]
    # 반투명 효과를 위해 약간 어두운 색상
    text_color = tuple(max(0, c - 60) for c in fg_color)
    draw.text((text_x, text_y), initial, fill=(255, 255, 255), font=font)

    # 파일 저장
    filename = f"avatar_{hash_val[:12]}.png"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    img.save(filepath, "PNG")

    return filename
