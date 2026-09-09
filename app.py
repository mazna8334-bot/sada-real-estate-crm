
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sada-dev-change-me"
DB = os.path.join(os.path.dirname(__file__), "sada.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        type TEXT,
        city TEXT,
        district TEXT,
        interest TEXT,
        budget REAL DEFAULT 0,
        status TEXT DEFAULT 'جديد',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS owners(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        city TEXT,
        notes TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS properties(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        owner_id INTEGER,
        type TEXT,
        city TEXT,
        district TEXT,
        area REAL DEFAULT 0,
        price REAL DEFAULT 0,
        offer_type TEXT,
        status TEXT DEFAULT 'متاح',
        map_url TEXT,
        notes TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        request_type TEXT,
        property_type TEXT,
        city TEXT,
        district TEXT,
        budget REAL DEFAULT 0,
        details TEXT,
        status TEXT DEFAULT 'جديد',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS deals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        property_id INTEGER,
        deal_type TEXT,
        amount REAL DEFAULT 0,
        commission_percent REAL DEFAULT 0,
        commission_amount REAL DEFAULT 0,
        stage TEXT DEFAULT 'استفسار',
        collected REAL DEFAULT 0,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()

@app.before_request
def protect():
    init_db()
    if request.endpoint not in ("login","static") and not session.get("user"):
        return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "1234":
            session["user"] = "admin"
            return redirect(url_for("dashboard"))
        error = "بيانات الدخول غير صحيحة"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def dashboard():
    conn = get_db()
    stats = {
        "clients": conn.execute("SELECT COUNT(*) c FROM clients").fetchone()["c"],
        "owners": conn.execute("SELECT COUNT(*) c FROM owners").fetchone()["c"],
        "properties": conn.execute("SELECT COUNT(*) c FROM properties").fetchone()["c"],
        "available": conn.execute("SELECT COUNT(*) c FROM properties WHERE status='متاح'").fetchone()["c"],
        "requests": conn.execute("SELECT COUNT(*) c FROM requests").fetchone()["c"],
        "deals": conn.execute("SELECT COUNT(*) c FROM deals").fetchone()["c"],
        "commissions": conn.execute("SELECT COALESCE(SUM(commission_amount),0) s FROM deals").fetchone()["s"],
        "collected": conn.execute("SELECT COALESCE(SUM(collected),0) s FROM deals").fetchone()["s"],
    }
    recent = conn.execute("SELECT * FROM properties ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return render_template("dashboard.html", stats=stats, recent=recent)

@app.route("/clients")
def clients():
    conn = get_db()
    rows = conn.execute("SELECT * FROM clients ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("clients.html", rows=rows)

@app.route("/clients/add", methods=["POST"])
def add_client():
    f=request.form
    conn=get_db()
    conn.execute("""INSERT INTO clients(name,phone,type,city,district,interest,budget,status,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                 (f.get("name"),f.get("phone"),f.get("type"),f.get("city"),f.get("district"),
                  f.get("interest"),float(f.get("budget") or 0),f.get("status"),datetime.now().isoformat()))
    conn.commit(); conn.close()
    return redirect(url_for("clients"))

@app.route("/owners")
def owners():
    conn = get_db()
    rows = conn.execute("SELECT * FROM owners ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("owners.html", rows=rows)

@app.route("/owners/add", methods=["POST"])
def add_owner():
    f=request.form
    conn=get_db()
    conn.execute("INSERT INTO owners(name,phone,city,notes,created_at) VALUES(?,?,?,?,?)",
                 (f.get("name"),f.get("phone"),f.get("city"),f.get("notes"),datetime.now().isoformat()))
    conn.commit(); conn.close()
    return redirect(url_for("owners"))

@app.route("/properties")
def properties():
    conn=get_db()
    rows=conn.execute("""SELECT p.*, o.name owner_name FROM properties p
                        LEFT JOIN owners o ON o.id=p.owner_id ORDER BY p.id DESC""").fetchall()
    owners=conn.execute("SELECT * FROM owners ORDER BY name").fetchall()
    conn.close()
    return render_template("properties.html", rows=rows, owners=owners)

@app.route("/properties/add", methods=["POST"])
def add_property():
    f=request.form
    conn=get_db()
    conn.execute("""INSERT INTO properties(title,owner_id,type,city,district,area,price,offer_type,status,map_url,notes,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                 (f.get("title"),f.get("owner_id") or None,f.get("type"),f.get("city"),f.get("district"),
                  float(f.get("area") or 0),float(f.get("price") or 0),f.get("offer_type"),f.get("status"),
                  f.get("map_url"),f.get("notes"),datetime.now().isoformat()))
    conn.commit(); conn.close()
    return redirect(url_for("properties"))

@app.route("/requests")
def requests_page():
    conn=get_db()
    rows=conn.execute("""SELECT r.*, c.name client_name FROM requests r
                        LEFT JOIN clients c ON c.id=r.client_id ORDER BY r.id DESC""").fetchall()
    clients=conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    return render_template("requests.html", rows=rows, clients=clients)

@app.route("/requests/add", methods=["POST"])
def add_request():
    f=request.form
    conn=get_db()
    conn.execute("""INSERT INTO requests(client_id,request_type,property_type,city,district,budget,details,status,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                 (f.get("client_id"),f.get("request_type"),f.get("property_type"),f.get("city"),f.get("district"),
                  float(f.get("budget") or 0),f.get("details"),f.get("status"),datetime.now().isoformat()))
    conn.commit(); conn.close()
    return redirect(url_for("requests_page"))

@app.route("/deals")
def deals():
    conn=get_db()
    rows=conn.execute("""SELECT d.*, c.name client_name, p.title property_title FROM deals d
                        LEFT JOIN clients c ON c.id=d.client_id
                        LEFT JOIN properties p ON p.id=d.property_id
                        ORDER BY d.id DESC""").fetchall()
    clients=conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    properties=conn.execute("SELECT * FROM properties ORDER BY title").fetchall()
    conn.close()
    return render_template("deals.html", rows=rows, clients=clients, properties=properties)

@app.route("/deals/add", methods=["POST"])
def add_deal():
    f=request.form
    amount=float(f.get("amount") or 0)
    pct=float(f.get("commission_percent") or 0)
    commission=amount*pct/100
    conn=get_db()
    conn.execute("""INSERT INTO deals(client_id,property_id,deal_type,amount,commission_percent,commission_amount,stage,collected,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                 (f.get("client_id"),f.get("property_id"),f.get("deal_type"),amount,pct,commission,
                  f.get("stage"),float(f.get("collected") or 0),datetime.now().isoformat()))
    conn.commit(); conn.close()
    return redirect(url_for("deals"))

@app.route("/delete/<table>/<int:row_id>", methods=["POST"])
def delete_row(table,row_id):
    allowed={"clients","owners","properties","requests","deals"}
    if table not in allowed:
        return "Not allowed",400
    conn=get_db()
    conn.execute(f"DELETE FROM {table} WHERE id=?",(row_id,))
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for("dashboard"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
