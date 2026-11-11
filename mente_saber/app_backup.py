import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from database import (
    init_db, create_user, authenticate_user, get_user, update_password,
    count_free_questions, save_message, get_history, clear_history,
    get_subscription, activate_demo_subscription, deactivate_subscription,
    list_subjects, save_feedback, create_conversation, list_conversations,
    get_conversation, get_conversation_history
)
from tutor import answer_question

load_dotenv()
init_db()

# Layout mais contido e moderno, sem alterar a lógica do aplicativo.
st.set_page_config(page_title="Mente Saber", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    /* Área principal: evita conteúdo esticado em monitores largos */
    .block-container {
        max-width: 1120px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Fundo e tipografia */
    .stApp {
        background: #f5f8fc;
    }
    h1, h2, h3, p, label {
        color: #172b4d;
    }

    /* Campos com aparência mais suave */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        border-radius: 10px;
    }
    div[data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid #e4eaf2;
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 8px 28px rgba(30, 55, 90, 0.06);
    }

    /* Botões */
    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 10px;
        min-height: 2.7rem;
        font-weight: 600;
    }

    /* Cartões das mensagens do chat */
    div[data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #e7edf5;
        border-radius: 14px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background: #eef4fb;
        border-right: 1px solid #e2eaf4;
    }

    /* No celular, usar toda a largura disponível */
    @media (max-width: 700px) {
        .block-container {
            padding: 1rem 0.8rem 2rem 0.8rem;
        }
        div[data-testid="stForm"] {
            padding: 0.85rem;
        }
    }
