import os
import json
import base64
import html as html_lib
from datetime import date
from functools import lru_cache
import re
import inspect
import importlib
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from database import (
    init_db,
    create_user,
    authenticate_user,
    get_user,
    update_password,
    count_free_questions,
    save_message,
    get_history,
    clear_history,
    get_subscription,
    activate_demo_subscription,
    deactivate_subscription,
    list_subjects,
    save_feedback,
    create_conversation,
    list_conversations,
    get_conversation,
    get_conversation_history,
    set_user_avatar,
)

import tutor

# =========================================================
# CONFIGURAÇÃO INICIAL
# =========================================================

load_dotenv()

# Garante que o banco esteja inicializado antes do uso.
init_db()

# Recarrega a versão atual do tutor.py.
importlib.reload(tutor)
answer_question = tutor.answer_question

st.set_page_config(
    page_title="Mente Saber",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SUBJECTS = list_subjects()
FREE_QUESTIONS = 3
PRICE = 35.00

AVATARS = {
    "coruja": {
        "label": "🦉 Olívia — Coruja",
        "emoji": "🦉",
        "persona": (
            "Você é Olívia, uma coruja sábia, curiosa e acolhedora. "
            "Explique com clareza, passo a passo, usando exemplos simples "
            "e mantendo a precisão pedagógica."
        ),
    },
    "borboleta": {
        "label": "🦋 Fifi — Borboleta",
        "emoji": "🦋",
        "persona": (
            "Você é Fifi, uma borboleta gentil, colorida e curiosa. "
            "Use um tom leve e encorajador, sem sacrificar a clareza "
            "nem a correção das explicações."
        ),
    },
    "cachorro": {
        "label": "🐶 Bolt — Cachorro",
        "emoji": "🐶",
        "persona": (
            "Você é Bolt, um cachorro tutor animado, leal e amigável. "
            "Explique com paciência, clareza e exemplos, mantendo "
            "o conteúdo correto."
        ),
    },
    "gato": {
        "label": "🐱 Mimi — Gato",
        "emoji": "🐱",
        "persona": (
            "Você é Mimi, uma gata esperta, tranquila e curiosa. "
            "Use um tom simpático e observador, com explicações "
            "corretas, claras e pacientes."
        ),
    },
}


# =========================================================
# ESTILO VISUAL
# =========================================================

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}

AVATAR_KEYWORDS = {
    "coruja": ("coruja", "olivia", "olívia", "owl"),
    "borboleta": ("borboleta", "butterfly"),
    "cachorro": ("cachorro", "bolt", "dog"),
    "gato": ("gato", "mimi", "cat"),
}

PREFERRED_WORDS = ("avatar", "icone", "ícone", "icon", "rosto", "face", "perfil")


@lru_cache(maxsize=None)
def find_asset(keywords, avoid=()):
    """Procura uma imagem na pasta assets pelo nome do arquivo."""
    if not ASSETS_DIR.exists():
        return None

    matches = []

    for file in ASSETS_DIR.rglob("*"):
        if file.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        stem = file.stem.lower()

        if any(word in stem for word in avoid):
            continue

        if any(word in stem for word in keywords):
            preferred = 0 if any(w in stem for w in PREFERRED_WORDS) else 1
            matches.append((preferred, len(stem), str(file)))

    if not matches:
        return None

    return Path(sorted(matches)[0][2])


@lru_cache(maxsize=None)
def image_data_uri(path_str):
    path = Path(path_str)
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }.get(path.suffix.lower(), "image/png")

    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def avatar_path(avatar_key):
    return find_asset(AVATAR_KEYWORDS.get(avatar_key, (avatar_key,)))


BUTTERFLY_SVG = (
    "<svg class='ms-bf' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg' "
    "role='img' aria-label='Borboleta'>"
    "<g class='ms-bf-wings'>"
    "<path d='M49 46 C30 14 6 20 12 46 C15 60 36 62 49 52Z' fill='#f59e3b' stroke='#7a3b12' stroke-width='2'/>"
    "<path d='M51 46 C70 14 94 20 88 46 C85 60 64 62 51 52Z' fill='#f59e3b' stroke='#7a3b12' stroke-width='2'/>"
    "<path d='M49 56 C34 58 22 72 30 82 C40 88 48 74 49 64Z' fill='#7fb7ff' stroke='#2f5fa8' stroke-width='2'/>"
    "<path d='M51 56 C66 58 78 72 70 82 C60 88 52 74 51 64Z' fill='#7fb7ff' stroke='#2f5fa8' stroke-width='2'/>"
    "<circle cx='24' cy='40' r='5' fill='#fff' opacity='.75'/>"
    "<circle cx='76' cy='40' r='5' fill='#fff' opacity='.75'/>"
    "</g>"
    "<ellipse cx='50' cy='58' rx='4' ry='19' fill='#3b2a52'/>"
    "<circle cx='50' cy='36' r='6' fill='#3b2a52'/>"
    "<path d='M47 32 Q41 22 36 21 M53 32 Q59 22 64 21' fill='none' stroke='#3b2a52' "
    "stroke-width='1.6' stroke-linecap='round'/>"
    "</svg>"
)


def _pet_svg(label, body):
    return (
        "<svg class='ms-pet' viewBox='0 0 100 100' "
        "xmlns='http://www.w3.org/2000/svg' role='img' "
        f"aria-label='{label}'>{body}</svg>"
    )


OWL_SVG = _pet_svg("Coruja", """
<g class='ms-owl-wing-l'><ellipse cx='22' cy='66' rx='8' ry='19' fill='#8a5a2b' stroke='#5e3a1a' stroke-width='2'/></g>
<g class='ms-owl-wing-r'><ellipse cx='78' cy='66' rx='8' ry='19' fill='#8a5a2b' stroke='#5e3a1a' stroke-width='2'/></g>
<ellipse cx='50' cy='60' rx='29' ry='32' fill='#a96f3e' stroke='#5e3a1a' stroke-width='2'/>
<path d='M24 36 L28 12 L42 28Z' fill='#a96f3e' stroke='#5e3a1a' stroke-width='2' stroke-linejoin='round'/>
<path d='M76 36 L72 12 L58 28Z' fill='#a96f3e' stroke='#5e3a1a' stroke-width='2' stroke-linejoin='round'/>
<ellipse cx='50' cy='70' rx='17' ry='21' fill='#f5dfb5'/>
<g class='ms-blink' style='transform-origin:50px 45px'>
<circle cx='37' cy='44' r='12' fill='#fff' stroke='#5e3a1a' stroke-width='2'/>
<circle cx='63' cy='44' r='12' fill='#fff' stroke='#5e3a1a' stroke-width='2'/>
<circle cx='38' cy='45' r='5.5' fill='#26314d'/><circle cx='62' cy='45' r='5.5' fill='#26314d'/>
<circle cx='36' cy='43' r='1.8' fill='#fff'/><circle cx='60' cy='43' r='1.8' fill='#fff'/>
</g>
<path d='M45 53 L55 53 L50 64Z' fill='#f0a83d' stroke='#b36e10' stroke-width='1.5' stroke-linejoin='round'/>
<ellipse cx='41' cy='93' rx='7' ry='3.5' fill='#f0a83d'/><ellipse cx='59' cy='93' rx='7' ry='3.5' fill='#f0a83d'/>
""")

