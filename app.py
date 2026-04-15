from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from flask import session
import random
import time
app = Flask(__name__)
app.secret_key = "secret123"

users = []

# ---------------- MYSQL CONFIG ----------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Chotu@0223'
app.config['MYSQL_DB'] = 'task_manager'

mysql = MySQL(app)

# ---------------- EMAIL CONFIG ----------------
EMAIL = "harikavasamsetti2004@gmail.com"
PASSWORD = "lkre btww kmmi bois"

# ---------------- SEND EMAIL ----------------
def send_email(to_email, name, title, status_text):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        EMAIL = "harikavasamsetti2004@gmail.com"
        PASSWORD = "lkre btww kmmi bois"

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)

        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL
        msg['To'] = to_email
        msg['Subject'] = "📌 Task Reminder"

        # 🎨 PREMIUM HTML EMAIL
        html = f"""
        <html>
        <body style="margin:0; padding:0; font-family:'Times New Roman', serif; background: linear-gradient(135deg, #5f2c82, #49a09d);">

            <div style="
            width:100%;
            height:100%;
            display:flex;
            justify-content:center;
            align-items:center;
            padding:40px 0;
            ">
         
            <div style="background:white; max-width:420px; width:90%; padding:30px; border-radius:15px; box-shadow:0 10px 25px rgba(0,0,0,0.2); text-align:center;">
                    
                    <h2 style="color:#5f2c82;">📚 Task Reminder</h2>

                    <p style="font-size:18px;">Hello <b>{name}</b> 👋</p>

                    <p style="font-size:16px; color:#555;">
                        Your task "<b>{title}</b>" status:
                    </p>

                    <div style="margin:20px 0; padding:15px; border-radius:10px; background:#f5f5f5; font-size:18px;">
                        {status_text}
                        <p style="color:gray;">Stay on track and complete your task on time⏰</p>
                    </div>

                    <p style="
                    margin-top:20px;
                    font-size:15px;
                    color:#555;
                    ">
                    🚀Login to your dashboard to update task status
                    </p>
                       

                    <p style="margin-top:25px; font-size:14px; color:gray;">
                        Task Prioritization & Deadline Management System
                    </p>

                </div>

            </div>

        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()

        print("✅ Premium Email Sent")

    except Exception as e:
        print("❌ Email error:", e)

# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user:
            if check_password_hash(user[2], password):
                session['user_id'] = user[0]
                return redirect('/dashboard')
            else:
                return render_template('login.html', error="Wrong password!")
        else:
            return render_template('login.html', error="User not found!")

    return render_template('login.html')

@app.route('/logout')
def logout():
    return redirect('/login')

@app.route('/')
def home():
    return redirect('/login')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user:
            otp = str(random.randint(1000, 9999))

            session['otp'] = otp
            session['otp_time'] = time.time()
            session['reset_email'] = email

            send_otp_email(email, otp)

            return redirect('/verify')
        else:
            return "Email not found ❌"

    return render_template('forgot.html')

def send_otp_email(to_email, otp):
    sender_email = EMAIL
    app_password = PASSWORD

    subject = "Your OTP for Password Reset"
    body = f"Your OTP is: {otp}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        if time.time() - session.get('otp_time', 0) > 300:
            return render_template('verify.html', error="expired")

        if entered_otp == session.get('otp'):
            return redirect('/reset')
        else:
            return render_template('verify.html', error="invalid")

    return render_template('verify.html')

@app.route('/resend')
def resend():
    email = session.get('reset_email')

    if email:
        otp = str(random.randint(1000, 9999))

        session['otp'] = otp
        session['otp_time'] = time.time()

        send_otp_email(email, otp)

    return redirect('/verify')

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            return "Passwords do not match ❌"

        email = session.get('reset_email')

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password=%s WHERE email=%s",
                    (hashed_password, email))
        mysql.connection.commit()

        return redirect('/login')

    return render_template('reset.html')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        regno = request.form['regno']

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            return render_template("register.html", error="Email already exists")

        hashed_password = generate_password_hash(password)

        cur.execute("""
            INSERT INTO users(fullname, email, password, phone, regno)
            VALUES (%s, %s, %s, %s, %s)
        """, (fullname, email, hashed_password, phone, regno))

        mysql.connection.commit()

        session['register_success'] = True
        return redirect('/register')

    return render_template('register.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, title, deadline, importance, difficulty, priority, status
        FROM tasks
        WHERE user_id=%s
    """, (session['user_id'],))

    tasks = cur.fetchall()

    # 🔢 COUNTS
    total = len(tasks)
    completed = len([t for t in tasks if t[6] == 'Completed'])
    pending = len([t for t in tasks if t[6] != 'Completed'])

    # 🔔 NOTIFICATIONS
    notifications = []
    today = date.today()

    for task in tasks:
        deadline = datetime.strptime(str(task[2]), "%Y-%m-%d").date()
        days_left = (deadline - today).days

        if days_left < 0:
         notifications.append(f"⚠️ {task[1]} is OVERDUE")
        elif days_left == 0:
         notifications.append(f"📅 {task[1]} is TODAY")
        else:
          notifications.append(f"⏳ {task[1]} - {days_left} day(s) left")

    # ✅ RETURN MUST BE INSIDE FUNCTION
    return render_template(
        "dashboard.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        notifications=notifications
    )
    

