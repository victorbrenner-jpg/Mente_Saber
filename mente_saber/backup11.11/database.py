import os
import sqlite3
import hashlib
import hmac
import secrets
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = os.getenv(
    "DATABASE_PATH",
    str(Path(__file__).parent / "data" / "mente_saber.db"),
)

SUBJECTS = [
    {
        "slug": "portugues",
        "name": "Português e Gramática",
        "emoji": "📚",
        "description": (
            "Estude gramática, ortografia, pontuação, concordância, "
            "crase, interpretação de texto e redação."
        ),
    },
    {
        "slug": "matematica",
        "name": "Matemática",
        "emoji": "➗",
        "description": (
            "Aprenda conceitos, resolva problemas e veja os cálculos "
            "explicados passo a passo."
        ),
    },
    {
        "slug": "ingles",
        "name": "Inglês",
        "emoji": "🌎",
        "description": "Pratique vocabulário, gramática, leitura e conversação.",
    },
    {
        "slug": "programacao",
        "name": "Programação e Tecnologia",
        "emoji": "💻",
        "description": (
            "Aprenda lógica, Python, SQL, planilhas e conceitos de tecnologia."
        ),
    },
    {
        "slug": "historia",
        "name": "História",
        "emoji": "🏛️",
        "description": (
            "Explore períodos históricos, acontecimentos e suas relações."
        ),
    },
]


def get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def _hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310_000,
    )
    return salt.hex() + "$" + derived.hex()


def _verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        calculated = _hash_password(
            password,
            bytes.fromhex(salt_hex),
        ).split("$", 1)[1]
        return hmac.compare_digest(calculated, digest_hex)
    except (ValueError, TypeError):
        return False


def init_db():
    """Cria as tabelas e migra mensagens antigas sem apagá-las."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            avatar TEXT NOT NULL DEFAULT 'cachorro'
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject_slug TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE
                REFERENCES users(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            provider TEXT,
            provider_subscription_id TEXT,
            started_at TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message_id INTEGER,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject_slug TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT 'Nova conversa',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # Migrações seguras: preserva os usuários e mensagens existentes.
        user_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "avatar" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT NOT NULL DEFAULT 'cachorro'")

        # Converte avatares antigos para os mascotes atuais sem apagar contas.
        conn.execute("UPDATE users SET avatar = 'coruja' WHERE avatar = 'homem'")
        conn.execute("UPDATE users SET avatar = 'borboleta' WHERE avatar = 'mulher'")
        # A foca foi substituída pela borboleta.
        conn.execute("UPDATE users SET avatar = 'borboleta' WHERE avatar = 'foca'")

        # Adiciona a coluna necessária em bancos que já existiam.
        message_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(messages)"
            ).fetchall()
        }

        if "conversation_id" not in message_columns:
            conn.execute("""
                ALTER TABLE messages
                ADD COLUMN conversation_id INTEGER
                REFERENCES conversations(id)
            """)

        conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_messages_user_subject
            ON messages(user_id, subject_slug, id);

        CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id, id);

        CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
            ON conversations(user_id, updated_at DESC);
        """)

        # Agrupa as mensagens antigas por usuário e matéria.
        # O conteúdo das mensagens existentes é preservado.
        groups = conn.execute("""
            SELECT user_id, subject_slug, MIN(created_at) AS first_created
            FROM messages
            WHERE conversation_id IS NULL
            GROUP BY user_id, subject_slug
        """).fetchall()

        for group in groups:
            subject_name = next(
                (
                    item["name"]
                    for item in SUBJECTS
                    if item["slug"] == group["subject_slug"]
                ),
                group["subject_slug"],
            )

            created = group["first_created"] or utcnow()

            cur = conn.execute("""
                INSERT INTO conversations(
                    user_id, subject_slug, title, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                group["user_id"],
                group["subject_slug"],
                f"Histórico anterior — {subject_name}",
                created,
                utcnow(),
            ))

            conn.execute("""
                UPDATE messages
                SET conversation_id = ?
                WHERE user_id = ?
                  AND subject_slug = ?
                  AND conversation_id IS NULL
            """, (
                cur.lastrowid,
                group["user_id"],
                group["subject_slug"],
            ))


def create_user(display_name, email, password):
    try:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO users(
                    display_name, email, password_hash, created_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                display_name,
                email,
                _hash_password(password),
                utcnow(),
            ))

        return True, "Conta criada com sucesso."

    except sqlite3.IntegrityError:
        return False, "Já existe uma conta com esse e-mail."


def authenticate_user(email, password):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if row and _verify_password(password, row["password_hash"]):
        return dict(row)

    return None


def get_user(user_id):
    with get_conn() as conn:
        row = conn.execute("""
            SELECT id, display_name, email, created_at, avatar
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

    return dict(row) if row else None


def set_user_avatar(user_id, avatar):
    """Salva o avatar escolhido pelo usuário."""
    allowed = {"coruja", "borboleta", "cachorro", "gato"}
    if avatar not in allowed:
        raise ValueError("Avatar inválido.")
    with get_conn() as conn:
        conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))