DOG_SVG = _pet_svg("Cachorro", """
<g class='ms-dog-tail'><path d='M72 80 Q93 70 90 50' fill='none' stroke='#b9793a' stroke-width='7' stroke-linecap='round'/></g>
<ellipse cx='50' cy='80' rx='22' ry='17' fill='#e2b273' stroke='#8a5a2b' stroke-width='2'/>
<ellipse cx='40' cy='94' rx='8' ry='3.5' fill='#f7e3c4' stroke='#8a5a2b' stroke-width='1.5'/>
<ellipse cx='60' cy='94' rx='8' ry='3.5' fill='#f7e3c4' stroke='#8a5a2b' stroke-width='1.5'/>
<circle cx='50' cy='44' r='24' fill='#e2b273' stroke='#8a5a2b' stroke-width='2'/>
<g class='ms-dog-ear-l'><path d='M32 26 Q12 30 15 60 Q31 58 35 40Z' fill='#8a5a2b' stroke='#5e3a1a' stroke-width='1.5'/></g>
<g class='ms-dog-ear-r'><path d='M68 26 Q88 30 85 60 Q69 58 65 40Z' fill='#8a5a2b' stroke='#5e3a1a' stroke-width='1.5'/></g>
<ellipse cx='50' cy='55' rx='13' ry='10' fill='#f7e3c4'/>
<g class='ms-blink' style='transform-origin:50px 42px'>
<circle cx='39' cy='42' r='3.6' fill='#26314d'/><circle cx='61' cy='42' r='3.6' fill='#26314d'/>
<circle cx='38' cy='40.8' r='1.1' fill='#fff'/><circle cx='60' cy='40.8' r='1.1' fill='#fff'/>
</g>
<ellipse cx='50' cy='50' rx='5' ry='3.5' fill='#3a2a22'/>
<path d='M50 53 V58 M50 58 Q45 62 41 58 M50 58 Q55 62 59 58' fill='none' stroke='#3a2a22' stroke-width='1.6' stroke-linecap='round'/>
<g class='ms-dog-tongue'><path d='M46 60 Q50 74 54 60Z' fill='#ef7f8f'/></g>
""")

CAT_SVG = _pet_svg("Gato", """
<g class='ms-cat-tail'><path d='M72 84 Q97 84 90 56' fill='none' stroke='#d98a4e' stroke-width='7' stroke-linecap='round'/></g>
<ellipse cx='50' cy='80' rx='20' ry='16' fill='#f0a65e' stroke='#9a5a22' stroke-width='2'/>
<ellipse cx='41' cy='94' rx='7' ry='3.3' fill='#f8e6cf' stroke='#9a5a22' stroke-width='1.5'/>
<ellipse cx='59' cy='94' rx='7' ry='3.3' fill='#f8e6cf' stroke='#9a5a22' stroke-width='1.5'/>
<path d='M30 36 L27 10 L47 26Z' fill='#f0a65e' stroke='#9a5a22' stroke-width='2' stroke-linejoin='round'/>
<g class='ms-cat-ear-r'><path d='M70 36 L73 10 L53 26Z' fill='#f0a65e' stroke='#9a5a22' stroke-width='2' stroke-linejoin='round'/>
<path d='M68 29 L70 18 L60 25Z' fill='#f2a3b4'/></g>
<path d='M32 29 L30 18 L40 25Z' fill='#f2a3b4'/>
<circle cx='50' cy='46' r='22' fill='#f0a65e' stroke='#9a5a22' stroke-width='2'/>
<path d='M44 26 V32 M50 24 V31 M56 26 V32' stroke='#c27a3a' stroke-width='2' stroke-linecap='round'/>
<ellipse cx='50' cy='56' rx='10' ry='7' fill='#f8e6cf'/>
<g class='ms-blink' style='transform-origin:50px 46px'>
<ellipse cx='40' cy='46' rx='4.6' ry='5.6' fill='#8fc66d'/><ellipse cx='60' cy='46' rx='4.6' ry='5.6' fill='#8fc66d'/>
<ellipse cx='40' cy='46' rx='1.6' ry='4.3' fill='#26314d'/><ellipse cx='60' cy='46' rx='1.6' ry='4.3' fill='#26314d'/>
</g>
<path d='M47 53 L53 53 L50 57Z' fill='#d97891'/>
<path d='M50 57 Q46 61 43 58 M50 57 Q54 61 57 58' fill='none' stroke='#7a4a22' stroke-width='1.4' stroke-linecap='round'/>
<path d='M32 55 H17 M32 59 L18 64 M68 55 H83 M68 59 L82 64' stroke='#7a4a22' stroke-width='1.3' stroke-linecap='round'/>
""")

PET_SVGS = {
    "coruja": OWL_SVG,
    "borboleta": BUTTERFLY_SVG,
    "cachorro": DOG_SVG,
    "gato": CAT_SVG,
}


def avatar_html(avatar_key, css_class="ms-avatar"):
    """Avatar animado (SVG). Usa emoji se o avatar não tiver desenho."""
    svg = PET_SVGS.get(avatar_key)

    if svg:
        return f"<span class='{css_class} ms-avatar-emoji'>{svg}</span>"

    emoji = AVATARS.get(avatar_key, {}).get("emoji", "🙂")
    return f"<span class='{css_class} ms-avatar-emoji'>{emoji}</span>"


def chat_avatar(avatar_key):
    """Valor aceito pelo parâmetro avatar de st.chat_message."""
    path = avatar_path(avatar_key)

    if path and path.suffix.lower() != ".svg":
        return str(path)

    return AVATARS.get(avatar_key, {}).get("emoji", "🙂")


APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --ms-primary: #2447C6;
    --ms-primary-2: #3d7be0;
    --ms-sky: #4a9be8;
    --ms-ink: #17233D;
    --ms-muted: #5C6880;
    --ms-line: #E2E8F3;
    --ms-soft: #EAF0FF;
    --ms-green: #2fae7b;
}

html, body, .stApp, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse at 90% 0%, rgba(102,132,255,.16), transparent 38%),
        radial-gradient(ellipse at 0% 100%, rgba(117,190,255,.16), transparent 38%),
        #f3f7fd;
}

header[data-testid="stHeader"] { background: transparent; height: 0; }
div[data-testid="stToolbar"], div[data-testid="stDecoration"],
section[data-testid="stSidebar"], div[data-testid="collapsedControl"],
div[data-testid="stSidebarCollapsedControl"], footer { display: none !important; }

.block-container {
    max-width: 1320px;
    padding: 0.8rem 1.2rem 2rem 1.2rem;
}

h1, h2, h3, p, label, span { color: var(--ms-ink); }