@app.route('/complete/<int:id>')
def complete(id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE tasks SET status='Completed' WHERE id=%s", (id,))
    mysql.connection.commit()
    return redirect('/dashboard')


@app.route('/delete/<int:id>')
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (id,))
    mysql.connection.commit()
    return redirect('/dashboard')

# ---------------- ADD TASK ----------------
@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect('/')

    title = request.form['title']
    deadline = request.form['deadline']
    difficulty = request.form['difficulty']
    importance = request.form['importance']

    # 🔥 SIMPLE PRIORITY LOGIC
    if importance == "High":
        priority = "High"
    elif importance == "Medium":
        priority = "Medium"
    else:
        priority = "Low"

    cur = mysql.connection.cursor()

    cur.execute("""
        INSERT INTO tasks(title, deadline, difficulty, importance, priority, status, user_id, last_remainder)
        VALUES (%s, %s, %s, %s, %s, 'Pending', %s, NULL)
    """, (title, deadline, difficulty, importance, priority, session['user_id']))

    mysql.connection.commit()

    return redirect('/dashboard')
# ---------------- DAILY REMINDER LOGIC ----------------
def check_deadlines():
    print("🚀 Scheduler running...")

    with app.app_context():
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT tasks.id, tasks.title, tasks.deadline,
                   users.email, users.FullName,
                   tasks.last_remainder, tasks.status
            FROM tasks
            JOIN users ON tasks.user_id = users.id
        """)

        tasks = cur.fetchall()   # ✅ MUST BE HERE

        print("TOTAL TASKS:", len(tasks))

        today = date.today()

        for task in tasks:
            task_id, title, deadline, email, name, last_remainder, status = task

            # ❌ skip completed
            if status == "Completed":
                continue

            # ✅ once per day
            if last_remainder is not None and last_remainder == today:
                continue

            deadline = datetime.strptime(str(deadline), "%Y-%m-%d").date()
            days_left = (deadline - today).days

            if days_left < 0:
                status_text = "⚠️ OVERDUE"
            elif days_left == 0:
                status_text = "📅 Due TODAY"
            else:
                status_text = f"⏳ {days_left} day(s) left"

            print("📤 Sending:", title)

            send_email(email, name, title, status_text)

            cur.execute("""
                UPDATE tasks SET last_remainder=%s
                WHERE id=%s
            """, (today, task_id))

            mysql.connection.commit()

# ---------------- RUN APP ----------------
import os

if __name__ == '__main__':

    # 🔥 START SCHEDULER FIRST
    scheduler = BackgroundScheduler(daemon=True)

    scheduler.add_job(check_deadlines, 'cron', hour=9, minute=0)
    # testing:
    # scheduler.add_job(check_deadlines, 'interval', minutes=1)

    scheduler.start()
    print("✅ Scheduler started")

    # 🔥 RENDER PORT FIX
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)