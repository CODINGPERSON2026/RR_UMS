from imports import *
import mysql.connector
from langchain_ollama import OllamaLLM
import re
import time
import threading
from schema import USERS_SCHEMA, PERSONNEL_SCHEMA, get_schema_for_question, get_schema_summary

ollama_bot_bp = Blueprint('bot', __name__, url_prefix='/bot')


def _get_db():
    conn = get_db_connection()
    if not conn:
        return None, None
    try:
        cursor = conn.cursor(dictionary=True)
        return conn, cursor
    except Exception:
        return conn, None


def _get_llm():
    try:
        return OllamaLLM(
            model="llama3.2:3b",
            temperature=0,
            keep_alive=-1,
            base_url="http://127.0.0.1:11434"
        )
    except Exception:
        return None


# =====================================================
# 🔥 GREETING KEYWORDS
# =====================================================
GREETING_KEYWORDS = [
    "hi", "hello", "hey",
    "good morning", "good evening", "good afternoon",
    "salam", "jai hind"
]

GREETING_RESPONSE = "Jai Hind! 👋 I am 15CESR Assistant.\nHow can I help you today?"


# =====================================================
# 🔥 NORMALIZATION
# =====================================================
def normalize_question(question: str) -> str:
    question = question.lower()

    # Strip regiment name
    question = re.sub(r'\b15cesr\b', '', question).strip()

    # 1 coy / 1 co → 1 Company
    question = re.sub(r'\b(\d+)\s*(coy|co|company)\b',
                      lambda m: f"{m.group(1)} Company", question)

    # hq coy / hq co → HQ Company
    question = re.sub(r'\bhq\s*(coy|co|company)\b', "HQ Company", question)

    # rank short forms → normalized
    question = re.sub(r'\b(havl|havaldar)\b', 'hav', question)
    question = re.sub(r'\blance hav\b', 'l hav', question)
    question = re.sub(r'\b(lance nk|lance naik)\b', 'l nk', question)
    question = re.sub(r'\b(nb sub|nb subedar)\b', 'naib subedar', question)
    question = re.sub(r'\bnaik\b', 'nk', question)
    question = re.sub(r'\bsig man\b', 'signal man', question)
    question = re.sub(r'\bsub maj\b', 'subedar major', question)
    question = re.sub(r'\bdet\b', 'detachment', question)

    return question


# =====================================================
# 🔥 GREETING DETECTOR
# =====================================================
def is_greeting(question: str) -> bool:
    q = question.lower()
    for keyword in GREETING_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', q):
            return True
    return False


# =====================================================
# 🔥 NAME SEARCH DETECTOR
# =====================================================
def extract_name_search(question: str):
    """
    Detects name/army_number search patterns.
    Only called AFTER keyword routing fails.
    """
    q = question.strip().lower()

    # Pattern 1: "who is <name>"
    match = re.match(r'^who is\s+(.+)$', q)
    if match:
        name = match.group(1).strip()
        return name

    # Pattern 2: "<name> who is he/she/this"
    match = re.match(r'^(.+?)\s+who is\s+(he|she|this|that)?$', q)
    if match:
        name = match.group(1).strip()
        return name

    return None


# =====================================================
# 🔥 DUAL TABLE NAME SEARCH
# =====================================================
def search_name_in_both_tables(cursor, name: str):
    """
    Search name/army_number in users first, then personnel.
    Returns (result, source_table, sql_used)
    """
    # Search users table first
    sql_users = f"SELECT username, role, company FROM users WHERE username LIKE '%{name}%'"
    cursor.execute(sql_users)
    result = cursor.fetchall()

    if result:
        return result, "users", sql_users

    # Not found in users → search personnel
    sql_personnel = f"SELECT army_number, name, `rank`, company FROM personnel WHERE name LIKE '%{name}%' OR army_number LIKE '%{name}%'"
    cursor.execute(sql_personnel)
    result = cursor.fetchall()

    if result:
        return result, "personnel", sql_personnel

    return [], "none", sql_personnel


