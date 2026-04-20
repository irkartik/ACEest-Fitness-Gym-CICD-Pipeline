import os
import sqlite3
from flask import Flask, jsonify, request, g, render_template

app = Flask(__name__)

DB_PATH = os.environ.get("ACEEST_DB", "aceest_fitness.db")

# ---------- Program Data Store ----------

PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": [
            "Mon: 5x5 Back Squat + AMRAP",
            "Tue: EMOM 20min Assault Bike",
            "Wed: Bench Press + 21-15-9",
            "Thu: 10RFT Deadlifts/Box Jumps",
            "Fri: 30min Active Recovery",
        ],
        "diet": {
            "breakfast": "3 Egg Whites + Oats Idli",
            "lunch": "Grilled Chicken + Brown Rice",
            "dinner": "Fish Curry + Millet Roti",
            "target_kcal": 2000,
        },
        "calorie_factor": 22,
    },
    "Muscle Gain (MG)": {
        "workout": [
            "Mon: Squat 5x5",
            "Tue: Bench 5x5",
            "Wed: Deadlift 4x6",
            "Thu: Front Squat 4x8",
            "Fri: Incline Press 4x10",
            "Sat: Barbell Rows 4x10",
        ],
        "diet": {
            "breakfast": "4 Eggs + PB Oats",
            "lunch": "Chicken Biryani (250g Chicken)",
            "dinner": "Mutton Curry + Jeera Rice",
            "target_kcal": 3200,
        },
        "calorie_factor": 35,
    },
    "Beginner (BG)": {
        "workout": [
            "Circuit Training: Air Squats, Ring Rows, Push-ups",
            "Focus: Technique Mastery & Form (90% Threshold)",
        ],
        "diet": {
            "breakfast": "Idli-Sambar",
            "lunch": "Rice-Dal",
            "dinner": "Chapati",
            "target_kcal": 2200,
            "protein_g": 120,
        },
        "calorie_factor": 26,
    },
}

SITE_METRICS = {
    "capacity": 150,
    "area_sqft": 10000,
    "break_even_members": 250,
}

# ---------- Database Helpers ----------


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            age INTEGER,
            height REAL,
            weight REAL,
            program TEXT,
            calories INTEGER,
            target_weight REAL,
            target_adherence INTEGER,
            membership_status TEXT DEFAULT 'Active',
            membership_end TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date TEXT NOT NULL,
            workout_type TEXT,
            duration_min INTEGER,
            notes TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            week TEXT,
            adherence INTEGER
        )
        """
    )

    db.commit()
    db.close()


# ---------- Routes: Homepage ----------


@app.route("/")
def index():
    return render_template("index.html")


# ---------- Routes: Health ----------


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "app": "ACEest Fitness & Gym API"})


# ---------- Routes: Programs ----------


@app.route("/api/programs", methods=["GET"])
def get_programs():
    return jsonify(PROGRAMS)


@app.route("/api/programs/<program_name>", methods=["GET"])
def get_program(program_name):
    for key, val in PROGRAMS.items():
        if key == program_name or key.startswith(program_name):
            return jsonify({key: val})
    return jsonify({"error": "Program not found"}), 404


@app.route("/api/site-metrics", methods=["GET"])
def get_site_metrics():
    return jsonify(SITE_METRICS)


# ---------- Routes: Clients ----------


@app.route("/api/clients", methods=["GET"])
def list_clients():
    db = get_db()
    rows = db.execute("SELECT * FROM clients ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/clients/<name>", methods=["GET"])
def get_client(name):
    db = get_db()
    row = db.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(dict(row))


@app.route("/api/clients", methods=["POST"])
def create_client():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    name = data["name"]
    program = data.get("program", "")
    weight = data.get("weight", 0)

    # Auto-calculate calories based on program factor
    factor = PROGRAMS.get(program, {}).get("calorie_factor", 25)
    calories = int(weight * factor) if weight else None

    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO clients (name, age, height, weight, program, calories,
                                 target_weight, target_adherence, membership_status, membership_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                data.get("age"),
                data.get("height"),
                weight,
                program,
                calories,
                data.get("target_weight"),
                data.get("target_adherence"),
                data.get("membership_status", "Active"),
                data.get("membership_end"),
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": f"Client '{name}' already exists"}), 409

    return jsonify({"message": f"Client '{name}' created", "calories": calories}), 201


@app.route("/api/clients/<name>", methods=["PUT"])
def update_client(name):
    db = get_db()
    existing = db.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
    if not existing:
        return jsonify({"error": "Client not found"}), 404

    data = request.get_json() or {}
    program = data.get("program", existing["program"])
    weight = data.get("weight", existing["weight"])
    factor = PROGRAMS.get(program, {}).get("calorie_factor", 25)
    calories = int(weight * factor) if weight else existing["calories"]

    db.execute(
        """
        UPDATE clients SET age=?, height=?, weight=?, program=?, calories=?,
                           target_weight=?, target_adherence=?,
                           membership_status=?, membership_end=?
        WHERE name=?
        """,
        (
            data.get("age", existing["age"]),
            data.get("height", existing["height"]),
            weight,
            program,
            calories,
            data.get("target_weight", existing["target_weight"]),
            data.get("target_adherence", existing["target_adherence"]),
            data.get("membership_status", existing["membership_status"]),
            data.get("membership_end", existing["membership_end"]),
            name,
        ),
    )
    db.commit()
    return jsonify({"message": f"Client '{name}' updated"})


@app.route("/api/clients/<name>", methods=["DELETE"])
def delete_client(name):
    db = get_db()
    result = db.execute("DELETE FROM clients WHERE name = ?", (name,))
    db.commit()
    if result.rowcount == 0:
        return jsonify({"error": "Client not found"}), 404
    return jsonify({"message": f"Client '{name}' deleted"})


# ---------- Routes: Workouts ----------


@app.route("/api/clients/<name>/workouts", methods=["GET"])
def list_workouts(name):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM workouts WHERE client_name = ? ORDER BY date DESC", (name,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/clients/<name>/workouts", methods=["POST"])
def log_workout(name):
    data = request.get_json()
    if not data or not data.get("date"):
        return jsonify({"error": "date is required"}), 400

    db = get_db()
    db.execute(
        """
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            name,
            data["date"],
            data.get("workout_type"),
            data.get("duration_min"),
            data.get("notes"),
        ),
    )
    db.commit()
    return jsonify({"message": "Workout logged"}), 201


# ---------- Routes: Progress ----------


@app.route("/api/clients/<name>/progress", methods=["GET"])
def list_progress(name):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM progress WHERE client_name = ? ORDER BY id", (name,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/clients/<name>/progress", methods=["POST"])
def log_progress(name):
    data = request.get_json()
    if not data or data.get("adherence") is None or not data.get("week"):
        return jsonify({"error": "week and adherence are required"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
        (name, data["week"], data["adherence"]),
    )
    db.commit()
    return jsonify({"message": "Progress logged"}), 201


# ---------- Entrypoint ----------

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
