
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import base64
import json

PASTA_PERSONAGENS = (
    Path(__file__).parent
    / "assets"
    / "personagens"
)

PERSONAGENS = {
    "Olívia": {
        "animal": "Coruja",
        "arquivo": "olivia.png",
        "emoji": "🦉"
    },
    "Fifi": {
        "animal": "Borboleta",
        "arquivo": "fifi.png",
        "emoji": "🦋"
    },
    "Bolt": {
        "animal": "Cachorro",
        "arquivo": "bolt.png",
        "emoji": "🐶"
    },
    "Mimi": {
        "animal": "Gato",
        "arquivo": "mimi.png",
        "emoji": "🐱"
    }
}


def inicializar_personagem():
    if "personagem_selecionado" not in st.session_state:
        st.session_state.personagem_selecionado = "Olívia"


def mostrar_seletor_personagem():

    inicializar_personagem()

    st.markdown("### 🧑‍🏫 Seu tutor")

    colunas = st.columns(4)

    for coluna, (nome, dados) in zip(
        colunas, PERSONAGENS.items()
    ):
        with coluna:

            caminho = PASTA_PERSONAGENS / dados["arquivo"]

            if caminho.exists():
                st.image(str(caminho), width=75)
            else:
                st.markdown(
                    f"<h1 style='text-align:center'>"
                    f"{dados['emoji']}</h1>",
                    unsafe_allow_html=True
                )

            selecionado = (
                st.session_state.personagem_selecionado
                == nome
            )

            if st.button(
                f"{nome}\n{dados['animal']}",
                key=f"personagem_{nome}",
                use_container_width=True,
                type="primary" if selecionado else "secondary"
            ):
                st.session_state.personagem_selecionado = nome
                st.rerun()

    return st.session_state.personagem_selecionado


def falar_resposta(texto, idioma="pt-BR"):

    personagem = st.session_state.get(
        "personagem_selecionado", "Olívia"
    )

    dados = PERSONAGENS[personagem]

    caminho = PASTA_PERSONAGENS / dados["arquivo"]

    imagem = ""

    if caminho.exists():
        conteudo = base64.b64encode(
            caminho.read_bytes()
        ).decode("utf-8")

        imagem = f"data:image/png;base64,{conteudo}"

    texto_js = json.dumps(texto, ensure_ascii=False)
    imagem_js = json.dumps(imagem)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            text-align: center;
        }}

        .personagem {{
            width: 115px;
            height: 115px;
            object-fit: contain;
            animation: respirar 2s infinite ease-in-out;
        }}

        .falando {{
            animation: falar 0.35s infinite alternate;
        }}

        @keyframes respirar {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-5px); }}
        }}

        @keyframes falar {{
            from {{ transform: translateY(0) scale(1); }}
            to {{ transform: translateY(-4px) scale(1.06); }}
        }}

        .status {{
            color: #3979e8;
            font-size: 13px;
            font-weight: bold;
        }}
    </style>
    </head>

    <body>

    <img id="avatar" class="personagem" src={imagem_js}
         onerror="this.style.display='none'">

    <div class="status" id="status">
        {personagem} está explicando...
    </div>

    <script>
        const texto = {texto_js};
        const idioma = {json.dumps(idioma)};
        const avatar = document.getElementById("avatar");
        const status = document.getElementById("status");

        function falar() {{

            if (!window.speechSynthesis) {{
                status.innerText =
                    "Seu navegador não oferece suporte à fala.";
                return;
            }}

            window.speechSynthesis.cancel();

            const fala = new SpeechSynthesisUtterance(texto);

            fala.lang = idioma;
            fala.rate = 0.92;
            fala.pitch = 1.05;

            fala.onstart = () => {{
                avatar.classList.add("falando");
                status.innerText = "🔊 Falando...";
            }};

            fala.onend = () => {{
                avatar.classList.remove("falando");
                status.innerText = "Explicação concluída!";
            }};

            fala.onerror = () => {{
                avatar.classList.remove("falando");
                status.innerText = "Não foi possível reproduzir o áudio.";
            }};

            window.speechSynthesis.speak(fala);
        }}

        falar();
    </script>

    </body>
    </html>
    """

    components.html(html, height=155, scrolling=False)
