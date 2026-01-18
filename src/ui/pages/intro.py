"""
Intro Page - Brand Identity
"""
import streamlit as st


def render():
    """Render the intro/brand identity page."""
    st.markdown("""
    <div style="text-align: center; padding: 50px 0;">
        <h1 style="font-size: 3.5rem; background: linear-gradient(to right, #818CF8, #C084FC); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px;">
            Where Data Analysts are Born.
        </h1>
        <p style="font-size: 1.2rem; margin-bottom: 40px; color: rgba(255,255,255,0.7);">
            "책으로만 배우는 A/B 테스트는 그만. 직접 경험하며 데이터 분석가로 다시 태어나세요."
        </p>
    </div>

    <div style="display: flex; gap: 20px; justify-content: center; margin-bottom: 50px;">
        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; width: 45%; border: 1px solid rgba(255,255,255,0.1);">
            <h3 style="color: #A78BFA; margin-bottom: 15px;">✨ Nova (New)</h3>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                라틴어로 <strong>'새로운'</strong>이라는 뜻이자, 우주를 밝히는 <strong>초신성(Supernova)</strong>을 의미합니다.<br>
                데이터의 홍수 속에서 인사이트를 발견하고 비즈니스를 밝히는 여러분을 상징합니다.
            </p>
        </div>
        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; width: 45%; border: 1px solid rgba(255,255,255,0.1);">
            <h3 style="color: #A78BFA; margin-bottom: 15px;">🏛️ Arium (Place)</h3>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                라틴어 접미사로 <strong>'~을 위한 공간'</strong> 또는 '생태계'를 뜻합니다.<br>
                예비 분석가들이 마음껏 가설을 세우고, 실패하고, 성장할 수 있는 안전한 훈련소입니다.
            </p>
        </div>
    </div>

    <div style="text-align: center;">
        <div style="background: linear-gradient(90deg, #6366F1, #8B5CF6); padding: 15px 30px; border-radius: 50px; display: inline-block; font-weight: bold; font-size: 1.2rem; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);">
            🚀 Mission: "데이터로 비즈니스를 움직이는 초신성(Analyst)을 위한 실전 생태계"
        </div>
    </div>
    """, unsafe_allow_html=True)