# =====================================================
# 🔥 NATURAL LANGUAGE FORMATTER
# =====================================================
def format_result(result, generated_sql):

    # ---- 0 records ----
    if len(result) == 0:
        return "No results found."

    # ---- COUNT query ----
    if len(result) == 1:
        row = result[0]
        keys = list(row.keys())
        if len(keys) == 1 and 'count' in keys[0].lower():
            count_value = list(row.values())[0]
            return f"There are {count_value} record(s) found."

    # ---- 1 record ----
    if len(result) == 1:
        row = result[0]
        lines = []
        for key, value in row.items():
            lines.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(lines)

    # ---- Multiple records ----
    lines = []
    for i, row in enumerate(result, start=1):
        fields = " | ".join(
            f"{k.replace('_', ' ').title()}: {v}"
            for k, v in row.items()
        )
        lines.append(f"{i}. {fields}")
    return "\n".join(lines)


# -------------------------
# CHAT API
# -------------------------
@ollama_bot_bp.route("/chat", methods=["POST"])
def chat():

    _total_start = time.time()

    # -------------------------
    # STEP 1: Extract Question
    # -------------------------
    question = request.json.get("message", "").strip()

    if not question:
        return jsonify({"error": "Empty question"}), 400

    # -------------------------
    # STEP 2: Normalize
    # -------------------------
    question = normalize_question(question)

    # -------------------------
    # STEP 2.5: Greeting Check
    # -------------------------
    if is_greeting(question):
        return jsonify({"answer": GREETING_RESPONSE})

    conn, cursor = _get_db()
    if not conn or not cursor:
        return jsonify({"error": "Database connection unavailable"}), 500

    try:
        # -------------------------
        # STEP 3: Keyword Routing (ALWAYS FIRST)
        # -------------------------
        schema_to_use, matched_keyword, matched_table = get_schema_for_question(question)

        if schema_to_use:
            # ========================
            # PATH A: LLM FLOW
            # ========================
            llm = _get_llm()
            if not llm:
                return jsonify({"error": "Ollama LLM service unavailable"}), 500

            prompt = f"""
You are an expert MySQL query generator for HRMS.

STRICT RULES:
1. ONLY generate SELECT queries.
2. NEVER use DELETE, UPDATE, INSERT, DROP, ALTER.
3. NEVER select password column.
4. Return ONLY the SQL query, nothing else.
5. ALWAYS replace placeholders with actual values from the question.
6. Company names are case sensitive:
   - 'COMN Company'
   - '3 Company'
   - 'HQ Company'
7. CRITICAL: `rank` is a reserved MySQL word — ALWAYS wrap in backticks: `rank`

Database Information:
{schema_to_use}

User Question:
{question}

Return ONLY SQL query:
"""

            try:
                generated_sql = llm.invoke(prompt)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

            generated_sql = re.sub(r"```sql|```", "", generated_sql).strip()
            generated_sql = re.sub(r"^SQL:\s*", "", generated_sql, flags=re.IGNORECASE)

            sql_lower = generated_sql.lower()
            dangerous = ['delete', 'update', 'insert', 'drop', 'alter', 'create', 'truncate']
            if any(word in sql_lower for word in dangerous):
                return jsonify({"error": "Only SELECT allowed"}), 400
            if not sql_lower.startswith("select"):
                return jsonify({"error": "Invalid query"}), 400

            try:
                cursor.execute(generated_sql)
                result = cursor.fetchall()
            except mysql.connector.Error as e:
                return jsonify({"error": str(e)}), 500
            except Exception as e:
                return jsonify({"error": str(e)}), 500

            natural_answer = format_result(result, generated_sql)
            return jsonify({"answer": natural_answer})

        else:
            # ========================
            # PATH B: NAME SEARCH
            # ========================
            name = extract_name_search(question)

            if name:
                try:
                    result, source_table, generated_sql = search_name_in_both_tables(cursor, name)

                    natural_answer = format_result(result, generated_sql)
                    return jsonify({"answer": natural_answer})

                except mysql.connector.Error as e:
                    return jsonify({"error": str(e)}), 500

            # ========================
            # PATH C: NO MATCH AT ALL
            # ========================
            return jsonify({"answer": "i could not understand your quetion"}), 400

    finally:
        try:
            conn.close()
        except Exception:
            pass