from flask import Flask, render_template, request, redirect, session
from supabase import create_client

app = Flask(__name__)
app.secret_key = "feedback_secret_key"

# ---------------- SUPABASE CONFIG ----------------
SUPABASE_URL = "https://iatarpayhjxnltjhabqq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlhdGFycGF5aGp4bmx0amhhYnFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIyMzI3MzIsImV4cCI6MjA5NzgwODczMn0.D0DVl2BWqMW2LZYrZmSjb-OH50iSPLSdeI82dnEWjYU"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- HOME / LOGIN ----------------
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/check', methods=['POST'])
def check():

    student_id = request.form['student_id']
    password = request.form['password']

    response = supabase.table("students") \
        .select("*") \
        .eq("student_id", student_id) \
        .eq("password", password) \
        .execute()

    user = response.data

    if user:
        user = user[0]
        session['student_id'] = user['student_id']
        session['name'] = user['name']
        return redirect('/dashboard')

    return "Invalid Login"


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():

    if 'student_id' not in session:
        return redirect('/')

    return render_template('dashboard.html', name=session['name'])


# ---------------- GIVE FEEDBACK ----------------
@app.route('/give-feedback')
def give_feedback():

    if 'student_id' not in session:
        return redirect('/')

    response = supabase.table("students").select("student_id,name").execute()
    students = response.data

    return render_template('give_feedback.html', students=students)


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():

    if 'student_id' not in session:
        return redirect('/')

    giver_id = session['student_id']
    receiver_id = request.form['receiver_id']
    rating = request.form['rating']
    comment = request.form['comment']

    if giver_id == receiver_id:
        return "You cannot give feedback to yourself."

    # check duplicate
    existing = supabase.table("feedback") \
        .select("*") \
        .eq("giver_id", giver_id) \
        .eq("receiver_id", receiver_id) \
        .execute()

    if existing.data:
        return "Already submitted feedback."

    # insert feedback
    supabase.table("feedback").insert({
        "giver_id": giver_id,
        "receiver_id": receiver_id,
        "rating": int(rating),
        "comment": comment
    }).execute()

    return redirect('/dashboard')


# ---------------- MY FEEDBACK ----------------
@app.route('/my-feedback')
def my_feedback():

    if 'student_id' not in session:
        return redirect('/')

    response = supabase.table("feedback") \
        .select("rating,comment") \
        .eq("receiver_id", session['student_id']) \
        .execute()

    feedbacks = response.data

    return render_template('my_feedback.html', feedbacks=feedbacks)


# ---------------- CHANGE PASSWORD ----------------
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():

    if 'student_id' not in session:
        return redirect('/')

    if request.method == 'POST':

        old_password = request.form['old_password']
        new_password = request.form['new_password']

        response = supabase.table("students") \
            .select("*") \
            .eq("student_id", session['student_id']) \
            .eq("password", old_password) \
            .execute()

        user = response.data

        if not user:
            return "Old password is incorrect"

        supabase.table("students") \
            .update({"password": new_password}) \
            .eq("student_id", session['student_id']) \
            .execute()

        return redirect('/dashboard')

    return render_template('change_password.html')


# ---------------- ADMIN LOGIN ----------------
@app.route('/admin-login')
def admin_login():
    return render_template('admin_login.html')


@app.route('/admin-check', methods=['POST'])
def admin_check():

    username = request.form['username']
    password = request.form['password']

    if username == "rohith" and password == "rohith9550":
        session['admin'] = True
        return redirect('/admin')

    return "Invalid Admin Login"


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():

    if 'admin' not in session:
        return redirect('/admin-login')

    response = supabase.table("feedback").select("*").execute()
    data = response.data

    results = {}

    for f in data:
        rid = f['receiver_id']
        if rid not in results:
            results[rid] = {"count": 0, "total": 0}

        results[rid]["count"] += 1
        results[rid]["total"] += f["rating"]

    final_results = []
    for k, v in results.items():
        final_results.append((
            k,
            v["count"],
            round(v["total"] / v["count"], 2)
        ))

    return render_template('admin.html', results=final_results)


# ---------------- ADMIN VIEW ----------------
@app.route('/admin-view/<student_id>')
def admin_view(student_id):

    if 'admin' not in session:
        return redirect('/admin-login')

    response = supabase.table("feedback") \
        .select("giver_id,rating,comment") \
        .eq("receiver_id", student_id) \
        .execute()

    data = response.data

    return render_template('admin_view.html', data=data, student_id=student_id)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin-login')


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)