</style>
""", unsafe_allow_html=True)

SUBJECTS = list_subjects()
FREE_QUESTIONS = 3
PRICE = 35.00


def logged_in():
    return bool(st.session_state.get("user_id"))


def logout():
    for key in (
        "user_id", "username", "display_name", "selected_subject",
        "active_conversation_id", "active_conversation_subject",
        "subject_navigation",
    ):
        st.session_state.pop(key, None)
    st.rerun()


def show_auth():
    # Colunas laterais vazias mantêm login/cadastro no centro da página.
    left, center, right = st.columns([1, 1.15, 1], gap="large")
    with center:
        st.markdown(
            "<div style='text-align:center; font-size:2.7rem; margin-bottom:-0.5rem'>🧠</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h1 style='text-align:center; margin-bottom:0.2rem'>Mente Saber</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#60718a; margin-bottom:0.4rem'>"
            "Seu espaço para aprender, perguntar e evoluir.</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#60718a; font-size:0.95rem; "
            "margin-bottom:1.5rem'>Escolha um assunto, converse com um tutor virtual "
            "e aprenda no seu ritmo.</p>",
            unsafe_allow_html=True,
        )

        login_tab, signup_tab = st.tabs(["Entrar", "Criar conta"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("E-mail", key="login_email")
                password = st.text_input(
                    "Senha", type="password", key="login_password"
                )
                submitted = st.form_submit_button(
                    "Entrar", use_container_width=True
                )
            if submitted:
                user = authenticate_user(email.strip().lower(), password)
                if user:
                    st.session_state.user_id = user["id"]
                    st.session_state.username = user["email"]
                    st.session_state.display_name = user["display_name"]
                    st.rerun()
                else:
                    st.error("E-mail ou senha inválidos.")

        with signup_tab:
            with st.form("signup_form"):
                display_name = st.text_input("Como podemos chamar você?")
                email = st.text_input("Seu e-mail", key="signup_email")
                password = st.text_input(
                    "Crie uma senha (mínimo de 8 caracteres)",
                    type="password",
                    key="signup_password",
                )
                confirm = st.text_input("Confirme a senha", type="password")
                submitted = st.form_submit_button(
                    "Criar minha conta grátis", use_container_width=True
                )
            if submitted:
                if not display_name.strip() or not email.strip():
                    st.error("Preencha seu nome e e-mail.")
                elif len(password) < 8:
                    st.error("Use uma senha com pelo menos 8 caracteres.")
                elif password != confirm:
                    st.error("As senhas não conferem.")
                else:
                    ok, message = create_user(
                        display_name.strip(), email.strip().lower(), password
                    )
                    if ok:
                        user = authenticate_user(
                            email.strip().lower(), password
                        )
                        st.session_state.user_id = user["id"]
                        st.session_state.username = user["email"]
                        st.session_state.display_name = user["display_name"]
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        st.markdown(
            "<p style='text-align:center; color:#7b8798; font-size:0.78rem; "
            "margin-top:1rem'>Protótipo inicial. Não utilize senhas importantes "
            "ou reutilizadas de outros serviços.</p>",
            unsafe_allow_html=True,
        )

def _open_saved_conversation(conversation_id, user_id):
    """Callback executado antes da reconstrução dos widgets do Streamlit."""
    conversation = get_conversation(conversation_id, user_id)
    if not conversation:
        return

    st.session_state.active_conversation_id = conversation["id"]
    st.session_state.active_conversation_subject = conversation["subject_slug"]
    st.session_state.selected_subject = conversation["subject_slug"]
    st.session_state.subject_navigation = conversation["subject_slug"]
    st.session_state.page = "chat"


def _conversation_label(conversation, subject_by_slug):
    subject_name = subject_by_slug.get(
        conversation["subject_slug"],
        conversation["subject_slug"],
    )
    title = str(conversation.get("title") or "Nova conversa").strip()

    if len(title) > 42:
        title = title[:39].rstrip() + "..."

    return (
        f"{title}  ·  {subject_name}  ·  "
        f"{_conversation_date(conversation.get('created_at'))}"
    )


def show_sidebar(user):
    with st.sidebar:
        st.markdown("# 🧠 Mente Saber")
        st.caption(f"Olá, {user['display_name']}!")
        st.divider()

        st.markdown("### Escolha seu tutor")
        current = st.session_state.get(
            "selected_subject", SUBJECTS[0]["slug"]
        )
        slugs = [s["slug"] for s in SUBJECTS]
        labels = {
            s["slug"]: f"{s['emoji']} {s['name']}"
            for s in SUBJECTS
        }

        chosen = st.radio(
            "Disciplinas",
            slugs,
            index=slugs.index(current) if current in slugs else 0,
            format_func=lambda x: labels[x],
            label_visibility="collapsed",
            key="subject_navigation",
        )

        if chosen != current:
            # Ao entrar em outra matéria, começa uma conversa nova.
            st.session_state.selected_subject = chosen
            new_conversation_id = create_conversation(user["id"], chosen)
            st.session_state.active_conversation_id = new_conversation_id
            st.session_state.active_conversation_subject = chosen
            st.rerun()

        st.divider()
        st.markdown("### 🕘 Histórico de conversas")
        conversations = list_conversations(user["id"], limit=40)
        subject_by_slug = {
            s["slug"]: s["name"] for s in SUBJECTS
        }

        if not conversations:
            st.caption("Suas conversas aparecerão aqui.")
        else:
            active_id = st.session_state.get("active_conversation_id")
            active = (
                get_conversation(active_id, user["id"])
                if active_id else None
            )

            if active:
                st.caption("Conversa aberta")
                st.caption(
                    _conversation_label(active, subject_by_slug)
                )

            for conversation in conversations:
                label = _conversation_label(
                    conversation, subject_by_slug
                )
                is_active = conversation["id"] == active_id
                button_label = ("📍 " if is_active else "💬 ") + label

                st.button(
                    button_label,
                    key=f"open_conversation_{conversation['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    on_click=_open_saved_conversation,
                    args=(conversation["id"], user["id"]),
                )

        st.divider()
        sub = get_subscription(user["id"])
        used = count_free_questions(user["id"])

        if sub and sub["status"] == "active":
            st.success("Plano ativo")
            st.caption("Acesso de assinante")
        else:
            st.markdown("**Teste gratuito**")
            st.progress(min(used, FREE_QUESTIONS) / FREE_QUESTIONS)
            st.caption(
                f"{min(used, FREE_QUESTIONS)} de "
                f"{FREE_QUESTIONS} perguntas utilizadas"
            )
            st.markdown(f"### R$ {PRICE:.2f}/mês".replace(".", ","))
            st.caption("Assinatura mensal planejada")

        if st.button("Minha conta / plano", use_container_width=True):
            st.session_state.page = "account"
            st.rerun()

        if st.button("Sair", use_container_width=True):
            logout()

def show_account(user):
    st.title("Minha conta")
    st.write(f"**Nome:** {user['display_name']}")
    st.write(f"**E-mail:** {user['email']}")

    sub = get_subscription(user["id"])

    if sub and sub["status"] == "active":
        st.success("Sua conta está marcada como assinante ativa.")
        st.caption(
            "No protótipo, o status pode ser ativado em modo de demonstração. "
            "Ainda não há cobrança real."
        )

        if st.button("Desativar assinatura de demonstração"):
            deactivate_subscription(user["id"])
            st.rerun()
    else:
        st.subheader("Mente Saber Premium")
        st.markdown("### R$ 35,00 por mês")
        st.write(
            "Acesso aos tutores com uso sujeito a uma política de uso justo, "
            "que será definida após os testes."
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

    if st.button("Voltar ao chat"):
        st.session_state.page = "chat"
        st.rerun()


def is_english_subject(subject):
    """Identifica a disciplina de inglês pelo nome ou pelo identificador."""
    name = str(subject.get("name", "")).casefold()
    slug = str(subject.get("slug", "")).casefold()
    return any(
        term in f"{name} {slug}"
        for term in ("inglês", "ingles", "english")
    )


def show_english_pronunciation():
    """Mostra um leitor de pronúncia em inglês usando a voz do navegador."""
    st.subheader("🔊 Ouvir pronúncia")
    st.caption(
        "Digite uma palavra ou frase em inglês e ouça como ela é pronunciada. "
        "Você pode repetir o áudio quantas vezes quiser."
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
            <input id="englishText" type="text"
                   placeholder="Ex.: How are you?" autocomplete="off">

            <label for="accent">Pronúncia</label>
            <select id="accent">
                <option value="en-US">Inglês americano</option>
                <option value="en-GB">Inglês britânico</option>
            </select>

            <button id="speakButton" type="button">
                🔊 Ouvir pronúncia
            </button>
            <button id="stopButton" type="button">Parar áudio</button>
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

                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.lang = accent.value;
                        utterance.rate = 0.85;

                        const voices = window.speechSynthesis.getVoices();
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
def _conversation_date(value):
    """Converte a data ISO do banco para DD/MM/AAAA, sem interromper a tela."""
    try:
        from datetime import datetime
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return "Data não informada"


def _open_saved_conversation(conversation_id, user_id):
    """Callback executado antes da reconstrução dos widgets do Streamlit."""
    conversation = get_conversation(conversation_id, user_id)
    if not conversation:
        return

    st.session_state.active_conversation_id = conversation["id"]
    st.session_state.active_conversation_subject = conversation["subject_slug"]
    st.session_state.selected_subject = conversation["subject_slug"]
    st.session_state.subject_navigation = conversation["subject_slug"]
    st.session_state.page = "chat"


def _conversation_label(conversation, subject_by_slug):
    subject_name = subject_by_slug.get(
        conversation["subject_slug"],
        conversation["subject_slug"],
    )
    title = str(conversation.get("title") or "Nova conversa").strip()

    if len(title) > 42:
        title = title[:39].rstrip() + "..."

    return (
        f"{title}  ·  {subject_name}  ·  "
        f"{_conversation_date(conversation.get('created_at'))}"
    )


def show_sidebar(user):
    with st.sidebar:
        st.markdown("# 🧠 Mente Saber")
        st.caption(f"Olá, {user['display_name']}!")
        st.divider()

        st.markdown("### Escolha seu tutor")
        current = st.session_state.get(
            "selected_subject", SUBJECTS[0]["slug"]
        )
        slugs = [s["slug"] for s in SUBJECTS]
        labels = {
            s["slug"]: f"{s['emoji']} {s['name']}"
            for s in SUBJECTS
        }

        chosen = st.radio(
            "Disciplinas",
            slugs,
            index=slugs.index(current) if current in slugs else 0,
            format_func=lambda x: labels[x],
            label_visibility="collapsed",
            key="subject_navigation",
        )

        if chosen != current:
            # Ao entrar em outra matéria, começa uma conversa nova.
            st.session_state.selected_subject = chosen
            new_conversation_id = create_conversation(user["id"], chosen)
            st.session_state.active_conversation_id = new_conversation_id
            st.session_state.active_conversation_subject = chosen
            st.rerun()

        st.divider()
        st.markdown("### 🕘 Histórico de conversas")
        conversations = list_conversations(user["id"], limit=40)
        subject_by_slug = {
            s["slug"]: s["name"] for s in SUBJECTS
        }

        if not conversations:
            st.caption("Suas conversas aparecerão aqui.")
        else:
            active_id = st.session_state.get("active_conversation_id")
            active = (
                get_conversation(active_id, user["id"])
                if active_id else None
            )

            if active:
                st.caption("Conversa aberta")
                st.caption(
                    _conversation_label(active, subject_by_slug)
                )

            for conversation in conversations:
                label = _conversation_label(
                    conversation, subject_by_slug
                )
                is_active = conversation["id"] == active_id
                button_label = ("📍 " if is_active else "💬 ") + label

                st.button(
                    button_label,
                    key=f"open_conversation_{conversation['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    on_click=_open_saved_conversation,
                    args=(conversation["id"], user["id"]),
                )

        st.divider()
        sub = get_subscription(user["id"])
        used = count_free_questions(user["id"])

        if sub and sub["status"] == "active":
            st.success("Plano ativo")
            st.caption("Acesso de assinante")
        else:
            st.markdown("**Teste gratuito**")
            st.progress(min(used, FREE_QUESTIONS) / FREE_QUESTIONS)
            st.caption(
                f"{min(used, FREE_QUESTIONS)} de "
                f"{FREE_QUESTIONS} perguntas utilizadas"
            )
            st.markdown(f"### R$ {PRICE:.2f}/mês".replace(".", ","))
            st.caption("Assinatura mensal planejada")

        if st.button("Minha conta / plano", use_container_width=True):
            st.session_state.page = "account"
            st.rerun()

        if st.button("Sair", use_container_width=True):
            logout()


def show_account(user):
    st.title("Minha conta")
    st.write(f"**Nome:** {user['display_name']}")
    st.write(f"**E-mail:** {user['email']}")

    sub = get_subscription(user["id"])

    if sub and sub["status"] == "active":
        st.success("Sua conta está marcada como assinante ativa.")
        st.caption(
            "No protótipo, o status pode ser ativado em modo de demonstração. "
            "Ainda não há cobrança real."
        )

        if st.button("Desativar assinatura de demonstração"):
            deactivate_subscription(user["id"])
            st.rerun()
    else:
        st.subheader("Mente Saber Premium")
        st.markdown("### R$ 35,00 por mês")
        st.write(
            "Acesso aos tutores com uso sujeito a uma política de uso justo, "
            "que será definida após os testes."
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

    if st.button("Voltar ao chat"):
        st.session_state.page = "chat"
        st.rerun()


def is_english_subject(subject):
    """Identifica a disciplina de inglês pelo nome ou pelo identificador."""
    name = str(subject.get("name", "")).casefold()
    slug = str(subject.get("slug", "")).casefold()
    return any(
        term in f"{name} {slug}"
        for term in ("inglês", "ingles", "english")
    )


def show_english_pronunciation():
    """Mostra um leitor de pronúncia em inglês usando a voz do navegador."""
    st.subheader("🔊 Ouvir pronúncia")
    st.caption(
        "Digite uma palavra ou frase em inglês e ouça como ela é pronunciada. "
        "Você pode repetir o áudio quantas vezes quiser."
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
            <input id="englishText" type="text"
                   placeholder="Ex.: How are you?" autocomplete="off">

            <label for="accent">Pronúncia</label>
            <select id="accent">
                <option value="en-US">Inglês americano</option>
                <option value="en-GB">Inglês britânico</option>
            </select>

            <button id="speakButton" type="button">
                🔊 Ouvir pronúncia
            </button>
            <button id="stopButton" type="button">Parar áudio</button>
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

                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.lang = accent.value;
                        utterance.rate = 0.85;

                        const voices = window.speechSynthesis.getVoices();
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
def _conversation_date(value):
    """Converte a data ISO do banco para DD/MM/AAAA, sem interromper a tela."""
    try:
        from datetime import datetime
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return "Data não informada"


def _open_saved_conversation(conversation_id, user_id):
    """Callback executado antes da reconstrução dos widgets do Streamlit."""
    conversation = get_conversation(conversation_id, user_id)
    if not conversation:
        return

    st.session_state.active_conversation_id = conversation["id"]
    st.session_state.active_conversation_subject = conversation["subject_slug"]
    st.session_state.selected_subject = conversation["subject_slug"]
    st.session_state.subject_navigation = conversation["subject_slug"]
    st.session_state.page = "chat"


def _conversation_label(conversation, subject_by_slug):
    subject_name = subject_by_slug.get(
        conversation["subject_slug"],
        conversation["subject_slug"],
    )
    title = str(conversation.get("title") or "Nova conversa").strip()

    if len(title) > 42:
        title = title[:39].rstrip() + "..."

    return (
        f"{title}  ·  {subject_name}  ·  "
        f"{_conversation_date(conversation.get('created_at'))}"
    )


def show_sidebar(user):
    with st.sidebar:
        st.markdown("# 🧠 Mente Saber")
        st.caption(f"Olá, {user['display_name']}!")
        st.divider()

        st.markdown("### Escolha seu tutor")
        current = st.session_state.get(
            "selected_subject", SUBJECTS[0]["slug"]
        )
        slugs = [s["slug"] for s in SUBJECTS]
        labels = {
            s["slug"]: f"{s['emoji']} {s['name']}"
            for s in SUBJECTS
        }

        chosen = st.radio(
            "Disciplinas",
            slugs,
            index=slugs.index(current) if current in slugs else 0,
            format_func=lambda x: labels[x],
            label_visibility="collapsed",
            key="subject_navigation",
        )

        if chosen != current:
            # Ao entrar em outra matéria, começa uma conversa nova.
            st.session_state.selected_subject = chosen
            new_conversation_id = create_conversation(user["id"], chosen)
            st.session_state.active_conversation_id = new_conversation_id
            st.session_state.active_conversation_subject = chosen
            st.rerun()

        st.divider()
        st.markdown("### 🕘 Histórico de conversas")
        conversations = list_conversations(user["id"], limit=40)
        subject_by_slug = {
            s["slug"]: s["name"] for s in SUBJECTS
        }

        if not conversations:
            st.caption("Suas conversas aparecerão aqui.")
        else:
            active_id = st.session_state.get("active_conversation_id")
            active = (
                get_conversation(active_id, user["id"])
                if active_id else None
            )

            if active:
                st.caption("Conversa aberta")
                st.caption(
                    _conversation_label(active, subject_by_slug)
                )

            for conversation in conversations:
                label = _conversation_label(
                    conversation, subject_by_slug
                )
                is_active = conversation["id"] == active_id
                button_label = ("📍 " if is_active else "💬 ") + label

                st.button(
                    button_label,
                    key=f"open_conversation_{conversation['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    on_click=_open_saved_conversation,
                    args=(conversation["id"], user["id"]),
                )

        st.divider()
        sub = get_subscription(user["id"])
        used = count_free_questions(user["id"])

        if sub and sub["status"] == "active":
            st.success("Plano ativo")
            st.caption("Acesso de assinante")
        else:
            st.markdown("**Teste gratuito**")
            st.progress(min(used, FREE_QUESTIONS) / FREE_QUESTIONS)
            st.caption(
                f"{min(used, FREE_QUESTIONS)} de "
                f"{FREE_QUESTIONS} perguntas utilizadas"
            )
            st.markdown(f"### R$ {PRICE:.2f}/mês".replace(".", ","))
            st.caption("Assinatura mensal planejada")

        if st.button("Minha conta / plano", use_container_width=True):
            st.session_state.page = "account"
            st.rerun()

        if st.button("Sair", use_container_width=True):
            logout()


def show_account(user):
    st.title("Minha conta")
    st.write(f"**Nome:** {user['display_name']}")
    st.write(f"**E-mail:** {user['email']}")

    sub = get_subscription(user["id"])

    if sub and sub["status"] == "active":
        st.success("Sua conta está marcada como assinante ativa.")
        st.caption(
            "No protótipo, o status pode ser ativado em modo de demonstração. "
            "Ainda não há cobrança real."
        )

        if st.button("Desativar assinatura de demonstração"):
            deactivate_subscription(user["id"])
            st.rerun()
    else:
        st.subheader("Mente Saber Premium")
        st.markdown("### R$ 35,00 por mês")
        st.write(
            "Acesso aos tutores com uso sujeito a uma política de uso justo, "
            "que será definida após os testes."
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

    if st.button("Voltar ao chat"):
        st.session_state.page = "chat"
        st.rerun()


def is_english_subject(subject):
    """Identifica a disciplina de inglês pelo nome ou pelo identificador."""
    name = str(subject.get("name", "")).casefold()
    slug = str(subject.get("slug", "")).casefold()
    return any(
        term in f"{name} {slug}"
        for term in ("inglês", "ingles", "english")
    )


def show_english_pronunciation():
    """Mostra um leitor de pronúncia em inglês usando a voz do navegador."""
    st.subheader("🔊 Ouvir pronúncia")
    st.caption(
        "Digite uma palavra ou frase em inglês e ouça como ela é pronunciada. "
        "Você pode repetir o áudio quantas vezes quiser."
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
            <input id="englishText" type="text"
                   placeholder="Ex.: How are you?" autocomplete="off">

            <label for="accent">Pronúncia</label>
            <select id="accent">
                <option value="en-US">Inglês americano</option>
                <option value="en-GB">Inglês britânico</option>
            </select>

            <button id="speakButton" type="button">
                🔊 Ouvir pronúncia
            </button>
            <button id="stopButton" type="button">Parar áudio</button>
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

                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.lang = accent.value;
                        utterance.rate = 0.85;

                        const voices = window.speechSynthesis.getVoices();
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