def update_password(user_id, new_password):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_password(new_password), user_id),
        )


def count_free_questions(user_id):
    with get_conn() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS n
            FROM messages
            WHERE user_id = ? AND role = 'user'
        """, (user_id,)).fetchone()

    return int(row["n"])


def create_conversation(user_id, subject_slug, title="Nova conversa"):
    now = utcnow()

    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO conversations(
                user_id, subject_slug, title, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, subject_slug, title, now, now))

        return int(cur.lastrowid)

def list_conversations(user_id, limit=40):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, user_id, subject_slug, title, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
        """, (user_id, max(1, int(limit)))).fetchall()

    return [dict(row) for row in rows]


def get_conversation(conversation_id, user_id):
    if not conversation_id:
        return None

    with get_conn() as conn:
        row = conn.execute("""
            SELECT id, user_id, subject_slug, title, created_at, updated_at
            FROM conversations
            WHERE id = ? AND user_id = ?
        """, (conversation_id, user_id)).fetchone()

    return dict(row) if row else None


def get_conversation_history(user_id, conversation_id, limit=100):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, role, content, created_at
            FROM messages
            WHERE user_id = ? AND conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (
            user_id,
            conversation_id,
            max(1, int(limit)),
        )).fetchall()

    return [dict(row) for row in reversed(rows)]


def save_message(
    user_id,
    subject_slug,
    role,
    content,
    conversation_id=None,
):
    with get_conn() as conn:
        if conversation_id:
            conversation = conn.execute("""
                SELECT id
                FROM conversations
                WHERE id = ?
                  AND user_id = ?
                  AND subject_slug = ?
            """, (
                conversation_id,
                user_id,
                subject_slug,
            )).fetchone()

            if not conversation:
                raise ValueError(
                    "A conversa não pertence a este usuário ou matéria."
                )

        else:
            # Compatibilidade com chamadas antigas que não passam o ID.
            row = conn.execute("""
                SELECT id
                FROM conversations
                WHERE user_id = ? AND subject_slug = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
            """, (user_id, subject_slug)).fetchone()

            conversation_id = row["id"] if row else None

            if not conversation_id:
                now = utcnow()
                cur = conn.execute("""
                    INSERT INTO conversations(
                        user_id, subject_slug, title, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    subject_slug,
                    "Nova conversa",
                    now,
                    now,
                ))

                conversation_id = cur.lastrowid

        now = utcnow()

        cur = conn.execute("""
            INSERT INTO messages(
                user_id, subject_slug, role, content, created_at,
                conversation_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            subject_slug,
            role,
            content,
            now,
            conversation_id,
        ))

        # A primeira pergunta passa a ser o título da conversa.
        if role == "user":
            conversation = conn.execute("""
                SELECT title
                FROM conversations
                WHERE id = ?
            """, (conversation_id,)).fetchone()

            old_title = (
                conversation["title"]
                if conversation
                else "Nova conversa"
            )

            if old_title == "Nova conversa":
                full_title = " ".join(str(content).split())
                title = full_title[:60]

                if len(full_title) > 60:
                    title = title.rstrip() + "…"

                if not title:
                    title = "Nova conversa"

                conn.execute("""
                    UPDATE conversations
                    SET title = ?, updated_at = ?
                    WHERE id = ?
                """, (title, now, conversation_id))

            else:
                conn.execute("""
                    UPDATE conversations
                    SET updated_at = ?
                    WHERE id = ?
                """, (now, conversation_id))

        else:
            conn.execute("""
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
            """, (now, conversation_id))

        return int(cur.lastrowid)


def get_history(user_id, subject_slug, limit=60):
    """Mantém a função antiga disponível para compatibilidade."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, role, content, created_at
            FROM messages
            WHERE user_id = ? AND subject_slug = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, subject_slug, limit)).fetchall()

    return [dict(row) for row in reversed(rows)]


def clear_history(user_id, subject_slug):
    with get_conn() as conn:
        conn.execute("""
            DELETE FROM messages
            WHERE user_id = ? AND subject_slug = ?
        """, (user_id, subject_slug))

        conn.execute("""
            DELETE FROM conversations
            WHERE user_id = ? AND subject_slug = ?
        """, (user_id, subject_slug))


def get_subscription(user_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    return dict(row) if row else None


def activate_demo_subscription(user_id):
    now = utcnow()

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO subscriptions(
                user_id, status, provider, started_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                status = 'active',
                provider = 'demo',
                started_at = excluded.started_at,
                updated_at = excluded.updated_at
        """, (
            user_id,
            "active",
            "demo",
            now,
            now,
        ))


def deactivate_subscription(user_id):
    with get_conn() as conn:
        conn.execute("""
            UPDATE subscriptions
            SET status = 'inactive', updated_at = ?
            WHERE user_id = ?
        """, (utcnow(), user_id))


def list_subjects():
    return SUBJECTS


def save_feedback(user_id, message_id, rating, comment=""):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO feedback(
                user_id, message_id, rating, comment, created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            message_id,
            rating,
            comment,
            utcnow(),
        ))