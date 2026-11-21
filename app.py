import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "kunci-rahasia-default-salwa")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Inisialisasi koneksi Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def get_cv_data():
    """Ambil data CV baris id=1 dari Supabase."""
    try:
        res = supabase.table("cv").select("*").eq("id", 1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception as e:
        print("Error mengambil data CV:", e)
    return {}

@app.route("/")
def index():
    """Halaman utama portofolio."""
    try:
        res = supabase.table("projects").select("*").order("created_at", desc=True).execute()
        projects = res.data or []
    except Exception as e:
        print("Error mengambil projects:", e)
        projects = []

    cv = get_cv_data()
    return render_template("index.html", projects=projects, cv=cv)


@app.route("/cv")
def cv_page():
    """Halaman CV lengkap yang bisa dicetak/save PDF."""
    cv = get_cv_data()
    return render_template("cv.html", cv=cv)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Password salah! Silakan cek kembali."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    try:
        res = supabase.table("projects").select("*").order("created_at", desc=True).execute()
        projects = res.data or []
    except Exception as e:
        print("Error dashboard:", e)
        projects = []
    return render_template("dashboard.html", projects=projects)


@app.route("/create", methods=["POST"])
@login_required
def create_project():
    data = {
        "title": request.form.get("title"),
        "tech_stack": request.form.get("tech_stack"),
        "description": request.form.get("description"),
        "project_url": request.form.get("project_url"),
    }
    supabase.table("projects").insert(data).execute()
    return redirect(url_for("dashboard"))


@app.route("/update/<int:project_id>", methods=["POST"])
@login_required
def update_project(project_id):
    data = {
        "title": request.form.get("title"),
        "tech_stack": request.form.get("tech_stack"),
        "description": request.form.get("description"),
        "project_url": request.form.get("project_url"),
    }
    supabase.table("projects").update(data).eq("id", project_id).execute()
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:project_id>", methods=["POST"])
@login_required
def delete_project(project_id):
    supabase.table("projects").delete().eq("id", project_id).execute()
    return redirect(url_for("dashboard"))

@app.route("/dashboard/cv", methods=["GET", "POST"])
@login_required
def dashboard_cv():
    success = False
    if request.method == "POST":
        cv_data = {
            "id": 1,
            "full_name": request.form.get("full_name"),
            "job_title": request.form.get("job_title"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "location": request.form.get("location"),
            "linkedin": request.form.get("linkedin"),
            "github": request.form.get("github"),
            "summary": request.form.get("summary"),
            "skills": request.form.get("skills"),
            "experience": request.form.get("experience"),
            "education": request.form.get("education"),
        }
        supabase.table("cv").upsert(cv_data).execute()
        success = True

    cv = get_cv_data()
    return render_template("dashboard_cv.html", cv=cv, success=success)


if __name__ == "__main__":
    app.run(debug=True)