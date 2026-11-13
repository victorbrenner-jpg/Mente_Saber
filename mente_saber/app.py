import os
import json
import base64
import time
import sqlite3
import html as html_lib
from datetime import date, timedelta
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
    set_user_profile_avatar,
)
from database import DB_PATH

import tutor

# =========================================================
# CONFIGURAÇÃO INICIAL E DISCIPLINAS DO ENSINO REGULAR
# =========================================================

load_dotenv()

# Garante que o banco esteja inicializado antes do uso.
init_db()

# Recarrega a versão atual do tutor.py.
importlib.reload(tutor)
answer_question = tutor.answer_question
answer_question_stream = tutor.answer_question_stream

st.set_page_config(
    page_title="Mente Saber",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

REGULAR_EDUCATION_SUBJECTS = [
    {
        "slug": "portugues",
        "name": "Português e Gramática",
        "emoji": "📚",
        "description": "Estude gramática, ortografia, pontuação, concordância, crase, interpretação de texto e redação.",
    },
    {
        "slug": "matematica",
        "name": "Matemática",
        "emoji": "➗",
        "description": "Aprenda conceitos, resolva problemas e veja os cálculos explicados passo a passo.",
    },
    {
        "slug": "ingles",
        "name": "Inglês",
        "emoji": "🌍",
        "description": "Pratique vocabulário, gramática, leitura e conversação.",
    },
    {
        "slug": "ciencias",
        "name": "Ciências",
        "emoji": "🔬",
        "description": "Descubra o corpo humano, seres vivos, meio ambiente, matéria, energia e fenômenos da natureza.",
    },
    {
        "slug": "historia",
        "name": "História",
        "emoji": "🏛️",
        "description": "Explore períodos históricos, acontecimentos e suas relações.",
    },
    {
        "slug": "geografia",
        "name": "Geografia",
        "emoji": "🗺️",
        "description": "Explore mapas, relevo, clima, biomas, população, geopolítica e atualidades do Brasil e do mundo.",
    },
    {
        "slug": "biologia",
        "name": "Biologia",
        "emoji": "🧬",
        "description": "Estude células, genética, ecologia, evolução, botânica, zoologia e fisiologia humana.",
    },
    {
        "slug": "fisica",
        "name": "Física",
        "emoji": "⚛️",
        "description": "Compreenda movimento, forças, energia, eletricidade, ondas, óptica e termodinâmica.",
    },
    {
        "slug": "quimica",
        "name": "Química",
        "emoji": "🧪",
        "description": "Aprenda sobre átomos, tabela periódica, ligações químicas, reações e soluções.",
    },
    {
        "slug": "literatura",
        "name": "Literatura",
        "emoji": "📖",
        "description": "Conheça escolas literárias, obras clássicas, gêneros textuais e figuras de linguagem.",
    },
    {
        "slug": "redacao",
        "name": "Redação",
        "emoji": "✍️",
        "description": "Pratique estrutura textual, dissertação-argumentativa, coesão, coerência e produção de textos.",
    },
    {
        "slug": "espanhol",
        "name": "Espanhol",
        "emoji": "🇪🇸",
        "description": "Pratique vocabulário, leitura, gramática e expressões cotidianas em língua espanhola.",
    },
    {
        "slug": "artes",
        "name": "Artes",
        "emoji": "🎨",
        "description": "Explore artes visuais, música, teatro, dança, história da arte e expressão criativa.",
    },
    {
        "slug": "educacao_fisica",
        "name": "Educação Física",
        "emoji": "⚽",
        "description": "Aprenda sobre esportes, saúde, corpo em movimento, jogos, regras e qualidade de vida.",
    },
    {
        "slug": "filosofia",
        "name": "Filosofia",
        "emoji": "🤔",
        "description": "Reflita sobre ética, lógica, conhecimento, cidadania e os grandes pensadores.",
    },
    {
        "slug": "sociologia",
        "name": "Sociologia",
        "emoji": "👥",
        "description": "Compreenda cultura, sociedade, cidadania, trabalho e transformações sociais.",
    },
    {
        "slug": "ensino_religioso",
        "name": "Ensino Religioso",
        "emoji": "🕊️",
        "description": "Conheça diferentes tradições, valores humanos, respeito cultural e diversidade.",
    },
    {
        "slug": "programacao",
        "name": "Programação e Tecnologia",
        "emoji": "💻",
        "description": "Aprenda lógica, Python, SQL, planilhas e conceitos de tecnologia.",
    },
]


def _load_all_subjects():
    """Garante todas as matérias do ensino regular no banco e na lista ativa."""
    existing = list(list_subjects() or [])
    existing_slugs = {str(s.get("slug", "")).strip() for s in existing}
    existing_names = {str(s.get("name", "")).strip().casefold() for s in existing}

    missing = [
        item
        for item in REGULAR_EDUCATION_SUBJECTS
        if item["slug"] not in existing_slugs
        and item["name"].strip().casefold() not in existing_names
    ]

    if missing:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(subjects)")
                cols_info = cur.fetchall()
                col_names = {row[1] for row in cols_info}

                if {"slug", "name"}.issubset(col_names):
                    for item in missing:
                        insert_cols = ["slug", "name"]
                        insert_vals = [item["slug"], item["name"]]

                        if "emoji" in col_names:
                            insert_cols.append("emoji")
                            insert_vals.append(item["emoji"])
                        if "description" in col_names:
                            insert_cols.append("description")
                            insert_vals.append(item["description"])
                        if "prompt" in col_names:
                            insert_cols.append("prompt")
                            insert_vals.append(
                                f"Ensine {item['name']} de forma clara, didática e adequada ao ensino regular."
                            )
                        if "system_prompt" in col_names:
                            insert_cols.append("system_prompt")
                            insert_vals.append(
                                f"Ensine {item['name']} de forma clara, didática e adequada ao ensino regular."
                            )

                        placeholders = ", ".join("?" for _ in insert_cols)
                        cols_sql = ", ".join(insert_cols)
                        cur.execute(
                            f"INSERT OR IGNORE INTO subjects ({cols_sql}) VALUES ({placeholders})",
                            insert_vals,
                        )
                    conn.commit()
        except Exception:
            pass

    refreshed = list(list_subjects() or [])
    refreshed_slugs = {str(s.get("slug", "")).strip() for s in refreshed}
    refreshed_names = {str(s.get("name", "")).strip().casefold() for s in refreshed}

    for item in REGULAR_EDUCATION_SUBJECTS:
        if (
            item["slug"] not in refreshed_slugs
            and item["name"].strip().casefold() not in refreshed_names
        ):
            refreshed.append(dict(item))

    return refreshed


SUBJECTS = _load_all_subjects()
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


# =========================================================
# CATÁLOGO DE ACESSÓRIOS E SKINS EM SVG PARA OS TUTORES
# =========================================================

TUTOR_ACCESSORIES = [
    {
        "id": "none",
        "name": "Visual Original",
        "emoji": "✨",
        "stars": 0,
        "vip_free": False,
        "desc": "O visual clássico e querido do seu tutor.",
    },
    {
        "id": "oculos_nerd",
        "name": "Óculos de Gênio",
        "emoji": "🤓",
        "stars": 10,
        "vip_free": False,
        "desc": "Lentes brilhantes para resolver qualquer desafio!",
    },
    {
        "id": "coroa_real",
        "name": "Coroa Dourada",
        "emoji": "👑",
        "stars": 20,
        "vip_free": False,
        "desc": "Uma coroa brilhante com joias para quem estuda todo dia.",
    },
    {
        "id": "chapeu_mago",
        "name": "Chapéu de Mago",
        "emoji": "🧙",
        "stars": 30,
        "vip_free": False,
        "desc": "Chapéu estrelado cheio de magia do conhecimento.",
    },
    {
        "id": "fone_gamer",
        "name": "Fone Gamer Neon",
        "emoji": "🎧",
        "stars": 35,
        "vip_free": False,
        "desc": "Estilo super moderno para ouvir explicações e jogar.",
    },
    {
        "id": "super_heroi",
        "name": "Traje Super-Herói",
        "emoji": "🦸",
        "stars": 45,
        "vip_free": False,
        "desc": "Máscara heróica e estrela no peito para salvar o dia!",
    },
    {
        "id": "astronauta",
        "name": "Capacete Espacial",
        "emoji": "🚀",
        "stars": 60,
        "vip_free": True,
        "desc": "Visor espacial de astronauta (grátis para assinantes!).",
    },
]

# Pontos de encaixe proporcionais para cada mascote no viewBox 100x100
_AVATAR_ANCHORS = {
    "coruja": {"head_y": 27, "eye_y": 44, "eye_dx": 13, "eye_r": 12.5, "head_r": 27, "scale": 1.0, "chest_y": 76},
    "borboleta": {"head_y": 30, "eye_y": 36, "eye_dx": 3.2, "eye_r": 3.4, "head_r": 9, "scale": 0.54, "chest_y": 58},
    "cachorro": {"head_y": 20, "eye_y": 42, "eye_dx": 11, "eye_r": 7.5, "head_r": 24, "scale": 0.96, "chest_y": 80},
    "gato": {"head_y": 24, "eye_y": 46, "eye_dx": 10, "eye_r": 7.5, "head_r": 22, "scale": 0.92, "chest_y": 80},
}


def _accessory_svg_layer(avatar_key, accessory_id):
    """Gera a camada SVG compacta (sem quebras de linha) do acessório/skin."""
    if not accessory_id or accessory_id == "none":
        return ""

    a = _AVATAR_ANCHORS.get(avatar_key, _AVATAR_ANCHORS["cachorro"])
    hy = a["head_y"]
    ey = a["eye_y"]
    dx = a["eye_dx"]
    er = a["eye_r"]
    hr = a["head_r"]
    sc = a["scale"]
    cy = a["chest_y"]

    raw = ""

    if accessory_id == "oculos_nerd":
        lx = 50 - dx
        rx = 50 + dx
        bridge_l = lx + er
        bridge_r = rx - er
        raw = (
            f'<g class="ms-acc-layer">'
            f'<circle cx="{lx}" cy="{ey}" r="{er}" fill="rgba(224,242,254,0.28)" stroke="#1e293b" stroke-width="{2.2 * sc:.2f}"/>'
            f'<circle cx="{rx}" cy="{ey}" r="{er}" fill="rgba(224,242,254,0.28)" stroke="#1e293b" stroke-width="{2.2 * sc:.2f}"/>'
            f'<path d="M{bridge_l} {ey} Q50 {ey - 2 * sc:.1f} {bridge_r} {ey}" fill="none" stroke="#1e293b" stroke-width="{2.2 * sc:.2f}"/>'
            f'<line x1="{lx - er}" y1="{ey}" x2="{lx - er - 4 * sc:.1f}" y2="{ey - 2 * sc:.1f}" stroke="#1e293b" stroke-width="{2 * sc:.2f}" stroke-linecap="round"/>'
            f'<line x1="{rx + er}" y1="{ey}" x2="{rx + er + 4 * sc:.1f}" y2="{ey - 2 * sc:.1f}" stroke="#1e293b" stroke-width="{2 * sc:.2f}" stroke-linecap="round"/>'
            f'<line x1="{lx - er * 0.45:.1f}" y1="{ey - er * 0.35:.1f}" x2="{lx - er * 0.1:.1f}" y2="{ey - er * 0.65:.1f}" stroke="#ffffff" stroke-width="{1.5 * sc:.2f}" stroke-linecap="round" opacity="0.85"/>'
            f'<line x1="{rx - er * 0.45:.1f}" y1="{ey - er * 0.35:.1f}" x2="{rx - er * 0.1:.1f}" y2="{ey - er * 0.65:.1f}" stroke="#ffffff" stroke-width="{1.5 * sc:.2f}" stroke-linecap="round" opacity="0.85"/>'
            f'</g>'
        )

    elif accessory_id == "coroa_real":
        w = 26 * sc
        h = 15 * sc
        base_y = hy + 2 * sc
        top_y = base_y - h
        mid_y = base_y - h * 0.55
        raw = (
            f'<g class="ms-acc-layer">'
            f'<path d="M{50 - w / 2:.1f} {base_y:.1f} L{50 - w * 0.55:.1f} {top_y + 2 * sc:.1f} L{50 - w * 0.22:.1f} {mid_y:.1f} L50 {top_y:.1f} L{50 + w * 0.22:.1f} {mid_y:.1f} L{50 + w * 0.55:.1f} {top_y + 2 * sc:.1f} L{50 + w / 2:.1f} {base_y:.1f} Z" '
            f'fill="#fbbf24" stroke="#b45309" stroke-width="{1.6 * sc:.2f}" stroke-linejoin="round"/>'
            f'<rect x="{50 - w / 2:.1f}" y="{base_y - 3.2 * sc:.1f}" width="{w:.1f}" height="{3.4 * sc:.1f}" rx="{1.5 * sc:.1f}" fill="#f59e0b" stroke="#b45309" stroke-width="{1.3 * sc:.2f}"/>'
            f'<circle cx="50" cy="{base_y - 1.6 * sc:.1f}" r="{1.6 * sc:.1f}" fill="#ef4444"/>'
            f'<circle cx="{50 - w * 0.3:.1f}" cy="{base_y - 1.6 * sc:.1f}" r="{1.3 * sc:.1f}" fill="#3b82f6"/>'
            f'<circle cx="{50 + w * 0.3:.1f}" cy="{base_y - 1.6 * sc:.1f}" r="{1.3 * sc:.1f}" fill="#10b981"/>'
            f'</g>'
        )

    elif accessory_id == "chapeu_mago":
        brim_rx = 22 * sc
        brim_ry = 4.5 * sc
        base_y = hy + 2 * sc
        tip_y = max(2.0, base_y - 24 * sc)
        raw = (
            f'<g class="ms-acc-layer">'
            f'<ellipse cx="50" cy="{base_y:.1f}" rx="{brim_rx:.1f}" ry="{brim_ry:.1f}" fill="#312e81" stroke="#1e1b4b" stroke-width="{1.6 * sc:.2f}"/>'
            f'<path d="M{50 - 13 * sc:.1f} {base_y:.1f} Q48 {base_y - 13 * sc:.1f} {50 + 5 * sc:.1f} {tip_y:.1f} Q{50 + 11 * sc:.1f} {base_y - 11 * sc:.1f} {50 + 13 * sc:.1f} {base_y:.1f} Z" '
            f'fill="#4338ca" stroke="#1e1b4b" stroke-width="{1.6 * sc:.2f}" stroke-linejoin="round"/>'
            f'<path d="M{50 - 12.2 * sc:.1f} {base_y - 1.5 * sc:.1f} Q50 {base_y + 1.2 * sc:.1f} {50 + 12.2 * sc:.1f} {base_y - 1.5 * sc:.1f}" '
            f'fill="none" stroke="#fbbf24" stroke-width="{2.6 * sc:.2f}" stroke-linecap="round"/>'
            f'<circle cx="{50 - 2 * sc:.1f}" cy="{base_y - 9 * sc:.1f}" r="{1.6 * sc:.1f}" fill="#fde047"/>'
            f'<circle cx="{50 + 4 * sc:.1f}" cy="{base_y - 14 * sc:.1f}" r="{1.3 * sc:.1f}" fill="#fde047"/>'
            f'<circle cx="{50 - 5 * sc:.1f}" cy="{base_y - 15 * sc:.1f}" r="{1.1 * sc:.1f}" fill="#fef08a"/>'
            f'</g>'
        )

    elif accessory_id == "fone_gamer":
        arc_r = hr + 2 * sc
        ear_w = 6.5 * sc
        ear_h = 13 * sc
        raw = (
            f'<g class="ms-acc-layer">'
            f'<path d="M{50 - arc_r:.1f} {ey:.1f} A{arc_r:.1f} {arc_r:.1f} 0 0 1 {50 + arc_r:.1f} {ey:.1f}" '
            f'fill="none" stroke="#0f172a" stroke-width="{3.4 * sc:.2f}" stroke-linecap="round"/>'
            f'<path d="M{50 - arc_r:.1f} {ey:.1f} A{arc_r:.1f} {arc_r:.1f} 0 0 1 {50 + arc_r:.1f} {ey:.1f}" '
            f'fill="none" stroke="#38bdf8" stroke-width="{1.4 * sc:.2f}" stroke-linecap="round"/>'
            f'<rect x="{50 - arc_r - ear_w * 0.6:.1f}" y="{ey - ear_h / 2:.1f}" width="{ear_w:.1f}" height="{ear_h:.1f}" rx="{3 * sc:.1f}" '
            f'fill="#2563eb" stroke="#0f172a" stroke-width="{1.6 * sc:.2f}"/>'
            f'<rect x="{50 + arc_r - ear_w * 0.4:.1f}" y="{ey - ear_h / 2:.1f}" width="{ear_w:.1f}" height="{ear_h:.1f}" rx="{3 * sc:.1f}" '
            f'fill="#2563eb" stroke="#0f172a" stroke-width="{1.6 * sc:.2f}"/>'
            f'<circle cx="{50 - arc_r - ear_w * 0.1:.1f}" cy="{ey:.1f}" r="{1.8 * sc:.1f}" fill="#38bdf8"/>'
            f'<circle cx="{50 + arc_r + ear_w * 0.1:.1f}" cy="{ey:.1f}" r="{1.8 * sc:.1f}" fill="#38bdf8"/>'
            f'</g>'
        )

    elif accessory_id == "super_heroi":
        mask_w = dx + er * 0.85
        mask_h = er * 0.95
        lx = 50 - dx
        rx = 50 + dx
        hole_r = max(2.2, er * 0.52)
        raw = (
            f'<g class="ms-acc-layer">'
            f'<rect x="{50 - mask_w:.1f}" y="{ey - mask_h / 2:.1f}" width="{mask_w * 2:.1f}" height="{mask_h:.1f}" rx="{mask_h / 2:.1f}" '
            f'fill="#dc2626" stroke="#7f1d1d" stroke-width="{1.4 * sc:.2f}"/>'
            f'<circle cx="{lx}" cy="{ey}" r="{hole_r:.1f}" fill="#ffffff"/>'
            f'<circle cx="{rx}" cy="{ey}" r="{hole_r:.1f}" fill="#ffffff"/>'
            f'<circle cx="{lx + 0.6 * sc:.1f}" cy="{ey + 0.4 * sc:.1f}" r="{hole_r * 0.52:.1f}" fill="#1e293b"/>'
            f'<circle cx="{rx - 0.6 * sc:.1f}" cy="{ey + 0.4 * sc:.1f}" r="{hole_r * 0.52:.1f}" fill="#1e293b"/>'
            f'<polygon points="50,{cy - 6 * sc:.1f} {50 + 2.2 * sc:.1f},{cy - 1.5 * sc:.1f} {50 + 7 * sc:.1f},{cy - 1.5 * sc:.1f} {50 + 3.2 * sc:.1f},{cy + 1.5 * sc:.1f} {50 + 4.6 * sc:.1f},{cy + 6 * sc:.1f} 50,{cy + 3.2 * sc:.1f} {50 - 4.6 * sc:.1f},{cy + 6 * sc:.1f} {50 - 3.2 * sc:.1f},{cy + 1.5 * sc:.1f} {50 - 7 * sc:.1f},{cy - 1.5 * sc:.1f} {50 - 2.2 * sc:.1f},{cy - 1.5 * sc:.1f}" '
            f'fill="#facc15" stroke="#b45309" stroke-width="{1.1 * sc:.2f}"/>'
            f'</g>'
        )

    elif accessory_id == "astronauta":
        dome_cx = 50
        dome_cy = (hy + ey) / 2 + 4 * sc
        dome_r = hr + 6 * sc
        collar_y = dome_cy + dome_r * 0.82
        raw = (
            f'<g class="ms-acc-layer">'
            f'<line x1="50" y1="{max(2.0, dome_cy - dome_r):.1f}" x2="50" y2="{max(1.0, dome_cy - dome_r - 6 * sc):.1f}" '
            f'stroke="#94a3b8" stroke-width="{2 * sc:.2f}" stroke-linecap="round"/>'
            f'<circle cx="50" cy="{max(2.0, dome_cy - dome_r - 6 * sc):.1f}" r="{2.2 * sc:.1f}" fill="#38bdf8"/>'
            f'<circle cx="{dome_cx}" cy="{dome_cy:.1f}" r="{dome_r:.1f}" '
            f'fill="rgba(186,230,253,0.24)" stroke="#38bdf8" stroke-width="{2.4 * sc:.2f}"/>'
            f'<path d="M{dome_cx - dome_r * 0.55:.1f} {dome_cy - dome_r * 0.45:.1f} A{dome_r * 0.72:.1f} {dome_r * 0.72:.1f} 0 0 1 {dome_cx - dome_r * 0.1:.1f} {dome_cy - dome_r * 0.72:.1f}" '
            f'fill="none" stroke="#ffffff" stroke-width="{2.2 * sc:.2f}" stroke-linecap="round" opacity="0.85"/>'
            f'<rect x="{dome_cx - dome_r * 0.72:.1f}" y="{collar_y - 2.5 * sc:.1f}" width="{dome_r * 1.44:.1f}" height="{5 * sc:.1f}" rx="{2.5 * sc:.1f}" '
            f'fill="#f8fafc" stroke="#64748b" stroke-width="{1.5 * sc:.2f}"/>'
            f'</g>'
        )

    return re.sub(r"\s+", " ", raw).strip()


def tutor_svg(avatar_key, accessory_id="none"):
    """Retorna o SVG compacto do tutor vestido com o acessório/skin escolhido."""
    base = re.sub(r"\s+", " ", PET_SVGS.get(avatar_key, OWL_SVG)).strip()
    layer = _accessory_svg_layer(avatar_key, accessory_id)
    if not layer:
        return base
    return base.replace("</svg>", layer + "</svg>")


def avatar_html(avatar_key, css_class="ms-avatar", accessory_id="none"):
    """Avatar animado (SVG) com skin/acessório equipado."""
    if avatar_key in PET_SVGS:
        return f"<span class='{css_class} ms-avatar-emoji'>{tutor_svg(avatar_key, accessory_id)}</span>"

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
.ms-user { display: flex; align-items: center; gap: 10px; color: #fff; font-weight: 600; }
.ms-user span { color: #fff !important; }
.ms-star-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(255, 224, 102, .22); border: 1px solid rgba(255, 230, 128, .45);
    padding: 5px 12px; border-radius: 999px; font-size: .86rem; font-weight: 700;
}
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

/* ---------- Cards padronizados de Matérias ---------- */
.ms-subject-body {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    height: 138px;
    margin-bottom: 10px;
}
.ms-subject-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.15rem;
    font-weight: 800;
    line-height: 1.25;
    color: var(--ms-ink);
    min-height: 46px;
    margin-bottom: 8px;
}
.ms-subject-emoji {
    font-size: 1.55rem;
    line-height: 1;
    flex-shrink: 0;
}
.ms-subject-desc {
    font-size: .85rem;
    line-height: 1.42;
    color: var(--ms-muted) !important;
    height: 76px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
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
.ms-avatar { width: 46px; height: 46px; border-radius: 50%; object-fit: cover; background: #eaf2ff; border: 2px solid #fff; box-shadow: 0 3px 10px rgba(28,52,110,.15); overflow: hidden; flex-shrink: 0; }
.ms-avatar-emoji { display: inline-grid; place-items: center; font-size: 1.6rem; }
.ms-avatar svg { width: 36px; height: 36px; max-width: 100%; max-height: 100%; }
.ms-avatar-lg { width: 62px; height: 62px; }
.ms-avatar-lg svg { width: 48px; height: 48px; }
.ms-avatar-xl { width: 112px; height: 112px; background: radial-gradient(circle at 30% 30%, #ffffff, #dbeafe); border: 3px solid #93c5fd; }
.ms-avatar-xl svg { width: 88px; height: 88px; }

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

/* ---------- Painel lateral direito (Meta, Recompensas e Desconto) ---------- */
.ms-hero {
    border-radius: 20px; padding: 18px 15px 15px;
    background:
        linear-gradient(180deg, rgba(255,255,255,.84), rgba(242,248,255,.68)),
        linear-gradient(140deg, #cfe0ff, #dff1ff);
    background-size: cover; background-position: center; margin-bottom: 10px;
    border: 1px solid #d8e6fb;
}
.ms-hero h2 {
    font-family: "Segoe Script", "Brush Script MT", cursive; font-size: 1.58rem; line-height: 1.15;
    color: #1f4fb0 !important; transform: rotate(-2deg); margin: 0 0 12px; text-align: center;
}
.ms-goal-card {
    background: #fff; border-radius: 14px; padding: 10px 12px; margin-bottom: 8px;
    box-shadow: 0 6px 16px rgba(28,52,110,.08); border: 1px solid #e7effb;
}
.ms-goal-head {
    display: flex; justify-content: space-between; align-items: center;
    font-size: .82rem; font-weight: 700; margin-bottom: 6px;
}
.ms-goal-bar {
    width: 100%; height: 9px; border-radius: 999px; background: #e6eefc; overflow: hidden;
}
.ms-goal-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #3b82e6, #2fae7b);
    transition: width .35s ease;
}
.ms-goal-fill.gold {
    background: linear-gradient(90deg, #f59e0b, #fbbf24);
}
.ms-goal-sub {
    font-size: .76rem; color: var(--ms-muted) !important; margin-top: 5px; line-height: 1.3;
}
.ms-reward-badge {
    display: flex; align-items: center; gap: 8px; background: #ecfdf5;
    border: 1px solid #a7f3d0; border-radius: 12px; padding: 8px 10px;
    font-size: .8rem; font-weight: 600; color: #065f46 !important; margin-bottom: 8px;
}
.ms-reward-badge span { color: #065f46 !important; }
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
.ms-bf { animation: ms-bf-float 2.6s ease-in-out infinite; overflow: visible; }
.ms-bf-wings { transform-origin: 50px 50px; animation: ms-bf-flap .7s ease-in-out infinite alternate; }
@keyframes ms-bf-flap { from { transform: scaleX(1); } to { transform: scaleX(.3); } }
@keyframes ms-bf-float {
    0%, 100% { transform: translateY(0) rotate(-4deg); }
    50% { transform: translateY(-4px) rotate(4deg); }
}
@media (prefers-reduced-motion: reduce) { .ms-bf, .ms-bf-wings { animation: none; } }

/* ---------- Animais animados ---------- */
.ms-pet { overflow: visible; animation: ms-bf-float 2.8s ease-in-out infinite; }
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
# META DE ESTUDOS, RECOMPENSA DIÁRIA, LOJINHA E DESCONTO
# =========================================================

STUDY_PROGRESS_DIR = Path(DB_PATH).parent / "progress"

DAILY_GOAL_OPTIONS = [5, 10, 15, 20]  # minutos por dia
DAILY_REWARD_STARS = 10

DISCOUNT_TIERS = [
    (7, 10),   # 7 dias com meta batida no mês -> 10% de desconto
    (15, 20),  # 15 dias com meta batida no mês -> 20% de desconto
]

TUTOR_DAILY_TREATS = {
    "coruja": ("🪶 Pena Mágica da Sabedoria", "Olívia guardou a pena brilhante na biblioteca!"),
    "borboleta": ("🌸 Flor de Cristal", "Fifi pousou feliz na sua nova flor brilhante!"),
    "cachorro": ("🦴 Ossinho Dourado", "Bolt abanou o rabo de alegria com o ossinho!"),
    "gato": ("🧶 Novelo Estrelado", "Mimi ronronou de felicidade com o novelo!"),
}


def _progress_file(user_id):
    STUDY_PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    return STUDY_PROGRESS_DIR / f"u{int(user_id)}.json"


def _load_study_progress(user_id):
    today_str = date.today().isoformat()
    month_str = date.today().strftime("%Y-%m")
    path = _progress_file(user_id)

    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    if data.get("today_date") != today_str:
        data["today_date"] = today_str
        data["seconds_today"] = 0
        data["claimed_today"] = False

    if data.get("month_key") != month_str:
        data["month_key"] = month_str
        data["month_completed_days"] = 0

    goal = int(data.get("daily_goal_minutes") or 10)
    if goal not in DAILY_GOAL_OPTIONS:
        goal = 10

    unlocked = data.get("unlocked_accessories")
    if not isinstance(unlocked, list):
        unlocked = ["none"]
    if "none" not in unlocked:
        unlocked.insert(0, "none")

    equipped = data.get("equipped_accessories")
    if not isinstance(equipped, dict):
        equipped = {}
    for k in AVATARS:
        if equipped.get(k) not in unlocked:
            equipped[k] = "none"

    data["daily_goal_minutes"] = goal
    data["seconds_today"] = int(data.get("seconds_today") or 0)
    data["claimed_today"] = bool(data.get("claimed_today", False))
    data["total_stars"] = int(data.get("total_stars") or 0)
    data["streak_days"] = int(data.get("streak_days") or 0)
    data["last_claimed_date"] = str(data.get("last_claimed_date") or "")
    data["month_completed_days"] = int(data.get("month_completed_days") or 0)
    data["latest_treat"] = str(data.get("latest_treat") or "")
    data["unlocked_accessories"] = unlocked
    data["equipped_accessories"] = equipped
    return data


def _save_study_progress(user_id, data):
    path = _progress_file(user_id)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _record_study_activity(user_id, min_credit_seconds=0):
    """Atualiza o tempo ativo de estudo do dia sem provocar reruns que cortem o áudio."""
    now = time.time()
    ping_key = f"study_ping_{int(user_id)}"
    last_ping = st.session_state.get(ping_key)
    st.session_state[ping_key] = now

    elapsed = 0
    if last_ping is not None:
        raw_delta = now - float(last_ping)
        if 4 <= raw_delta <= 240:
            elapsed = int(raw_delta)

    credit = max(elapsed, int(min_credit_seconds))
    if credit <= 0:
        return

    data = _load_study_progress(user_id)
    data["seconds_today"] += credit
    _save_study_progress(user_id, data)


def _set_daily_goal(user_id, minutes):
    data = _load_study_progress(user_id)
    data["daily_goal_minutes"] = int(minutes)
    _save_study_progress(user_id, data)


def _claim_daily_reward(user_id, avatar_key):
    data = _load_study_progress(user_id)
    goal_seconds = data["daily_goal_minutes"] * 60

    if data["claimed_today"] or data["seconds_today"] < goal_seconds:
        return False

    today = date.today()
    yesterday_str = (today - timedelta(days=1)).isoformat()

    if data.get("last_claimed_date") == yesterday_str:
        data["streak_days"] += 1
    else:
        data["streak_days"] = 1

    treat_name, treat_note = TUTOR_DAILY_TREATS.get(
        avatar_key,
        ("🏅 Medalha de Dedicação", "Seu tutor ficou muito orguloso!"),
    )

    data["claimed_today"] = True
    data["last_claimed_date"] = today.isoformat()
    data["total_stars"] += DAILY_REWARD_STARS
    data["month_completed_days"] += 1
    data["latest_treat"] = f"{treat_name} — {treat_note}"
    _save_study_progress(user_id, data)
    return True


def _unlock_or_equip_accessory(user_id, avatar_key, item_id, is_subscriber=False):
    """Desbloqueia (trocando estrelas ou pelo plano VIP) e equipa o acessório no tutor."""
    item = next((x for x in TUTOR_ACCESSORIES if x["id"] == item_id), None)
    if not item:
        return False, "Item não encontrado."

    data = _load_study_progress(user_id)
    unlocked = data["unlocked_accessories"]
    already_unlocked = (
        item_id in unlocked
        or item["stars"] == 0
        or (item.get("vip_free") and is_subscriber)
    )

    if not already_unlocked:
        cost = int(item["stars"])
        if data["total_stars"] < cost:
            return False, f"Você precisa de {cost} ⭐ para desbloquear este item."
        data["total_stars"] -= cost
        unlocked.append(item_id)

    elif item_id not in unlocked:
        unlocked.append(item_id)

    data["equipped_accessories"][avatar_key] = item_id
    _save_study_progress(user_id, data)
    return True, f"{item['name']} equipado em {AVATARS[avatar_key]['label']}!"


def _calculate_discount_info(data):
    """Calcula o percentual de desconto conquistado no mês e a próxima meta."""
    days = int(data.get("month_completed_days") or 0)
    current_discount = 0
    next_days = None
    next_discount = None

    for req_days, pct in DISCOUNT_TIERS:
        if days >= req_days:
            current_discount = pct
        elif next_days is None:
            next_days = req_days
            next_discount = pct

    final_price = round(PRICE * (1.0 - current_discount / 100.0), 2)
    return {
        "days": days,
        "discount_pct": current_discount,
        "final_price": final_price,
        "next_days": next_days,
        "next_discount": next_discount,
    }


def _format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
        "autoplay_latest_conv",
        "shop_tutor_select",
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

def _html_component(html, key=None, **kwargs):
    """Compatível com versões do Streamlit que aceitam ou não o parâmetro key."""
    try:
        return components.html(html, key=key, **kwargs)
    except TypeError:
        return components.html(html, **kwargs)


VOICE_PLAYBACK_RATE = {
    "coruja": 1.0,
    "borboleta": 1.0,
    "cachorro": 1.0,
    "gato": 1.0,
}


@st.cache_data(show_spinner=False, max_entries=80, ttl=3600)
def _cached_tutor_audio(text, avatar_key):
    """Gera (e guarda em cache) o áudio do tutor. Falhas levantam erro com diagnóstico real."""
    return tutor.generate_audio_for_avatar(text, avatar_key, raise_on_error=True)


_VOICE_HTML = r"""
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
    body { margin: 0; background: transparent; font-family: Arial, sans-serif; }
    .voice-wrap { display: flex; align-items: center; gap: 10px; min-height: 76px; }
    .ms-tutor-avatar { width: 68px; height: 68px; flex: 0 0 68px;
        animation: ms-float 2s ease-in-out infinite; }
    .ms-tutor-avatar svg { width: 100%; height: 100%; overflow: visible; }
    .ms-talking-mouth { transform-box: fill-box; transform-origin: center; transform: scaleY(.12); }
    .ms-tutor-avatar.speaking { animation: ms-bounce .45s ease-in-out infinite alternate; }
    .ms-tutor-avatar.speaking.css-mouth .ms-talking-mouth {
        animation: ms-mouth .17s ease-in-out infinite alternate; }
    .voice-actions { display: flex; flex-wrap: wrap; gap: 6px; }
    button { border: 1px solid #cbd5e1; border-radius: 9px; background: #fff;
        padding: 8px 11px; cursor: pointer; color: #234; font-weight: 600; }
    #ms-speak { background: #2563eb; color: white; border-color: #2563eb; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    #ms-voice-status { margin-top: 5px; font-size: 12px; color: #3979e8; }
    @keyframes ms-mouth { from { transform: scaleY(.12); } to { transform: scaleY(1.7); } }
    @keyframes ms-float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }
    @keyframes ms-bounce { from { transform: translateY(0) rotate(-3deg); }
                           to { transform: translateY(-6px) rotate(3deg); } }
</style>
</head>
<body>
<div class="voice-wrap">
    <div class="ms-tutor-avatar" id="ms-avatar">__SVG__</div>
    <div>
        <div class="voice-actions">
            <button id="ms-speak" type="button">▶ Ouvir resposta</button>
            <button id="ms-stop" type="button">⏹ Parar</button>
        </div>
        <div id="ms-voice-status" role="status" aria-live="polite">Pronto para ouvir</div>
    </div>
</div>
<script>
    const AUDIO_B64 = __AUDIO__;
    const TUTOR_LABEL = __TUTOR_LABEL__;
    const RATE = __RATE__;
    const AUTOPLAY = __AUTOPLAY__;

    const avatar = document.getElementById("ms-avatar");
    const mouth = avatar.querySelector(".ms-talking-mouth");
    const status = document.getElementById("ms-voice-status");
    const speakButton = document.getElementById("ms-speak");
    const stopButton = document.getElementById("ms-stop");

    let audioEl = null, audioUrl = null, audioCtx = null, analyser = null, raf = null;

    function base64ToWavUrl(b64) {
        const binary = atob(b64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: "audio/wav" });
        return URL.createObjectURL(blob);
    }

    function setSpeaking(on) {
        avatar.classList.toggle("speaking", on);
        speakButton.disabled = on;
        if (!on) {
            cancelAnimationFrame(raf);
            if (mouth) mouth.style.transform = "";
            avatar.classList.remove("css-mouth");
        }
    }

    function animateMouth() {
        if (!analyser || !mouth) { avatar.classList.add("css-mouth"); return; }
        const data = new Uint8Array(analyser.fftSize);
        const loop = () => {
            analyser.getByteTimeDomainData(data);
            let sum = 0;
            for (let i = 0; i < data.length; i++) { const v = (data[i] - 128) / 128; sum += v * v; }
            const level = Math.min(1, Math.sqrt(sum / data.length) * 4);
            mouth.style.transform = "scaleY(" + (0.12 + level * 1.8).toFixed(2) + ")";
            raf = requestAnimationFrame(loop);
        };
        loop();
    }

    function playRecorded() {
        if (!AUDIO_B64) {
            status.textContent = "Áudio exclusivo do tutor indisponível.";
            return;
        }
        if (audioEl) { audioEl.pause(); }
        if (!audioUrl) {
            audioUrl = base64ToWavUrl(AUDIO_B64);
        }
        audioEl = new Audio(audioUrl);
        audioEl.playbackRate = RATE;

        try {
            audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
            const source = audioCtx.createMediaElementSource(audioEl);
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);
            analyser.connect(audioCtx.destination);
            if (audioCtx.state === "suspended") audioCtx.resume();
        } catch (e) { analyser = null; }

        audioEl.onplay = () => {
            setSpeaking(true);
            status.textContent = "🔊 " + TUTOR_LABEL + " falando...";
            animateMouth();
        };
        audioEl.onended = () => { setSpeaking(false); status.textContent = "Explicação concluída!"; };
        audioEl.onerror = () => { setSpeaking(false); status.textContent = "Não foi possível reproduzir o áudio WAV."; };
        audioEl.play().catch(() => {
            setSpeaking(false);
            status.textContent = "Toque em ▶ Ouvir resposta para começar.";
        });
    }

    speakButton.addEventListener("click", playRecorded);
    stopButton.addEventListener("click", () => {
        if (audioEl) { audioEl.pause(); audioEl.currentTime = 0; }
        setSpeaking(false);
        status.textContent = "Áudio interrompido.";
    });

    if (AUTOPLAY) playRecorded();
</script>
</body>
</html>
"""


def _render_voice_button(
    text,
    key,
    avatar_key="coruja",
    accessory_id="none",
    language="pt-BR",
    auto_prepare=False,
    autoplay=False,
):
    """Lê a resposta com a voz exclusiva de cada tutor (Gemini TTS) e anima o mascote vestido."""
    safe_key = re.sub(r"[^a-zA-Z0-9_-]", "_", str(key))
    ready_key = f"voice_ready_{safe_key}"
    tutor_label = AVATARS.get(avatar_key, AVATARS["coruja"])["label"]

    is_ready = auto_prepare or bool(st.session_state.get(ready_key))

    if not is_ready:
        if st.button("🔈 Ouvir novamente", key=f"voice_btn_{safe_key}"):
            st.session_state[ready_key] = True
            st.session_state["voice_autoplay_key"] = safe_key
            st.rerun()
        return

    try:
        with st.spinner(f"Preparando a voz de {tutor_label}..."):
            audio = _cached_tutor_audio(str(text), avatar_key)
        audio_b64 = base64.b64encode(audio).decode("ascii")
    except Exception as err:
        st.error(f"Não foi possível gerar a voz de {tutor_label}: {err}")
        if st.button("🔄 Tentar novamente", key=f"voice_retry_{safe_key}"):
            st.session_state[ready_key] = True
            st.session_state["voice_autoplay_key"] = safe_key
            st.rerun()
        return

    svg = tutor_svg(avatar_key, accessory_id)

    mouth = '<ellipse class="ms-talking-mouth" cx="50" cy="66" rx="4" ry="2.4" fill="#713b46" stroke="#512b34" stroke-width="0.7"/>'
    svg = svg.replace("</svg>", mouth + "</svg>")

    manual_autoplay = st.session_state.get("voice_autoplay_key") == safe_key
    if manual_autoplay:
        st.session_state.pop("voice_autoplay_key", None)

    should_autoplay = bool(autoplay or manual_autoplay)

    html = (
        _VOICE_HTML
        .replace("__SVG__", svg)
        .replace("__AUDIO__", json.dumps(audio_b64))
        .replace("__TUTOR_LABEL__", json.dumps(tutor_label, ensure_ascii=False))
        .replace("__RATE__", str(VOICE_PLAYBACK_RATE.get(avatar_key, 1.0)))
        .replace("__AUTOPLAY__", "true" if should_autoplay else "false")
    )

    _html_component(
        html,
        key=f"voice_{safe_key}_{avatar_key}_{accessory_id}_{'play' if should_autoplay else 'idle'}",
        height=88,
        scrolling=False,
    )


# =========================================================
# AVATAR DO USUÁRIO (emoji ou imagem enviada)
# =========================================================

USER_AVATARS_DIR = Path(DB_PATH).parent / "avatars"

USER_EMOJI_CHOICES = [
    "🙂", "😎", "🤓", "😄", "🥳", "🤩", "😺", "🐼",
    "🦊", "🐯", "🦁", "🐸", "🐧", "🐙", "🦄", "🚀",
    "⭐", "🌈", "⚽", "🎨", "🎮", "📚", "🌻", "🍀",
]


def _user_avatar_file(user):
    value = str(user.get("profile_avatar") or "")

    if value.startswith("image:"):
        path = USER_AVATARS_DIR / Path(value[6:]).name

        if path.exists():
            return path

    return None


def user_chat_avatar(user):
    """Avatar do usuário para st.chat_message."""
    image = _user_avatar_file(user)

    if image:
        return str(image)

    value = str(user.get("profile_avatar") or "")

    if value.startswith("emoji:"):
        return value[6:]

    return "🙂"


def user_avatar_html(user, size=32):
    """Avatar do usuário em HTML (imagem, emoji ou inicial do nome)."""
    image = _user_avatar_file(user)

    if image:
        return (
            f"<img alt='' src='{image_data_uri(str(image))}' "
            f"style='width:{size}px;height:{size}px;border-radius:50%;object-fit:cover'>"
        )

    value = str(user.get("profile_avatar") or "")

    if value.startswith("emoji:"):
        return (
            f"<div class='ms-user-initial' style='width:{size}px;height:{size}px'>"
            f"{html_lib.escape(value[6:])}</div>"
        )

    name = str(user.get("display_name") or "A").strip()
    initial = html_lib.escape((name[:1] or "A").upper())

    return (
        f"<div class='ms-user-initial' style='width:{size}px;height:{size}px'>"
        f"{initial}</div>"
    )


def _save_user_image(user_id, uploaded_file):
    """Recorta em quadrado, redimensiona, deixa redondo e salva em data/avatars."""
    from PIL import Image, ImageDraw, ImageOps

    if uploaded_file.size > 5 * 1024 * 1024:
        raise ValueError("A imagem deve ter até 5 MB.")

    try:
        image = Image.open(uploaded_file)
        image = ImageOps.exif_transpose(image).convert("RGBA")
    except Exception:
        raise ValueError("Não consegui ler essa imagem. Use PNG, JPG ou WEBP.")

    size = 192
    image = ImageOps.fit(image, (size, size), Image.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    image.putalpha(mask)

    USER_AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    name = f"u{int(user_id)}_{int(time.time())}.png"
    image.save(USER_AVATARS_DIR / name, "PNG")

    for old in USER_AVATARS_DIR.glob(f"u{int(user_id)}_*.png"):
        if old.name != name:
            old.unlink(missing_ok=True)

    return name


def _set_profile_avatar(user_id, value):
    set_user_profile_avatar(user_id, value)


def _use_uploaded_avatar(user_id):
    uploaded = st.session_state.get("avatar_upload")

    if uploaded is None:
        return

    try:
        name = _save_user_image(user_id, uploaded)
        set_user_profile_avatar(user_id, f"image:{name}")
        st.session_state["avatar_msg"] = ("ok", "Avatar atualizado!")
    except ValueError as error:
        st.session_state["avatar_msg"] = ("erro", str(error))


def show_user_avatar_editor(user):
    st.subheader("Seu avatar")
    st.caption("Escolha um emoji ou envie uma foto. Ele aparece nas suas mensagens e no topo da página.")

    left, right = st.columns([1, 4])

    with left:
        st.markdown(user_avatar_html(user, 72), unsafe_allow_html=True)

    with right:
        st.markdown("**Escolher um emoji**")

        per_row = 8

        for start in range(0, len(USER_EMOJI_CHOICES), per_row):
            cols = st.columns(per_row)

            for col, emoji in zip(cols, USER_EMOJI_CHOICES[start:start + per_row]):
                with col:
                    st.button(
                        emoji,
                        key=f"user_emoji_{emoji}",
                        use_container_width=True,
                        on_click=_set_profile_avatar,
                        args=(user["id"], f"emoji:{emoji}"),
                    )

    st.markdown("**Ou enviar uma imagem**")

    uploaded = st.file_uploader(
        "Foto ou imagem (PNG, JPG ou WEBP, até 5 MB)",
        type=["png", "jpg", "jpeg", "webp"],
        key="avatar_upload",
        label_visibility="collapsed",
    )

    if uploaded is not None:
        st.image(uploaded, width=96, caption="Prévia (será recortada em círculo)")

        st.button(
            "Usar esta imagem",
            key="avatar_use_upload",
            type="primary",
            on_click=_use_uploaded_avatar,
            args=(user["id"],),
        )

    if st.session_state.get("avatar_msg"):
        kind, text = st.session_state.pop("avatar_msg")
        (st.success if kind == "ok" else st.error)(text)

    if user.get("profile_avatar"):
        st.button(
            "Voltar ao avatar padrão",
            key="avatar_reset",
            on_click=_set_profile_avatar,
            args=(user["id"], ""),
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
    avatar = user_avatar_html(user, 32)
    progress = _load_study_progress(user["id"])
    stars = progress["total_stars"]
    streak = progress["streak_days"]

    st.markdown(
        f'<div class="ms-topbar">'
        f'<div class="ms-brand"><div class="ms-logo">🧠</div>'
        f'<div><div class="ms-brand-name">Mente <b>Saber</b></div>'
        f'<div class="ms-brand-tag">Aprender hoje, conquistar amanhã!</div></div></div>'
        f'<div class="ms-user">'
        f'<div class="ms-star-pill" title="Estrelas conquistadas e dias seguidos">⭐ {stars} &nbsp;·&nbsp; 🔥 {streak}d</div>'
        f'<div class="ms-user-chip">{avatar}<span>{name}</span></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def show_left_panel(user):
    page = st.session_state.get("page", "chat")
    progress = _load_study_progress(user["id"])
    equipped_map = progress["equipped_accessories"]

    nav_items = [
        ("chat", "🏠  Início"),
        ("subjects", "📖  Matérias"),
        ("shop", "🛍️  Lojinha"),
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
            acc_id = equipped_map.get(key, "none")

            try:
                cols = st.columns([1, 3], vertical_alignment="center")
            except TypeError:
                cols = st.columns([1, 3])

            with cols[0]:
                st.markdown(avatar_html(key, accessory_id=acc_id), unsafe_allow_html=True)

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
# PAINEL DIREITO (META DE ESTUDOS, RECOMPENSAS, DESCONTO, DISCIPLINA)
# =========================================================

DAILY_TIPS = [
    "Ler é viajar sem sair do lugar!",
    "Errar faz parte de aprender. Tente de novo!",
    "Pequenos estudos todos os dias valem mais que uma maratona.",
    "Explicar com suas palavras é a melhor forma de fixar.",
    "Uma boa pergunta já é metade do caminho.",
]


def show_right_panel(user):
    hero_image = find_asset(
        ("fundo", "background", "biblioteca", "banner", "sala"),
        avoid=AVATAR_KEYWORDS["coruja"],
    )
    hero_style = ""

    if hero_image:
        hero_style = (
            f" style=\"background-image:linear-gradient(180deg,rgba(255,255,255,.72),rgba(242,248,255,.55)),"
            f"url('{image_data_uri(str(hero_image))}')\""
        )

    avatar_key = user.get("avatar", "cachorro")
    if avatar_key not in AVATARS:
        avatar_key = "cachorro"

    progress = _load_study_progress(user["id"])
    goal_min = progress["daily_goal_minutes"]
    goal_sec = goal_min * 60
    studied_sec = progress["seconds_today"]
    studied_min = min(goal_min, round(studied_sec / 60, 1))
    studied_min_display = int(studied_min) if studied_min == int(studied_min) else studied_min
    daily_pct = min(100, int((studied_sec / max(1, goal_sec)) * 100))
    goal_reached = studied_sec >= goal_sec

    discount_info = _calculate_discount_info(progress)
    month_days = discount_info["days"]
    target_days = discount_info["next_days"] or DISCOUNT_TIERS[-1][0]
    discount_pct_bar = min(100, int((month_days / max(1, target_days)) * 100))

    if discount_info["discount_pct"] > 0:
        discount_status = (
            f"🎉 Você já garantiu <b>{discount_info['discount_pct']}% OFF</b> "
            f"({_format_brl(discount_info['final_price'])}/mês)!"
        )
    else:
        faltam = max(0, 7 - month_days)
        plural_d = "dia" if faltam == 1 else "dias"
        discount_status = f"Faltam <b>{faltam} {plural_d}</b> para ganhar 10% OFF na mensalidade."

    if discount_info["next_days"] and discount_info["discount_pct"] > 0:
        faltam_prox = discount_info["next_days"] - month_days
        discount_status += f" (+{faltam_prox}d para {discount_info['next_discount']}% OFF)"

    daily_sub = (
        "✅ Meta concluída! Pegue sua recompensa abaixo."
        if goal_reached and not progress["claimed_today"]
        else (
            "🌟 Recompensa diária já resgatada hoje!"
            if progress["claimed_today"]
            else "Converse com seu tutor para completar o tempo de hoje."
        )
    )

    st.markdown(
        f'<div class="ms-hero"{hero_style}>'
        f'<h2>Juntos vamos mais longe!</h2>'
        f'<div class="ms-goal-card">'
        f'<div class="ms-goal-head"><span>🎯 Meta de hoje</span><span>{studied_min_display} / {goal_min} min</span></div>'
        f'<div class="ms-goal-bar"><div class="ms-goal-fill" style="width:{daily_pct}%"></div></div>'
        f'<div class="ms-goal-sub">{daily_sub}</div>'
        f'</div>'
        f'<div class="ms-goal-card">'
        f'<div class="ms-goal-head"><span>👑 Desconto na mensalidade</span><span>{month_days} / {target_days} dias</span></div>'
        f'<div class="ms-goal-bar"><div class="ms-goal-fill gold" style="width:{discount_pct_bar}%"></div></div>'
        f'<div class="ms-goal-sub">{discount_status}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Botão de resgate da recompensa diária quando bater a meta
    if goal_reached and not progress["claimed_today"]:
        if st.button(
            f"🎁 Resgatar recompensa de hoje (+{DAILY_REWARD_STARS} ⭐)",
            key="claim_daily_reward_btn",
            type="primary",
            use_container_width=True,
        ):
            if _claim_daily_reward(user["id"], avatar_key):
                st.balloons()
                st.rerun()
    elif progress.get("latest_treat") and progress["claimed_today"]:
        st.markdown(
            f"<div class='ms-reward-badge'><span>{html_lib.escape(progress['latest_treat'])}</span></div>",
            unsafe_allow_html=True,
        )

    # Seletor rápido da meta diária da criança
    with st.container(border=True):
        st.markdown(
            "<div class='ms-section-label'>⏱️ Minha meta diária de estudo</div>",
            unsafe_allow_html=True,
        )
        goal_widget_key = f"daily_goal_select_{user['id']}"
        st.session_state[goal_widget_key] = goal_min

        def _on_goal_change():
            _set_daily_goal(user["id"], st.session_state[goal_widget_key])

        st.selectbox(
            "Meta diária",
            DAILY_GOAL_OPTIONS,
            format_func=lambda m: f"⏱️ {m} minutos por dia (+{DAILY_REWARD_STARS} ⭐)",
            key=goal_widget_key,
            label_visibility="collapsed",
            on_change=_on_goal_change,
        )

    slugs = [subject["slug"] for subject in SUBJECTS]
    labels = {
        subject["slug"]: f"{subject.get('emoji', '📘')} {subject['name']}"
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

        st.session_state.setdefault("voice_enabled", True)

        st.checkbox(
            "🔊 Voz automática do tutor",
            key="voice_enabled",
            help="Quando ativado, o tutor lê cada resposta nova automaticamente com a própria voz.",
        )

    tip = DAILY_TIPS[date.today().toordinal() % len(DAILY_TIPS)]

    st.markdown(
        f"<div class='ms-tip'>💡 <b>Dica do dia</b><br>{tip}</div>",
        unsafe_allow_html=True,
    )


# =========================================================
# LOJINHA DE SKINS E ACESSÓRIOS DOS TUTORES
# =========================================================

def show_shop(user):
    progress = _load_study_progress(user["id"])
    stars = progress["total_stars"]
    unlocked = progress["unlocked_accessories"]
    equipped_map = progress["equipped_accessories"]

    subscription = get_subscription(user["id"])
    is_subscriber = bool(subscription and subscription["status"] == "active")

    st.markdown("## 🛍️ Lojinha de Visuais dos Tutores")
    st.caption(
        f"Você tem **⭐ {stars} estrelas** acumuladas. "
        "Conclua sua meta diária de estudo para ganhar mais estrelas e vestir seus tutores!"
    )

    if st.session_state.get("shop_feedback"):
        kind, msg = st.session_state.pop("shop_feedback")
        (st.success if kind == "ok" else st.warning)(msg)

    default_tutor = user.get("avatar", "cachorro")
    if default_tutor not in AVATARS:
        default_tutor = "cachorro"

    st.session_state.setdefault("shop_tutor_select", default_tutor)

    selected_tutor = st.radio(
        "Escolha o tutor para experimentar:",
        list(AVATARS.keys()),
        format_func=lambda k: AVATARS[k]["label"],
        key="shop_tutor_select",
        horizontal=True,
    )

    current_equipped = equipped_map.get(selected_tutor, "none")

    cols = st.columns(3)
    for idx, item in enumerate(TUTOR_ACCESSORIES):
        item_id = item["id"]
        is_equipped = current_equipped == item_id
        is_unlocked = (
            item_id in unlocked
            or item["stars"] == 0
            or (item.get("vip_free") and is_subscriber)
        )

        with cols[idx % 3]:
            with st.container(border=True):
                preview_html = avatar_html(selected_tutor, "ms-avatar ms-avatar-xl", accessory_id=item_id)
                st.markdown(
                    f'<div style="text-align:center;padding:6px 0 4px">{preview_html}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="text-align:center;font-weight:800;font-size:1.02rem;margin-top:4px">'
                    f'{item["emoji"]} {html_lib.escape(item["name"])}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="text-align:center;font-size:.82rem;color:#5C6880;min-height:36px;margin:4px 0 8px">'
                    f'{html_lib.escape(item["desc"])}</div>',
                    unsafe_allow_html=True,
                )

                if is_equipped:
                    st.button(
                        "✅ Equipado",
                        key=f"shop_btn_{selected_tutor}_{item_id}",
                        use_container_width=True,
                        disabled=True,
                    )
                elif is_unlocked:
                    if st.button(
                        "👕 Equipar",
                        key=f"shop_btn_{selected_tutor}_{item_id}",
                        use_container_width=True,
                        type="primary",
                    ):
                        ok, msg = _unlock_or_equip_accessory(
                            user["id"], selected_tutor, item_id, is_subscriber=is_subscriber
                        )
                        st.session_state["shop_feedback"] = ("ok" if ok else "warn", msg)
                        st.rerun()
                else:
                    cost = item["stars"]
                    can_afford = stars >= cost
                    btn_label = (
                        f"⭐ Desbloquear ({cost} ⭐)"
                        if can_afford
                        else f"🔒 {cost} ⭐ (faltam {cost - stars})"
                    )
                    if st.button(
                        btn_label,
                        key=f"shop_btn_{selected_tutor}_{item_id}",
                        use_container_width=True,
                        type="primary" if can_afford else "secondary",
                        disabled=not can_afford,
                    ):
                        ok, msg = _unlock_or_equip_accessory(
                            user["id"], selected_tutor, item_id, is_subscriber=is_subscriber
                        )
                        if ok:
                            st.balloons()
                        st.session_state["shop_feedback"] = ("ok" if ok else "warn", msg)
                        st.rerun()

    st.divider()
    if st.button("← Voltar ao chat", key="shop_back_to_chat"):
        st.session_state["page"] = "chat"
        st.rerun()


# =========================================================
# MATÉRIAS E HISTÓRICO
# =========================================================

def show_subjects(user):
    st.markdown("## 📖 Matérias")
    st.caption(
        f"Escolha entre as {len(SUBJECTS)} disciplinas do ensino regular e tecnologia "
        "para começar uma nova conversa."
    )

    for start in range(0, len(SUBJECTS), 3):
        cols = st.columns(3)

        for col, subject in zip(cols, SUBJECTS[start:start + 3]):
            with col:
                with st.container(border=True):
                    emoji = html_lib.escape(str(subject.get("emoji", "📘")))
                    name = html_lib.escape(str(subject.get("name", "")))
                    desc = html_lib.escape(str(subject.get("description", "")))

                    st.markdown(
                        f'<div class="ms-subject-body">'
                        f'<div class="ms-subject-title"><span class="ms-subject-emoji">{emoji}</span><span>{name}</span></div>'
                        f'<div class="ms-subject-desc">{desc}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

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

    st.caption("Para trocar o avatar ou vestir acessórios, use Seu tutor e a Lojinha no painel à esquerda.")

    st.divider()
    show_user_avatar_editor(user)

    st.divider()
    progress = _load_study_progress(user["id"])
    discount_info = _calculate_discount_info(progress)

    st.subheader("👑 Recompensa de Dedicação (Desconto na Mensalidade)")
    st.write(
        f"**Estrelas acumuladas:** ⭐ {progress['total_stars']}  |  "
        f"**Sequência atual:** 🔥 {progress['streak_days']} dia(s)  |  "
        f"**Metas batidas neste mês:** 🎯 {discount_info['days']} dia(s)"
    )
    st.info(
        "Regra de incentivo: ao bater a meta diária de estudo por **7 dias no mês**, "
        "a família ganha **10% de desconto** (R$ 31,50/mês). Ao completar **15 dias no mês**, "
        "o desconto sobe para **20%** (R$ 28,00/mês)!"
    )

    subscription = get_subscription(user["id"])

    if subscription and subscription["status"] == "active":
        st.success("Sua conta está marcada como assinante ativa.")

        if discount_info["discount_pct"] > 0:
            st.success(
                f"Desconto ativo pelos estudos da criança: **{discount_info['discount_pct']}% OFF** "
                f"(valor com desconto: **{_format_brl(discount_info['final_price'])}/mês**)."
            )

        st.caption(
            "No protótipo, o status pode ser ativado em modo de "
            "demonstração. Ainda não há cobrança real."
        )

        if st.button("Desativar assinatura de demonstração"):
            deactivate_subscription(user["id"])
            st.rerun()

    else:
        st.subheader("Mente Saber Premium")
        if discount_info["discount_pct"] > 0:
            st.markdown(
                f"### ~~{_format_brl(PRICE)}~~ → **{_format_brl(discount_info['final_price'])} por mês** "
                f"({discount_info['discount_pct']}% OFF conquistado!)"
            )
        else:
            st.markdown(f"### {_format_brl(PRICE)} por mês")

        st.write(
            "Acesso aos tutores e ao Capacete Espacial VIP, com uso sujeito "
            "a uma política de uso justo que será definida após os testes."
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
    # Registra tempo decorrido desde a última interação na sessão
    _record_study_activity(user["id"], min_credit_seconds=0)

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

    progress = _load_study_progress(user["id"])
    equipped_accessory = progress["equipped_accessories"].get(avatar_key, "none")

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

    st.session_state.setdefault("voice_enabled", True)

    subscription = get_subscription(user["id"])
    is_subscriber = bool(subscription and subscription["status"] == "active")

    used = count_free_questions(user["id"])
    remaining = max(0, FREE_QUESTIONS - used)

    with st.container(border=True):
        head_avatar = avatar_html(avatar_key, "ms-avatar ms-avatar-lg", accessory_id=equipped_accessory)
        st.markdown(
            f'<div class="ms-chat-head">{head_avatar}'
            f'<div><div class="ms-chat-name">{html_lib.escape(tutor_name)}</div>'
            f'<div class="ms-chat-sub">{html_lib.escape(tutor_species)} · {html_lib.escape(subject["name"])}</div>'
            f'</div></div>',
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

        voice_enabled = bool(st.session_state.get("voice_enabled", True))
        last_assistant_idx = max(
            (idx for idx, msg in enumerate(history) if msg["role"] == "assistant"),
            default=-1,
        )

        should_autoplay_latest = (
            st.session_state.get("autoplay_latest_conv") == active_id
        )
        if should_autoplay_latest:
            st.session_state.pop("autoplay_latest_conv", None)

        box = _chat_box()

        with box:
            if not history:
                with st.chat_message("assistant", avatar=tutor_avatar):
                    st.markdown(welcome)

            for idx, item in enumerate(history):
                is_assistant = item["role"] == "assistant"
                is_latest_reply = is_assistant and (idx == last_assistant_idx)

                with st.chat_message(
                    item["role"],
                    avatar=tutor_avatar if is_assistant else user_chat_avatar(user),
                ):
                    st.markdown(item["content"])

                    if is_assistant and voice_enabled:
                        _render_voice_button(
                            item["content"],
                            f"history_{active_id}_"
                            f"{item.get('id', item.get('created_at', 'message'))}",
                            avatar_key=avatar_key,
                            accessory_id=equipped_accessory,
                            language="en-US" if is_english_subject(subject) else "pt-BR",
                            auto_prepare=is_latest_reply,
                            autoplay=is_latest_reply and should_autoplay_latest,
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
            with st.chat_message("user", avatar=user_chat_avatar(user)):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar=tutor_avatar):
                thinking = st.empty()
                thinking.markdown(f"_{html_lib.escape(str(tutor_name))} está pensando..._ 💭")

                meta = {}
                stream = answer_question_stream(
                    subject,
                    prompt,
                    user_id=user["id"],
                    user_name=user.get(
                        "display_name",
                        st.session_state.get("display_name", ""),
                    ),
                    avatar=avatar_key,
                    mode=interaction_mode,
                    history=history,
                    meta=meta,
                )

                def _pieces():
                    first = True
                    for piece in stream:
                        if first:
                            thinking.empty()
                            first = False
                        yield piece
                    if first:
                        thinking.empty()

                answer = str(st.write_stream(_pieces()) or "").strip()

                if not answer:
                    answer = "Não consegui formular uma resposta agora. Tente perguntar de outra maneira."
                    st.markdown(answer)

                source_mode = meta.get("source", "ai")

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

                # Cada rodada completa de estudo/leitura/escuta conta ao menos 60s
                _record_study_activity(user["id"], min_credit_seconds=60)

                if voice_enabled and source_mode == "ai":
                    voice_prep = st.empty()
                    voice_prep.caption(f"🎙️ {html_lib.escape(str(tutor_name))} preparando a voz...")
                    try:
                        _cached_tutor_audio(answer, avatar_key)
                        st.session_state["autoplay_latest_conv"] = active_id
                    except Exception:
                        pass
                    finally:
                        voice_prep.empty()

        st.rerun()


# =========================================================
# PÁGINA PÚBLICA DE DIVULGAÇÃO
# =========================================================

def show_landing():
    """
    Exibe a página pública antes do login, com os mesmos tutores
    vetoriais animados do chat (Olívia, Fifi, Bolt e Mimi).
    """

    base_dir = Path(__file__).resolve().parent
    candidates = sorted(base_dir.glob("Mente*Saber*divulga*.html"))
    landing_path = (
        candidates[0]
        if candidates
        else base_dir / "Mente Saber Página de divulgação.html"
    )

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

    tutor_svgs_json = json.dumps(
        {key: tutor_svg(key) for key in PET_SVGS},
        ensure_ascii=False,
    )

    landing_tutor_css = """
    <style id="ms-landing-animated-tutors-css">
        .ms-landing-tutor-badge {
            width: 54px;
            height: 54px;
            border-radius: 50%;
            display: inline-grid;
            place-items: center;
            background: radial-gradient(circle at 30% 30%, #ffffff, #eaf2ff);
            border: 2px solid #ffffff;
            box-shadow: 0 4px 12px rgba(28, 52, 110, 0.14);
            margin: 0 auto 4px;
            overflow: hidden;
            flex-shrink: 0;
        }
        .ms-landing-tutor-badge svg {
            width: 42px;
            height: 42px;
            max-width: 100%;
            max-height: 100%;
        }
        .ms-landing-tutor-badge.ms-inline {
            width: 34px;
            height: 34px;
            margin: 0 6px 0 0;
            vertical-align: middle;
        }
        .ms-landing-tutor-badge.ms-inline svg {
            width: 26px;
            height: 26px;
        }

        /* Animações idênticas às do chat */
        .ms-bf { animation: ms-bf-float 2.6s ease-in-out infinite; overflow: visible; }
        .ms-bf-wings { transform-origin: 50px 50px; animation: ms-bf-flap .7s ease-in-out infinite alternate; }
        @keyframes ms-bf-flap { from { transform: scaleX(1); } to { transform: scaleX(.3); } }
        @keyframes ms-bf-float {
            0%, 100% { transform: translateY(0) rotate(-4deg); }
            50% { transform: translateY(-4px) rotate(4deg); }
        }

        .ms-pet { overflow: visible; animation: ms-bf-float 2.8s ease-in-out infinite; }
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
    </style>
    """

    bridge = f"""
    <script>
    (function () {{
        var TUTOR_SVGS = {tutor_svgs_json};
        var EMOJI_TO_KEY = {{
            "🦉": "coruja",
            "🦋": "borboleta",
            "🐶": "cachorro",
            "🐕": "cachorro",
            "🐱": "gato",
            "🐈": "gato"
        }};

        function goTo(label) {{
            try {{
                var buttons = window.parent.document.querySelectorAll("button");
                for (var i = 0; i < buttons.length; i++) {{
                    if ((buttons[i].textContent || "").trim() === label) {{
                        buttons[i].click();
                        return;
                    }}
                }}
            }} catch (err) {{}}

            try {{ window.parent.location.search = "?cadastro=1"; }} catch (err) {{}}
        }}

        document.addEventListener("click", function (event) {{
            var el = event.target.closest("[data-open-login], [data-open-signup]");
            if (!el) return;

            event.preventDefault();
            event.stopImmediatePropagation();

            goTo(
                el.hasAttribute("data-open-login")
                    ? "landing-go-login"
                    : "landing-go-signup"
            );
        }}, true);

        function detectTutorKey(text) {{
            var s = (text || "").toLowerCase();
            if (s.indexOf("coruja") !== -1 || s.indexOf("olívia") !== -1 || s.indexOf("olivia") !== -1 || s.indexOf("owl") !== -1) return "coruja";
            if (s.indexOf("borboleta") !== -1 || s.indexOf("fifi") !== -1 || s.indexOf("butterfly") !== -1) return "borboleta";
            if (s.indexOf("cachorro") !== -1 || s.indexOf("bolt") !== -1 || s.indexOf("dog") !== -1) return "cachorro";
            if (s.indexOf("gato") !== -1 || s.indexOf("mimi") !== -1 || s.indexOf("cat") !== -1) return "gato";
            return null;
        }}

        function svgDataUri(key) {{
            var raw = TUTOR_SVGS[key] || "";
            return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(raw);
        }}

        function makeBadge(key, inline) {{
            var span = document.createElement("span");
            span.className = "ms-landing-tutor-badge" + (inline ? " ms-inline" : "");
            span.setAttribute("data-ms-tutor-rendered", key);
            span.innerHTML = TUTOR_SVGS[key] || "";
            return span;
        }}

        function enhanceLandingTutors() {{
            try {{
                if (!document.body) return;

                var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
                var nodes = [];
                var n;
                while ((n = walker.nextNode())) {{
                    var parent = n.parentElement;
                    if (!parent) continue;
                    var tag = parent.tagName;
                    if (tag === "SCRIPT" || tag === "STYLE" || tag === "TEXTAREA" || tag === "INPUT") continue;
                    if (parent.closest("[data-ms-tutor-rendered]")) continue;
                    if (/[🦉🦋🐶🐕🐱🐈]/.test(n.nodeValue || "")) {{
                        nodes.push(n);
                    }}
                }}

                nodes.forEach(function (textNode) {{
                    if (!textNode.parentNode) return;
                    var val = textNode.nodeValue || "";
                    var trimmed = val.trim();
                    if (EMOJI_TO_KEY[trimmed]) {{
                        textNode.parentNode.replaceChild(makeBadge(EMOJI_TO_KEY[trimmed], false), textNode);
                        return;
                    }}

                    var frag = document.createDocumentFragment();
                    var parts = val.split(/(🦉|🦋|🐶|🐕|🐱|🐈)/g);
                    parts.forEach(function (part) {{
                        if (EMOJI_TO_KEY[part]) {{
                            frag.appendChild(makeBadge(EMOJI_TO_KEY[part], true));
                        }} else if (part) {{
                            frag.appendChild(document.createTextNode(part));
                        }}
                    }});
                    textNode.parentNode.replaceChild(frag, textNode);
                }});

                var imgs = document.querySelectorAll("img");
                for (var j = 0; j < imgs.length; j++) {{
                    var img = imgs[j];
                    var hint = (img.getAttribute("alt") || "") + " " + (img.getAttribute("src") || "") + " " + (img.id || "") + " " + (img.className || "");
                    var imgKey = detectTutorKey(hint);
                    if (imgKey) {{
                        img.src = svgDataUri(imgKey);
                        img.style.borderRadius = "50%";
                        img.style.background = "radial-gradient(circle at 30% 30%, #ffffff, #dbeafe)";
                        img.style.padding = "6px";
                    }}
                }}
            }} catch (e) {{}}
        }}

        if (document.readyState === "loading") {{
            document.addEventListener("DOMContentLoaded", enhanceLandingTutors);
        }} else {{
            enhanceLandingTutors();
        }}

        document.addEventListener("click", function (event) {{
            if (event.target.closest("button, [role='button'], [data-tutor]")) {{
                setTimeout(enhanceLandingTutors, 30);
            }}
        }}, true);
    }})();
    </script>
    """

    if "</head>" in html:
        html = html.replace("</head>", landing_tutor_css + "</head>", 1)
    else:
        html = landing_tutor_css + html

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
        elif page == "shop":
            show_shop(user)
        elif page == "history":
            show_history(user)
        else:
            show_chat(user)

    if right is not None:
        with right:
            show_right_panel(user)


if __name__ == "__main__":
    main()
