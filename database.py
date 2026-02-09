import psycopg2
import json
import uuid

# ---------------- DB CONNECTION FUNCTION ----------------
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="pbas",
        user="postgres",
        password="Vai@020"
    )


# ---------------- CREATE NEW SESSION ----------------
def create_session(user_id):
    conn = get_connection()
    cur = conn.cursor()

    session_id = str(uuid.uuid4())

    cur.execute(
        "INSERT INTO chat_sessions(session_id, user_id, category) VALUES(%s, %s, %s)",
        (session_id, user_id, "general")
    )

    conn.commit()
    cur.close()
    conn.close()

    return session_id


# 🆕 ---------------- ENSURE SESSION EXISTS ----------------
def create_session_if_not_exists(session_id, user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT session_id FROM chat_sessions WHERE session_id=%s", (session_id,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(
            "INSERT INTO chat_sessions(session_id, user_id, category) VALUES(%s, %s, %s)",
            (session_id, user_id, "general")
        )
        conn.commit()

    cur.close()
    conn.close()


# ---------------- USER PROFILE ----------------
def get_user_stats(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM v_user_profile_stats WHERE user_id=%s", (user_id,))
    data = cur.fetchone()

    cur.close()
    conn.close()
    return data


# ---------------- RULE SEARCH ----------------
def get_rules_by_activity_and_level(keyword, academic_level):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT rule_id, activity_name, points, max_points
        FROM pbas_rules
        WHERE activity_name ILIKE %s
        AND (min_academic_level IS NULL OR min_academic_level <= %s)
    """, (f"%{keyword}%", academic_level))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ---------------- PROMOTION ----------------
def get_promotion_requirements(rank):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT required_score FROM promotion_rules WHERE rank=%s", (rank,))
    row = cur.fetchone()

    cur.close()
    conn.close()
    return row[0] if row else None


# ---------------- AUDIT LOGS ----------------
def get_audit_reason(submission_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT audit_metadata FROM audit_logs WHERE submission_id=%s", (submission_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return json.loads(row[0])
    return None


# 🔄 ---------------- CHAT MEMORY (UPDATED) ----------------
def save_message(session_id, role, content, user_id=None):
    conn = get_connection()
    cur = conn.cursor()

    # 🆕 Ensure session exists before inserting message
    if user_id:
        create_session_if_not_exists(session_id, user_id)

    cur.execute(
        "INSERT INTO chat_messages(session_id, role, content) VALUES(%s,%s,%s)",
        (session_id, role, content)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_last_messages(session_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT role, content FROM chat_messages
        WHERE session_id=%s ORDER BY timestamp DESC LIMIT 5
    """, (session_id,))

    msgs = cur.fetchall()

    cur.close()
    conn.close()

    return msgs[::-1]


# ---------------- SESSION TAGGING ----------------
def update_session_category(session_id, category):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE chat_sessions SET category=%s WHERE session_id=%s",
        (category, session_id)
    )

    conn.commit()
    cur.close()
    conn.close()
