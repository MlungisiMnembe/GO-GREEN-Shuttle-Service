import os
import sqlite3
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash, session
import bcrypt

from database import create_tables, create_connection


# --------------------------------------------------
# Load environment variables from .env
# --------------------------------------------------
load_dotenv()


# --------------------------------------------------
# Flask application configuration
# --------------------------------------------------
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is not configured."
    )


# --------------------------------------------------
# Initialise database tables
# --------------------------------------------------
create_tables()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning'); return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Administrator access required.', 'danger'); return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def approved_driver(user_id):
    conn=create_connection(); row=conn.execute("SELECT 1 FROM driver_requests WHERE user_id=? AND LOWER(status)='approved' ORDER BY id DESC LIMIT 1",(user_id,)).fetchone(); conn.close()
    return bool(row)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=='POST':
        username=request.form.get('username','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        if len(username)<2 or '@' not in email or len(password)<6:
            flash('Enter a valid name and email, and use a password of at least 6 characters.','danger'); return render_template('signup.html')
        try:
            conn=create_connection(); conn.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",(username,email,bcrypt.hashpw(password.encode(),bcrypt.gensalt()))); conn.commit(); conn.close()
            flash('Account created. You can now log in.','success'); return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('That email address is already registered.','danger')
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        admin_email = os.environ.get('ADMIN_EMAIL', '').strip().lower()
        admin_password = os.environ.get('ADMIN_PASSWORD', '')

        if admin_email and admin_password and email == admin_email and password == admin_password:
            session.clear()
            session.update(user_id=0, username='Admin', is_admin=True)
            return redirect(url_for('admin_dashboard'))
        if email==admin_email and password==admin_password:
            session.clear(); session.update(user_id=0,username='Admin',is_admin=True); return redirect(url_for('admin_dashboard'))
        conn=create_connection(); user=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); conn.close()
        if user and not user['is_blocked'] and bcrypt.checkpw(password.encode(),user['password']):
            session.clear(); session.update(user_id=user['id'],username=user['username'],is_admin=False); return redirect(url_for('dashboard'))
        flash('Invalid credentials or the account is unavailable.','danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn=create_connection(); uid=session['user_id']
    user=conn.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    rides=conn.execute("""SELECT r.*, d.username driver_name FROM rides r LEFT JOIN users d ON d.id=r.driver_id WHERE r.user_id=? ORDER BY r.id DESC""",(uid,)).fetchall()
    driver_request=conn.execute("SELECT * FROM driver_requests WHERE user_id=? ORDER BY id DESC LIMIT 1",(uid,)).fetchone(); conn.close()
    return render_template('user_dashboard.html',user=user,rides=rides,driver_request=driver_request,is_driver=approved_driver(uid))

@app.route('/ride_request', methods=['GET','POST'])
@login_required
def ride_request():
    if request.method=='POST':
        pickup=request.form.get('pickup_location','').strip(); destination=request.form.get('destination','').strip(); notes=request.form.get('notes','').strip(); method=request.form.get('payment_method','cash');
        try: passengers=max(1,min(8,int(request.form.get('passengers',1))))
        except ValueError: passengers=1
        if not pickup or not destination or pickup.lower()==destination.lower():
            flash('Please enter different pickup and destination locations.','danger'); return render_template('ride_request.html')
        # Transparent demo estimate: base R45 + R20 per passenger; no external map/API required.
        fare=45 + (20*passengers)
        conn=create_connection(); conn.execute("""INSERT INTO rides(user_id,pickup_location,destination,passengers,notes,status,fare,payment_method,payment_status) VALUES(?,?,?,?,?,'requested',?,?,?)""",(session['user_id'],pickup,destination,passengers,notes,fare,method,'pending')); conn.commit(); conn.close()
        flash('Ride requested successfully. An approved driver can now accept it.','success'); return redirect(url_for('dashboard'))
    return render_template('ride_request.html')

@app.route('/ride/<int:ride_id>/cancel', methods=['POST'])
@login_required
def cancel_ride(ride_id):
    conn=create_connection(); cur=conn.execute("UPDATE rides SET status='cancelled' WHERE id=? AND user_id=? AND status IN ('requested','accepted')",(ride_id,session['user_id'])); conn.commit(); conn.close()
    flash('Ride cancelled.' if cur.rowcount else 'This ride can no longer be cancelled.','info'); return redirect(url_for('dashboard'))

@app.route('/driver/apply', methods=['POST'])
@login_required
def submit_driver_request():
    uid=session['user_id']; license_no=request.form.get('license','').strip(); vehicle=request.form.get('vehicle','').strip()
    if not license_no or not vehicle: flash('License and vehicle details are required.','danger'); return redirect(url_for('dashboard'))
    conn=create_connection(); existing=conn.execute("SELECT * FROM driver_requests WHERE user_id=? ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
    if existing and existing['status'].lower() in ('pending','approved'):
        conn.close(); flash('You already have an active driver application.','warning'); return redirect(url_for('dashboard'))
    conn.execute("INSERT INTO driver_requests(user_id,license,vehicle,status) VALUES(?,?,?,'pending')",(uid,license_no,vehicle)); conn.commit(); conn.close(); flash('Driver application submitted for review.','success'); return redirect(url_for('dashboard'))

@app.route('/submit_driver_request', methods=['POST'])
@login_required
def submit_driver_request_legacy(): return submit_driver_request()
@app.route('/resubmit_driver_request', methods=['POST'])
@login_required
def resubmit_driver_request(): return submit_driver_request()

@app.route('/driver')
@login_required
def driver_dashboard():
    uid=session['user_id']
    if not approved_driver(uid): flash('Your driver application must be approved first.','warning'); return redirect(url_for('dashboard'))
    conn=create_connection(); available=conn.execute("""SELECT r.*,u.username customer_name FROM rides r JOIN users u ON u.id=r.user_id WHERE r.status='requested' AND r.user_id<>? ORDER BY r.id DESC""",(uid,)).fetchall(); mine=conn.execute("""SELECT r.*,u.username customer_name FROM rides r JOIN users u ON u.id=r.user_id WHERE r.driver_id=? ORDER BY r.id DESC""",(uid,)).fetchall(); conn.close()
    return render_template('driver_dashboard.html',available=available,mine=mine)

@app.route('/driver/ride/<int:ride_id>/accept', methods=['POST'])
@login_required
def accept_ride(ride_id):
    uid=session['user_id']
    if not approved_driver(uid): return redirect(url_for('dashboard'))
    conn=create_connection(); cur=conn.execute("UPDATE rides SET driver_id=?,status='accepted',accepted_at=CURRENT_TIMESTAMP WHERE id=? AND status='requested'",(uid,ride_id)); conn.commit(); conn.close(); flash('Ride accepted.' if cur.rowcount else 'That ride is no longer available.','success' if cur.rowcount else 'warning'); return redirect(url_for('driver_dashboard'))

@app.route('/driver/ride/<int:ride_id>/<action>', methods=['POST'])
@login_required
def update_ride(ride_id,action):
    uid=session['user_id']; transitions={'start':('accepted','in_progress'),'complete':('in_progress','completed')}
    if not approved_driver(uid) or action not in transitions: return redirect(url_for('driver_dashboard'))
    old,new=transitions[action]; extra=", completed_at=CURRENT_TIMESTAMP, payment_status='paid'" if new=='completed' else ''
    conn=create_connection(); cur=conn.execute(f"UPDATE rides SET status=? {extra} WHERE id=? AND driver_id=? AND status=?",(new,ride_id,uid,old)); conn.commit(); conn.close(); flash('Ride updated successfully.' if cur.rowcount else 'Ride status could not be changed.','success' if cur.rowcount else 'warning'); return redirect(url_for('driver_dashboard'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn=create_connection()
    customers=conn.execute("""SELECT u.*,COUNT(r.id) rides_taken FROM users u LEFT JOIN rides r ON r.user_id=u.id GROUP BY u.id ORDER BY u.id DESC""").fetchall()
    drivers=conn.execute("""SELECT u.id,u.username,u.email,d.license,d.vehicle,d.status FROM users u JOIN driver_requests d ON d.user_id=u.id WHERE LOWER(d.status)='approved' AND d.id=(SELECT MAX(d2.id) FROM driver_requests d2 WHERE d2.user_id=d.user_id)""").fetchall()
    pending=conn.execute("""SELECT d.*,u.username,u.email FROM driver_requests d JOIN users u ON u.id=d.user_id WHERE LOWER(d.status)='pending' AND d.id=(SELECT MAX(d2.id) FROM driver_requests d2 WHERE d2.user_id=d.user_id) ORDER BY d.id DESC""").fetchall()
    rides=conn.execute("""SELECT r.*,u.username customer_name,d.username driver_name FROM rides r JOIN users u ON u.id=r.user_id LEFT JOIN users d ON d.id=r.driver_id ORDER BY r.id DESC LIMIT 10""").fetchall()
    stats={'customers':conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],'rides':conn.execute('SELECT COUNT(*) FROM rides').fetchone()[0],'drivers':len(drivers),'pending':len(pending),'earnings':conn.execute("SELECT COALESCE(SUM(fare),0) FROM rides WHERE status='completed'").fetchone()[0]}
    conn.close(); return render_template('admin.html',customers=customers,drivers=drivers,pending_requests=pending,rides=rides,stats=stats)

@app.route('/admin/pending_requests')
@admin_required
def pending_requests():
    conn=create_connection(); pending=conn.execute("""SELECT d.*,u.username,u.email FROM driver_requests d JOIN users u ON u.id=d.user_id WHERE LOWER(d.status)='pending' ORDER BY d.id DESC""").fetchall(); conn.close(); return render_template('pending_requests.html',pending=pending)

@app.route('/admin/update_driver_status/<int:request_id>', methods=['POST'])
@admin_required
def update_driver_status(request_id):
    status=request.form.get('status','').lower()
    if status not in ('approved','declined'): flash('Invalid status.','danger'); return redirect(url_for('pending_requests'))
    conn=create_connection(); conn.execute("UPDATE driver_requests SET status=?,reviewed_at=CURRENT_TIMESTAMP WHERE id=?",(status,request_id)); conn.commit(); conn.close(); flash(f'Driver application {status}.','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    conn=create_connection(); conn.execute("UPDATE users SET is_blocked=CASE WHEN is_blocked=1 THEN 0 ELSE 1 END WHERE id=?",(user_id,)); conn.commit(); conn.close(); flash('Customer access updated.','success'); return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout(): session.clear(); flash('You have been logged out.','info'); return redirect(url_for('index'))

if __name__=='__main__': app.run(debug=True)