/* ---------- Barra superior ---------- */
.ms-topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(95deg, #1f3f9e 0%, #2d62c8 55%, #3d8be0 100%);
    border-radius: 20px; padding: 12px 22px; margin-bottom: 16px;
    box-shadow: 0 10px 28px rgba(36, 71, 198, .22);
}
.ms-brand { display: flex; align-items: center; gap: 12px; }
.ms-logo {
    width: 46px; height: 46px; border-radius: 14px; display: grid; place-items: center;
    background: rgba(255,255,255,.18); font-size: 1.6rem;
}
.ms-brand-name { color: #fff !important; font-weight: 800; font-size: 1.55rem; letter-spacing: -.03em; line-height: 1.1; }
.ms-brand-name b { color: #bfe3ff !important; }
.ms-brand-tag { color: #dbe9ff !important; font-size: .82rem; }
.ms-user { display: flex; align-items: center; gap: 14px; color: #fff; font-weight: 600; }
.ms-user span { color: #fff !important; }
.ms-user-chip {
    display: flex; align-items: center; gap: 9px; background: rgba(255,255,255,.16);
    padding: 5px 14px 5px 6px; border-radius: 999px;
}
.ms-user-initial {
    width: 32px; height: 32px; border-radius: 50%; background: #fff; display: grid;
    place-items: center; color: var(--ms-primary) !important; font-weight: 800;
}

/* ---------- Cartões (containers com borda) ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.92);
    border: 1px solid var(--ms-line) !important;
    border-radius: 22px !important;
    box-shadow: 0 12px 34px rgba(28, 52, 110, .08);
}
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"] {
    background: transparent; border: none !important; box-shadow: none; border-radius: 0 !important;
}

/* ---------- Botões ---------- */
.stButton > button, .stFormSubmitButton > button {
    border-radius: 12px; min-height: 2.6rem; font-weight: 600;
    border: 1px solid var(--ms-line); background: #fff; color: var(--ms-ink);
    justify-content: flex-start; transition: all .15s ease;
}
.stButton > button:hover { border-color: var(--ms-primary-2); color: var(--ms-primary); transform: translateY(-1px); }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f8cf0, #2f6fe0); color: #fff; border: none;
    box-shadow: 0 8px 18px rgba(47,111,224,.25);
}
.stButton > button[kind="primary"] p { color: #fff !important; }
.stFormSubmitButton > button { justify-content: center; }

/* ---------- Texto auxiliar dos painéis ---------- */
.ms-section-label { font-size: .86rem; font-weight: 700; color: var(--ms-muted) !important; margin: 4px 0 8px; }

/* ---------- Avatares ---------- */
.ms-avatar { width: 46px; height: 46px; border-radius: 50%; object-fit: cover; background: #eaf2ff; border: 2px solid #fff; box-shadow: 0 3px 10px rgba(28,52,110,.15); }
.ms-avatar-emoji { display: inline-grid; place-items: center; font-size: 1.6rem; }
.ms-avatar-lg { width: 62px; height: 62px; }

/* ---------- Cabeçalho do chat ---------- */
.ms-chat-head {
    display: flex; align-items: center; gap: 14px; padding: 14px 18px; border-radius: 18px;
    background: linear-gradient(95deg, #3b82e6, #5eb0f0); margin-bottom: 12px;
}
.ms-chat-head .ms-chat-name { color: #fff !important; font-size: 1.45rem; font-weight: 800; line-height: 1.1; }
.ms-chat-head .ms-chat-sub { color: #e8f3ff !important; font-size: .88rem; }

/* ---------- Modo de interação (pílulas) ---------- */
div[role="radiogroup"][aria-label="Modo de interação"] { gap: 8px; }
div[role="radiogroup"][aria-label="Modo de interação"] label {
    background: #fff; border: 1px solid var(--ms-line); border-radius: 999px;
    padding: 4px 16px; cursor: pointer;
}
div[role="radiogroup"][aria-label="Modo de interação"] label > div:first-child { display: none; }
div[role="radiogroup"][aria-label="Modo de interação"] label:has(input:checked) {
    background: linear-gradient(135deg, #3bb98a, #2fae7b); border-color: transparent;
}
div[role="radiogroup"][aria-label="Modo de interação"] label:has(input:checked) p { color: #fff !important; font-weight: 700; }

/* ---------- Mensagens ---------- */
div[data-testid="stChatMessage"] {
    background: #ffffff; border: 1px solid #e7edf5; border-radius: 18px;
    padding: .7rem 1rem; margin-bottom: .55rem; box-shadow: 0 4px 14px rgba(28,52,110,.05);
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse; background: #dcebff; border-color: #c9defa; margin-left: 18%;
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { margin-right: 12%; }

/* ---------- Campo de mensagem ---------- */
div[data-testid="stChatInput"] { border-radius: 16px; border: 1px solid #cfe0f7; background: #fff; }
div[data-testid="stChatInput"] button { background: linear-gradient(135deg,#4f8cf0,#2f6fe0); color: #fff; border-radius: 12px; }

/* ---------- Painel lateral direito ---------- */
.ms-hero {
    border-radius: 20px; padding: 26px 18px 18px;
    background:
        linear-gradient(180deg, rgba(255,255,255,.78), rgba(255,255,255,.35)),
        linear-gradient(140deg, #cfe0ff, #dff1ff);
    background-size: cover; background-position: center; margin-bottom: 10px;
}
.ms-hero h2 {
    font-family: "Segoe Script", "Brush Script MT", cursive; font-size: 1.9rem; line-height: 1.15;
    color: #1f4fb0 !important; transform: rotate(-4deg); margin: 0 0 16px; text-align: center;
}
.ms-chip {
    display: flex; align-items: center; gap: 10px; background: #fff; border-radius: 14px;
    padding: 10px 12px; margin-bottom: 8px; font-weight: 600; font-size: .88rem;
    box-shadow: 0 6px 16px rgba(28,52,110,.10);
}
.ms-tip { background: #fff8e6; border: 1px solid #fde9b0; border-radius: 16px; padding: 12px 14px; }
.ms-tip b { color: #8a5a00 !important; }
.ms-quote { background: #eaf7f0; border-radius: 16px; padding: 14px; text-align: center; color: #1c6b4c; }
.ms-quote b, .ms-quote span { color: #1c6b4c !important; }
.ms-plan {
    background: linear-gradient(160deg, #2a4fb4, #3a6fd0); border-radius: 18px; padding: 14px;
    color: #fff; margin-top: 10px;
}
.ms-plan b, .ms-plan span, .ms-plan div { color: #fff !important; }
.ms-welcome { font-size: .95rem; }

/* ---------- Borboleta animada ---------- */
.ms-bf { width: 74%; height: 74%; animation: ms-bf-float 2.6s ease-in-out infinite; overflow: visible; }
.ms-bf-wings { transform-origin: 50px 50px; animation: ms-bf-flap .7s ease-in-out infinite alternate; }
@keyframes ms-bf-flap { from { transform: scaleX(1); } to { transform: scaleX(.3); } }
@keyframes ms-bf-float {
    0%, 100% { transform: translateY(0) rotate(-4deg); }
    50% { transform: translateY(-4px) rotate(4deg); }
}
@media (prefers-reduced-motion: reduce) { .ms-bf, .ms-bf-wings { animation: none; } }

/* ---------- Animais animados ---------- */
.ms-pet { width: 78%; height: 78%; overflow: visible; animation: ms-bf-float 2.8s ease-in-out infinite; }
.ms-blink { animation: ms-blink 4.2s infinite; }
@keyframes ms-blink { 0%, 90%, 100% { transform: scaleY(1); } 94% { transform: scaleY(.08); } }

.ms-owl-wing-l { transform-origin: 26px 54px; animation: ms-owl-wl 1.8s ease-in-out infinite alternate; }
.ms-owl-wing-r { transform-origin: 74px 54px; animation: ms-owl-wr 1.8s ease-in-out infinite alternate; }
@keyframes ms-owl-wl { from { transform: rotate(0); } to { transform: rotate(-16deg); } }
@keyframes ms-owl-wr { from { transform: rotate(0); } to { transform: rotate(16deg); } }

.ms-dog-tail { transform-origin: 72px 80px; animation: ms-wag .35s ease-in-out infinite alternate; }
@keyframes ms-wag { from { transform: rotate(-18deg); } to { transform: rotate(22deg); } }
.ms-dog-ear-l { transform-origin: 32px 28px; animation: ms-ear-l 1.6s ease-in-out infinite alternate; }
.ms-dog-ear-r { transform-origin: 68px 28px; animation: ms-ear-r 1.6s ease-in-out infinite alternate; }
@keyframes ms-ear-l { from { transform: rotate(0); } to { transform: rotate(9deg); } }
@keyframes ms-ear-r { from { transform: rotate(0); } to { transform: rotate(-9deg); } }
.ms-dog-tongue { transform-origin: 50px 60px; animation: ms-pant .5s ease-in-out infinite alternate; }
@keyframes ms-pant { from { transform: scaleY(.6); } to { transform: scaleY(1.1); } }

.ms-cat-tail { transform-origin: 72px 84px; animation: ms-swish 1.8s ease-in-out infinite alternate; }
@keyframes ms-swish { from { transform: rotate(-10deg); } to { transform: rotate(16deg); } }
.ms-cat-ear-r { transform-origin: 62px 28px; animation: ms-twitch 5s infinite; }
@keyframes ms-twitch { 0%, 86%, 100% { transform: rotate(0); } 90% { transform: rotate(-10deg); } 94% { transform: rotate(0); } }

@media (prefers-reduced-motion: reduce) {
    .ms-pet, .ms-blink, .ms-owl-wing-l, .ms-owl-wing-r, .ms-dog-tail, .ms-dog-ear-l,
    .ms-dog-ear-r, .ms-dog-tongue, .ms-cat-tail, .ms-cat-ear-r { animation: none; }
}

@media (max-width: 900px) {
    .block-container { padding: .5rem .6rem 2rem .6rem; }
    .ms-topbar { padding: 10px 14px; }
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { margin-left: 4%; }
}
</style>
"""

st.markdown(APP_CSS, unsafe_allow_html=True)
# =========================================================
# AUTENTICAÇÃO E SESSÃO
# =========================================================

def logged_in():
    return bool(st.session_state.get("user_id"))


def go_to_auth(tab="login"):
    """
    Abre a tela de autenticação real do Streamlit.
    tab pode ser 'login' ou 'cadastro'.
    """
    st.session_state["auth_tab"] = tab
    st.query_params["cadastro"] = "1"
    st.rerun()


def logout():
    keys_to_clear = (
        "user_id",
        "username",
        "display_name",
        "selected_subject",
        "active_conversation_id",
        "active_conversation_subject",
        "subject_navigation",
        "avatar_navigation",
        "interaction_mode",
        "voice_enabled",
        "page",
    )

    for key in keys_to_clear:
        st.session_state.pop(key, None)

    st.query_params.clear()
    st.rerun()


def show_auth():
    """Exibe o formulário funcional de login e criação de conta."""

    left, center, right = st.columns([1, 1.15, 1], gap="large")

    with center:
        st.markdown(
            "<div style='text-align:center;font-size:2.7rem;"
            "margin-bottom:-0.5rem'>🧠</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<h1 style='text-align:center;margin-bottom:0.2rem'>"
            "Mente Saber</h1>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<p style='text-align:center;color:#60718a'>"
            "Seu espaço para aprender, perguntar e evoluir.</p>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<p style='text-align:center;color:#60718a;"
            "font-size:0.95rem;margin-bottom:1.5rem'>"
            "Escolha um assunto, converse com um tutor virtual "
            "e aprenda no seu ritmo.</p>",
            unsafe_allow_html=True,
        )

        default_tab = st.session_state.get("auth_tab", "login")
        tabs = st.tabs(["Entrar", "Criar conta"])

        # --------------------- LOGIN ---------------------
        with tabs[0]:
            with st.form("login_form"):
                email = st.text_input(
                    "E-mail",
                    key="login_email",
                )

                password = st.text_input(
                    "Senha",
                    type="password",
                    key="login_password",
                )

                submitted = st.form_submit_button(
                    "Entrar",
                    use_container_width=True,
                )

            if submitted:
                normalized_email = email.strip().lower()

                if not normalized_email or not password:
                    st.error("Informe seu e-mail e sua senha.")
                else:
                    user = authenticate_user(
                        normalized_email,
                        password,
                    )

                    if user:
                        st.session_state["user_id"] = user["id"]
                        st.session_state["username"] = user["email"]
                        st.session_state["display_name"] = user["display_name"]
                        st.session_state["page"] = "chat"

                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error("E-mail ou senha inválidos.")

        # -------------------- CADASTRO --------------------
        with tabs[1]:
            with st.form("signup_form"):
                display_name = st.text_input(
                    "Como podemos chamar você?",
                    key="signup_display_name",
                )

                email = st.text_input(
                    "Seu e-mail",
                    key="signup_email",
                )

                password = st.text_input(
                    "Crie uma senha (mínimo de 8 caracteres)",
                    type="password",
                    key="signup_password",
                )

                confirm = st.text_input(
                    "Confirme a senha",
                    type="password",
                    key="signup_confirm_password",
                )

                submitted = st.form_submit_button(
                    "Criar minha conta grátis",
                    use_container_width=True,
                )

            if submitted:
                normalized_name = display_name.strip()
                normalized_email = email.strip().lower()

                if not normalized_name or not normalized_email:
                    st.error("Preencha seu nome e e-mail.")

                elif len(password) < 8:
                    st.error(
                        "Use uma senha com pelo menos 8 caracteres."
                    )

                elif password != confirm:
                    st.error("As senhas não conferem.")

                else:
                    ok, message = create_user(
                        normalized_name,
                        normalized_email,
                        password,
                    )

                    if ok:
                        user = authenticate_user(
                            normalized_email,
                            password,
                        )

                        if user:
                            st.session_state["user_id"] = user["id"]
                            st.session_state["username"] = user["email"]
                            st.session_state["display_name"] = (
                                user["display_name"]
                            )
                            st.session_state["page"] = "chat"

                            st.success(message)
                            st.query_params.clear()
                            st.rerun()
                        else:
                            st.success(message)
                            st.info(
                                "Conta criada. Entre usando seu e-mail "
                                "e sua senha."
                            )
                    else:
                        st.error(message)

        st.markdown(
            "<p style='text-align:center;color:#7b8798;"
            "font-size:0.78rem;margin-top:1rem'>"
            "Protótipo inicial. Não utilize senhas importantes "
            "ou reutilizadas de outros serviços.</p>",
            unsafe_allow_html=True,
        )


# =========================================================
# HISTÓRICO DE CONVERSAS
# =========================================================

def _conversation_date(value):
    """Converte uma data ISO para DD/MM/AAAA."""
    try:
        from datetime import datetime

        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).strftime("%d/%m/%Y")

    except (TypeError, ValueError):
        return "Data não informada"


def _open_saved_conversation(conversation_id, user_id):
    """Abre uma conversa existente do usuário autenticado."""

    conversation = get_conversation(
        conversation_id,
        user_id,
    )

    if not conversation:
        return

    st.session_state["active_conversation_id"] = conversation["id"]
    st.session_state["active_conversation_subject"] = (
        conversation["subject_slug"]
    )
    st.session_state["selected_subject"] = conversation["subject_slug"]
    st.session_state["subject_navigation"] = conversation["subject_slug"]
    st.session_state["page"] = "chat"


def _conversation_label(conversation, subject_by_slug):
    subject_name = subject_by_slug.get(
        conversation["subject_slug"],
        conversation["subject_slug"],
    )

    title = str(
        conversation.get("title") or "Nova conversa"
    ).strip()

    if len(title) > 42:
        title = title[:39].rstrip() + "..."

    return (
        f"{title} · {subject_name} · "
        f"{_conversation_date(conversation.get('created_at'))}"
    )


# =========================================================
# LEITURA DAS RESPOSTAS EM VOZ ALTA
# =========================================================

def _render_voice_button(
    text,
    key,
    avatar_key="coruja",
    language="pt-BR",
):
    """Reproduz a resposta com voz do navegador e anima o mascote."""

    safe_text = json.dumps(str(text), ensure_ascii=False)
    safe_key = re.sub(r"[^a-zA-Z0-9_-]", "_", str(key))

    # Reutiliza os SVGs originais do Mente Saber.
    svg = PET_SVGS.get(avatar_key, OWL_SVG)

    # Camada simples de boca animada. A animação é visual, não é
    # sincronização fonética/silábica real.
    mouth = """
    <ellipse class="ms-talking-mouth"
        cx="50" cy="66" rx="4" ry="2.4"
        fill="#713b46" stroke="#512b34" stroke-width="0.7"/>
    """
    svg = svg.replace("</svg>", mouth + "</svg>")

    components.html(
        f"""
        <!doctype html>
        <html lang="pt-BR">
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    margin: 0;
                    background: transparent;
                    font-family: Arial, sans-serif;
                }}
                .voice-wrap {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    min-height: 76px;
                }}
                .ms-tutor-avatar {{
                    width: 68px;
                    height: 68px;
                    flex: 0 0 68px;
                    animation: ms-float 2s ease-in-out infinite;
                }}
                .ms-tutor-avatar svg {{
                    width: 100%;
                    height: 100%;
                    overflow: visible;
                }}
                .ms-talking-mouth {{
                    transform-box: fill-box;
                    transform-origin: center;
                    transform: scaleY(.12);
                }}
                .ms-tutor-avatar.speaking .ms-talking-mouth {{
                    animation: ms-mouth .17s ease-in-out infinite alternate;
                }}
                .voice-actions {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                }}
                button {{
                    border: 1px solid #cbd5e1;
                    border-radius: 9px;
                    background: #fff;
                    padding: 8px 11px;
                    cursor: pointer;
                    color: #234;
                    font-weight: 600;
                }}
                #ms-speak {{
                    background: #2563eb;
                    color: white;
                    border-color: #2563eb;
                }}
                button:disabled {{
                    opacity: .55;
                    cursor: not-allowed;
                }}
                #ms-voice-status {{
                    margin-top: 5px;
                    font-size: 12px;
                    color: #3979e8;
                }}
                @keyframes ms-mouth {{
                    from {{ transform: scaleY(.12); }}
                    to {{ transform: scaleY(1.7); }}
                }}
                @keyframes ms-float {{
                    0%, 100% {{ transform: translateY(0); }}
                    50% {{ transform: translateY(-3px); }}
                }}
            </style>
        </head>
        <body>
            <div class="voice-wrap">
                <div class="ms-tutor-avatar" id="ms-avatar">
                    {svg}
                </div>
                <div>
                    <div class="voice-actions">
                        <button id="ms-speak" type="button">🔊 Ouvir resposta</button>
                        <button id="ms-stop" type="button">⏹ Parar</button>
                    </div>
                    <div id="ms-voice-status" role="status" aria-live="polite">
                        Pronto para ouvir
                    </div>
                </div>
            </div>
            <script>
                const message = {safe_text};
                const language = {json.dumps(language)};
                const avatar = document.getElementById("ms-avatar");
                const status = document.getElementById("ms-voice-status");
                const speakButton = document.getElementById("ms-speak");
                const stopButton = document.getElementById("ms-stop");

                function cleanForSpeech(value) {{
                    return value
                        .replace(/```[\\s\\S]*?```/g, " bloco de código ")
                        .replace(/`([^`]+)`/g, "$1")
                        .replace(/\\[([^\\]]+)\\]\\([^)]+\\)/g, "$1")
                        .replace(/[*_#~]/g, "")
                        .replace(/\\s+/g, " ")
                        .trim();
                }}

                speakButton.addEventListener("click", () => {{
                    if (!("speechSynthesis" in window)) {{
                        status.textContent = "Seu navegador não oferece leitura por voz.";
                        return;
                    }}

                    window.speechSynthesis.cancel();

                    const utterance = new SpeechSynthesisUtterance(
                        cleanForSpeech(message)
                    );
                    utterance.lang = language;
                    utterance.rate = language.startsWith("en") ? 0.88 : 0.95;
                    utterance.pitch = 1.04;

                    const voices = window.speechSynthesis.getVoices();
                    const prefix = language.toLowerCase().split("-")[0];
                    const exactVoice = voices.find(v =>
                        v.lang.toLowerCase() === language.toLowerCase()
                    );
                    const fallbackVoice = voices.find(v =>
                        v.lang.toLowerCase().startsWith(prefix)
                    );
                    if (exactVoice || fallbackVoice) {{
                        utterance.voice = exactVoice || fallbackVoice;
                    }}

                    utterance.onstart = () => {{
                        avatar.classList.add("speaking");
                        status.textContent = "🔊 Tutor falando...";
                        speakButton.disabled = true;
                    }};
                    utterance.onend = () => {{
                        avatar.classList.remove("speaking");
                        status.textContent = "Explicação concluída.";
                        speakButton.disabled = false;
                    }};
                    utterance.onerror = (event) => {{
                        avatar.classList.remove("speaking");
                        status.textContent = "Não foi possível reproduzir: " + event.error;
                        speakButton.disabled = false;
                    }};

                    window.speechSynthesis.speak(utterance);
                }});

                stopButton.addEventListener("click", () => {{
                    if ("speechSynthesis" in window) {{
                        window.speechSynthesis.cancel();
                    }}
                    avatar.classList.remove("speaking");
                    speakButton.disabled = false;
                    status.textContent = "Áudio interrompido.";
                }});
            </script>
        </body>
        </html>
        """,
        height=88,
        scrolling=False,
        key=f"voice_{safe_key}",
    )


# =========================================================
# PAINEL ESQUERDO (MENU, TUTORES, PLANO)
# =========================================================

def _set_page(page):
    st.session_state["page"] = page


def _choose_avatar(user_id, avatar_key):
    set_user_avatar(user_id, avatar_key)


def _choose_subject(user_id, slug):
    st.session_state["selected_subject"] = slug
    st.session_state["subject_navigation"] = slug
    st.session_state["active_conversation_id"] = create_conversation(user_id, slug)
    st.session_state["active_conversation_subject"] = slug
    st.session_state["page"] = "chat"


def _on_subject_change(user_id):
    slug = st.session_state.get("subject_navigation")

    if slug and slug != st.session_state.get("selected_subject"):
        _choose_subject(user_id, slug)


def show_topbar(user):
    name = html_lib.escape(str(user.get("display_name") or "Aluno"))
    initial = name[:1].upper() or "A"

    st.markdown(
        f"""
        <div class="ms-topbar">
            <div class="ms-brand">
                <div class="ms-logo">🧠</div>
                <div>
                    <div class="ms-brand-name">Mente <b>Saber</b></div>
                    <div class="ms-brand-tag">Aprender hoje, conquistar amanhã!</div>
                </div>
            </div>
            <div class="ms-user">
                <span>🔔</span>
                <div class="ms-user-chip">
                    <div class="ms-user-initial">{initial}</div>
                    <span>{name}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_left_panel(user):
    page = st.session_state.get("page", "chat")

    nav_items = [
        ("chat", "🏠  Início"),
        ("subjects", "📖  Matérias"),
        ("history", "🕘  Histórico"),
        ("account", "👤  Perfil"),
    ]

    with st.container(border=True):
        for key, label in nav_items:
            st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if page == key else "secondary",
                on_click=_set_page,
                args=(key,),
            )

    current_avatar = user.get("avatar", "cachorro")

    if current_avatar not in AVATARS:
        current_avatar = "cachorro"

    with st.container(border=True):
        st.markdown(
            "<div class='ms-section-label'>Seu tutor</div>",
            unsafe_allow_html=True,
        )

        for key, data in AVATARS.items():
            name, species = [p.strip() for p in data["label"][2:].split("—")]

            try:
                cols = st.columns([1, 3], vertical_alignment="center")
            except TypeError:
                cols = st.columns([1, 3])

            with cols[0]:
                st.markdown(avatar_html(key), unsafe_allow_html=True)

            with cols[1]:
                st.button(
                    f"{name} · {species}",
                    key=f"avatar_pick_{key}",
                    use_container_width=True,
                    type="primary" if key == current_avatar else "secondary",
                    on_click=_choose_avatar,
                    args=(user["id"], key),
                )

    subscription = get_subscription(user["id"])
    used = count_free_questions(user["id"])
    remaining = max(0, FREE_QUESTIONS - used)

    if subscription and subscription["status"] == "active":
        plan_html = (
            "<div class='ms-plan'><b>⭐ Plano ativo</b>"
            "<div style='font-size:.85rem'>Acesso de assinante</div></div>"
        )
    else:
        plural = "pergunta gratuita" if remaining == 1 else "perguntas gratuitas"
        plan_html = (
            "<div class='ms-plan'>"
            f"<div style='font-size:.85rem'>⭐ Você tem</div>"
            f"<b>{remaining} {plural}</b>"
            "<div style='font-size:.85rem'>no teste gratuito!</div></div>"
        )

    st.markdown(plan_html, unsafe_allow_html=True)

    st.button(
        "👑  Ver planos",
        key="nav_plans",
        use_container_width=True,
        on_click=_set_page,
        args=("account",),
    )

    st.markdown(
        "<div class='ms-quote'>🌱<br><b>Você consegue!</b><br>"
        "<span style='font-size:.85rem'>Cada pequeno passo te aproxima "
        "dos seus sonhos!</span></div>",
        unsafe_allow_html=True,
    )

    if st.button("Sair", key="nav_logout", use_container_width=True):
        logout()


# =========================================================
# PAINEL DIREITO (DISCIPLINA, VOZ, DICA)
# =========================================================

DAILY_TIPS = [
    "Ler é viajar sem sair do lugar!",
    "Errar faz parte de aprender. Tente de novo!",
    "Pequenos estudos todos os dias valem mais que uma maratona.",
    "Explicar com suas palavras é a melhor forma de fixar.",
    "Uma boa pergunta já é metade do caminho.",
]


def show_right_panel(user):
    hero_image = find_asset(("fundo", "background", "biblioteca", "banner", "sala"), avoid=AVATAR_KEYWORDS["coruja"])
    hero_style = ""

    if hero_image:
        hero_style = (
            f" style=\"background-image:linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,.1)),"
            f"url('{image_data_uri(str(hero_image))}')\""
        )

    st.markdown(
        f"""
        <div class="ms-hero"{hero_style}>
            <h2>Juntos vamos mais longe!</h2>
            <div class="ms-chip">⭐ Responda perguntas</div>
            <div class="ms-chip">📖 Aprenda divertindo-se</div>
            <div class="ms-chip">📈 Acompanhe seu progresso</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    slugs = [subject["slug"] for subject in SUBJECTS]
    labels = {
        subject["slug"]: f"{subject['emoji']} {subject['name']}"
        for subject in SUBJECTS
    }

    with st.container(border=True):
        st.markdown(
            "<div class='ms-section-label'>Disciplina selecionada</div>",
            unsafe_allow_html=True,
        )

        st.selectbox(
            "Disciplina",
            slugs,
            format_func=lambda slug: labels[slug],
            key="subject_navigation",
            label_visibility="collapsed",
            on_change=_on_subject_change,
            args=(user["id"],),
        )

        st.session_state.setdefault("voice_enabled", False)

        st.checkbox(
            "🔊 Controles de voz",
            key="voice_enabled",
            help="Exibe botões para ouvir as respostas usando a voz do navegador.",
        )

    tip = DAILY_TIPS[date.today().toordinal() % len(DAILY_TIPS)]

    st.markdown(
        f"<div class='ms-tip'>💡 <b>Dica do dia</b><br>{tip}</div>",
        unsafe_allow_html=True,
    )

# =========================================================
# MATÉRIAS E HISTÓRICO
# =========================================================

def show_subjects(user):
    st.markdown("## 📖 Matérias")
    st.caption("Escolha uma disciplina para começar uma nova conversa.")

    cols = st.columns(3)

    for index, subject in enumerate(SUBJECTS):
        with cols[index % 3]:
            with st.container(border=True):
                st.markdown(f"### {subject['emoji']} {subject['name']}")
                st.caption(subject.get("description", ""))

                st.button(
                    "Estudar",
                    key=f"subject_card_{subject['slug']}",
                    use_container_width=True,
                    type="primary",
                    on_click=_choose_subject,
                    args=(user["id"], subject["slug"]),
                )


def show_history(user):
    st.markdown("## 🕘 Histórico de conversas")

    conversations = list_conversations(user["id"], limit=40)

    subject_by_slug = {
        subject["slug"]: subject["name"] for subject in SUBJECTS
    }

    if not conversations:
        st.info("Suas conversas aparecerão aqui.")
        return

    active_id = st.session_state.get("active_conversation_id")

    for conversation in conversations:
        is_active = conversation["id"] == active_id

        st.button(
            ("📍 " if is_active else "💬 ")
            + _conversation_label(conversation, subject_by_slug),
            key=f"open_conversation_{conversation['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            on_click=_open_saved_conversation,
            args=(conversation["id"], user["id"]),
        )
# =========================================================
# MINHA CONTA E PLANO
# =========================================================

def show_account(user):
    st.title("Minha conta")

    st.write(f"**Nome:** {user['display_name']}")
    st.write(f"**E-mail:** {user['email']}")

    avatar_key = user.get("avatar", "cachorro")

    if avatar_key not in AVATARS:
        avatar_key = "cachorro"

    st.write(
        f"**Tutor-avatar escolhido:** {AVATARS[avatar_key]['label']}"
    )

    st.caption("Para trocar o avatar, use a lista Seu tutor no painel à esquerda.")

    subscription = get_subscription(user["id"])

    if subscription and subscription["status"] == "active":
        st.success("Sua conta está marcada como assinante ativa.")

        st.caption(
            "No protótipo, o status pode ser ativado em modo de "
            "demonstração. Ainda não há cobrança real."
        )

        if st.button("Desativar assinatura de demonstração"):
            deactivate_subscription(user["id"])
            st.rerun()

    else:
        st.subheader("Mente Saber Premium")
        st.markdown("### R$ 35,00 por mês")

        st.write(
            "Acesso aos tutores com uso sujeito a uma política de uso "
            "justo, que será definida após os testes."
        )

        st.warning(
            "A cobrança online ainda não está conectada. "
            "Não informe dados de cartão nesta versão."
        )

        if st.button(
            "Experimentar assinatura (modo demonstração)",
            type="primary",
        ):
            activate_demo_subscription(user["id"])
            st.success("Assinatura de demonstração ativada.")
            st.rerun()

    st.divider()

    if st.button("Voltar ao chat", key="account_back"):
        st.session_state["page"] = "chat"
        st.rerun()


# =========================================================
# DISCIPLINA DE INGLÊS
# =========================================================

def is_english_subject(subject):
    """Identifica a disciplina de inglês pelo nome ou identificador."""

    name = str(subject.get("name", "")).casefold()
    slug = str(subject.get("slug", "")).casefold()

    return any(
        term in f"{name} {slug}"
        for term in ("inglês", "ingles", "english")
    )


def show_english_pronunciation():
    """Leitor de pronúncia em inglês usando a voz do navegador."""

    st.subheader("🔊 Ouvir pronúncia")

    st.caption(
        "Digite uma palavra ou frase em inglês e ouça como ela é "
        "pronunciada. Você pode repetir o áudio quantas vezes quiser."
    )

    components.html(
        """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    color: #172b4d;
                    margin: 0;
                }

                input, select, button {
                    box-sizing: border-box;
                    width: 100%;
                    padding: 12px;
                    margin: 5px 0 10px;
                    border: 1px solid #d6e0ed;
                    border-radius: 9px;
                    font-size: 15px;
                }

                button {
                    background: #2563eb;
                    color: white;
                    border: none;
                    font-weight: bold;
                    cursor: pointer;
                }

                button:hover {
                    background: #1d4ed8;
                }

                #status {
                    font-size: 13px;
                    margin-top: 4px;
                }
            </style>
        </head>

        <body>
            <label for="englishText">Palavra ou frase em inglês</label>
            <input
                id="englishText"
                type="text"
                placeholder="Ex.: How are you?"
                autocomplete="off"
            >

            <label for="accent">Pronúncia</label>
            <select id="accent">
                <option value="en-US">Inglês americano</option>
                <option value="en-GB">Inglês britânico</option>
            </select>

            <button id="speakButton" type="button">
                🔊 Ouvir pronúncia
            </button>

            <button id="stopButton" type="button">
                Parar áudio
            </button>

            <div id="status" role="status" aria-live="polite"></div>

            <script>
                const textInput = document.getElementById("englishText");
                const accent = document.getElementById("accent");
                const status = document.getElementById("status");

                document.getElementById("speakButton")
                    .addEventListener("click", function () {
                        const text = textInput.value.trim();

                        if (!text) {
                            status.textContent =
                                "Digite uma palavra ou frase primeiro.";
                            textInput.focus();
                            return;
                        }

                        if (!("speechSynthesis" in window)) {
                            status.textContent =
                                "Seu navegador não oferece síntese de voz.";
                            return;
                        }

                        window.speechSynthesis.cancel();

                        const utterance =
                            new SpeechSynthesisUtterance(text);

                        utterance.lang = accent.value;
                        utterance.rate = 0.85;

                        const voices =
                            window.speechSynthesis.getVoices();

                        const matchingVoice = voices.find(voice =>
                            voice.lang.toLowerCase() ===
                            accent.value.toLowerCase()
                        );

                        if (matchingVoice) {
                            utterance.voice = matchingVoice;
                        }

                        utterance.onstart = function () {
                            status.textContent = "Reproduzindo áudio...";
                        };

                        utterance.onend = function () {
                            status.textContent = "Áudio concluído.";
                        };

                        utterance.onerror = function (event) {
                            status.textContent =
                                "Não foi possível reproduzir o áudio: " +
                                event.error;
                        };

                        window.speechSynthesis.speak(utterance);
                    });

                document.getElementById("stopButton")
                    .addEventListener("click", function () {
                        if ("speechSynthesis" in window) {
                            window.speechSynthesis.cancel();
                        }

                        status.textContent = "Áudio interrompido.";
                    });

                textInput.addEventListener("keydown", function (event) {
                    if (event.key === "Enter") {
                        event.preventDefault();
                        document.getElementById("speakButton").click();
                    }
                });
            </script>
        </body>
        </html>
        """,
        height=300,
        scrolling=False,
    )



# =========================================================
# CHAT PRINCIPAL
# =========================================================

def _chat_box():
    """Área rolável das mensagens (com alternativa para versões antigas)."""
    try:
        return st.container(height=480, border=False)
    except TypeError:
        return st.container()


def show_chat(user):
    subject_slug = st.session_state.get(
        "selected_subject",
        SUBJECTS[0]["slug"],
    )

    subject = next(
        (item for item in SUBJECTS if item["slug"] == subject_slug),
        SUBJECTS[0],
    )

    active_id = st.session_state.get("active_conversation_id")

    active_conversation = (
        get_conversation(active_id, user["id"]) if active_id else None
    )

    if (
        not active_conversation
        or active_conversation["subject_slug"] != subject_slug
        or st.session_state.get("active_conversation_subject") != subject_slug
    ):
        active_id = create_conversation(user["id"], subject_slug)

        st.session_state["active_conversation_id"] = active_id
        st.session_state["active_conversation_subject"] = subject_slug

        active_conversation = get_conversation(active_id, user["id"])

    avatar_key = user.get("avatar", "cachorro")

    if avatar_key not in AVATARS:
        avatar_key = "cachorro"

    tutor_name, tutor_species = [
        p.strip() for p in AVATARS[avatar_key]["label"][2:].split("—")
    ]

    tutor_avatar = chat_avatar(avatar_key)

    mode_labels = {
        "estudar": "📚 Estudar",
        "conversar": "💬 Conversar",
        "brincar": "🎮 Brincar",
    }

    if st.session_state.get("interaction_mode") not in mode_labels:
        st.session_state["interaction_mode"] = "estudar"

    subscription = get_subscription(user["id"])
    is_subscriber = bool(subscription and subscription["status"] == "active")

    used = count_free_questions(user["id"])
    remaining = max(0, FREE_QUESTIONS - used)

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="ms-chat-head">
                {avatar_html(avatar_key, "ms-avatar ms-avatar-lg")}
                <div>
                    <div class="ms-chat-name">{html_lib.escape(tutor_name)}</div>
                    <div class="ms-chat-sub">{html_lib.escape(tutor_species)} · {html_lib.escape(subject['name'])}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.radio(
            "Modo de interação",
            list(mode_labels),
            format_func=lambda value: mode_labels[value],
            key="interaction_mode",
            horizontal=True,
            label_visibility="collapsed",
        )

        interaction_mode = st.session_state["interaction_mode"]

        if is_english_subject(subject):
            with st.expander("🔊 Ouvir pronúncia em inglês"):
                show_english_pronunciation()

        history = get_conversation_history(user["id"], active_id, limit=100)

        welcome = {
            "estudar": f"Olá! Vamos estudar {subject['name']}. Faça sua primeira pergunta!",
            "conversar": "Vamos conversar! Pode falar sobre qualquer assunto.",
            "brincar": "Vamos brincar! Peça um quiz, uma charada, uma adivinhação ou um jogo de palavras.",
        }[interaction_mode]

        box = _chat_box()

        with box:
            if not history:
                with st.chat_message("assistant", avatar=tutor_avatar):
                    st.markdown(welcome)

            for item in history:
                is_assistant = item["role"] == "assistant"

                with st.chat_message(
                    item["role"],
                    avatar=tutor_avatar if is_assistant else "🙂",
                ):
                    st.markdown(item["content"])

                    if is_assistant and st.session_state.get("voice_enabled", False):
                        _render_voice_button(
                            item["content"],
                            f"history_{active_id}_"
                            f"{item.get('id', item.get('created_at', 'message'))}",
                            avatar_key=avatar_key,
                            language="en-US" if is_english_subject(subject) else "pt-BR",
                        )

        if not is_subscriber and remaining <= 0:
            st.warning(
                "Você usou suas três perguntas gratuitas. "
                "A assinatura mensal permitirá continuar estudando."
            )

            st.button(
                "Conhecer o plano de R$ 35/mês",
                type="primary",
                key="chat_see_plan",
                on_click=_set_page,
                args=("account",),
            )

            return

        placeholders = {
            "estudar": f"Pergunte sobre {subject['name'].lower()}...",
            "conversar": "Sobre o que você quer conversar?",
            "brincar": "Peça um quiz, uma charada ou uma brincadeira...",
        }

        prompt = st.chat_input(
            placeholders[interaction_mode],
            key="chat_prompt",
        )

        if not prompt:
            return

        prompt = prompt.strip()

        if not prompt:
            return

        subscription = get_subscription(user["id"])
        is_subscriber = bool(subscription and subscription["status"] == "active")

        if not is_subscriber and count_free_questions(user["id"]) >= FREE_QUESTIONS:
            st.warning("Você usou suas três perguntas gratuitas.")
            return

        save_message(
            user["id"],
            subject_slug,
            "user",
            prompt,
            conversation_id=active_id,
        )

        with box:
            with st.chat_message("user", avatar="🙂"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar=tutor_avatar):
                with st.spinner(f"{tutor_name} está preparando uma resposta..."):
                    parameters = inspect.signature(answer_question).parameters

                    tutor_kwargs = {}

                    if "user_id" in parameters:
                        tutor_kwargs["user_id"] = user["id"]

                    if "user_name" in parameters:
                        tutor_kwargs["user_name"] = user.get(
                            "display_name",
                            st.session_state.get("display_name", ""),
                        )

                    if "avatar" in parameters:
                        tutor_kwargs["avatar"] = avatar_key

                    if "mode" in parameters:
                        tutor_kwargs["mode"] = interaction_mode

                    if "history" in parameters:
                        # Mensagens anteriores (sem a pergunta atual).
                        tutor_kwargs["history"] = history

                    answer, source_mode = answer_question(
                        subject,
                        prompt,
                        **tutor_kwargs,
                    )

                st.markdown(answer)

                if source_mode == "demo":
                    st.caption(
                        "Modo demonstração: configure uma chave de API "
                        "para habilitar respostas reais de IA."
                    )

        save_message(
            user["id"],
            subject_slug,
            "assistant",
            answer,
            conversation_id=active_id,
        )

        st.rerun()
# =========================================================
# PÁGINA PÚBLICA DE DIVULGAÇÃO
# =========================================================

def show_landing():
    """
    Exibe a página pública antes do login.

    O HTML é mantido. O botão abaixo também fornece uma alternativa
    funcional caso os botões internos do HTML ainda não estejam
    conectados à tela real de autenticação.
    """

    base_dir = Path(__file__).resolve().parent
    candidates = sorted(base_dir.glob("Mente*Saber*divulga*.html"))
    landing_path = (
        candidates[0]
        if candidates
        else base_dir / "Mente Saber Página de divulgação.html"
    )

    # Botões "ponte" invisíveis: os botões da própria página de divulgação
    # clicam neles para abrir a tela de login do Streamlit.
    st.markdown(
        """
        <style>
            .st-key-landing_login, .st-key-landing_signup {
                position: absolute; left: -9999px; width: 1px; height: 1px;
                overflow: hidden; opacity: 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.button("landing-go-login", key="landing_login"):
        go_to_auth("login")

    if st.button("landing-go-signup", key="landing_signup"):
        go_to_auth("cadastro")

    if not landing_path.exists():
        st.warning("Não encontrei o arquivo da página de divulgação.")

        st.info(
            "Deixe o arquivo 'Mente Saber Página de divulgação.html' "
            "na mesma pasta do app.py."
        )
        return

    html = landing_path.read_text(encoding="utf-8")

    bridge = """
    <script>
    (function () {
        function goTo(label) {
            try {
                var buttons = window.parent.document.querySelectorAll("button");
                for (var i = 0; i < buttons.length; i++) {
                    if ((buttons[i].textContent || "").trim() === label) {
                        buttons[i].click();
                        return;
                    }
                }
            } catch (err) {}

            try { window.parent.location.search = "?cadastro=1"; } catch (err) {}
        }

        document.addEventListener("click", function (event) {
            var el = event.target.closest("[data-open-login], [data-open-signup]");
            if (!el) return;

            event.preventDefault();
            event.stopImmediatePropagation();

            goTo(
                el.hasAttribute("data-open-login")
                    ? "landing-go-login"
                    : "landing-go-signup"
            );
        }, true);
    })();
    </script>
    """

    if "</body>" in html:
        html = html.replace("</body>", bridge + "</body>", 1)
    else:
        html += bridge

    components.html(html, height=4400, scrolling=True)


# =========================================================
# ROTEAMENTO PRINCIPAL
# =========================================================

def main():
    if not logged_in():
        auth_requested = st.query_params.get("cadastro") == "1"

        if auth_requested:
            if st.button("← Voltar para a página inicial", key="back_to_landing"):
                st.query_params.clear()
                st.session_state.pop("auth_tab", None)
                st.rerun()

            show_auth()

        else:
            show_landing()

        return

    user = get_user(st.session_state["user_id"])

    if not user:
        logout()
        return

    # Mantém o seletor de disciplina sincronizado com a disciplina ativa.
    selected = st.session_state.get("selected_subject", SUBJECTS[0]["slug"])
    st.session_state["selected_subject"] = selected
    st.session_state["subject_navigation"] = selected

    page = st.session_state.get("page", "chat")

    show_topbar(user)

    if page == "chat":
        left, center, right = st.columns([1.05, 2.9, 1.3], gap="medium")
    else:
        left, center = st.columns([1.05, 4.2], gap="medium")
        right = None

    with left:
        show_left_panel(user)

    with center:
        if page == "account":
            show_account(user)
        elif page == "subjects":
            show_subjects(user)
        elif page == "history":
            show_history(user)
        else:
            show_chat(user)

    if right is not None:
        with right:
            show_right_panel(user)


if __name__ == "__main__":
    main()
