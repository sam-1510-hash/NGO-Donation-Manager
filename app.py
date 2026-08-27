import re
from io import BytesIO
from sched import scheduler
import MySQLdb
import MySQLdb.cursors
from flask import Flask, render_template, request, session, json
from flask import flash, redirect, url_for
from flask import send_file
from flask_apscheduler import APScheduler
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
from reportlab.lib import colors
app = Flask(__name__)
app.secret_key = 'funddonate_secret_key_2023'

# MySQL Configuration for XAMPP
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'fund_donation_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# ---------- Flask-Mail Setup ----------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'amrutawavdhane@gmail.com'
app.config['MAIL_PASSWORD'] = 'vqvlfzyanfyofeac'
mail = Mail(app)


# ROUTES
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/donor-login', methods=['GET', 'POST'])
def donor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM donors WHERE email = %s AND password = %s', (email, password))
        donor = cursor.fetchone()

        if donor:
            session['donor_loggedin'] = True
            session['donor_id'] = donor['id']
            session['donor_name'] = donor['fullname']
            flash('Login successful!', 'success')
            return redirect(url_for('donor_dashboard'))
        else:
            flash('Invalid email or password!', 'error')

    return render_template('donor-login.html')


@app.route('/donor-register', methods=['GET', 'POST'])
def donor_register():
    if request.method == 'POST':
        try:
            fullname = request.form['fullname']
            designation = request.form['designation']
            address = request.form['address']
            city = request.form['city']
            taluka = request.form['taluka']
            district = request.form['district']
            state = request.form['state']
            country = request.form['country']
            email = request.form['email']
            phone = request.form['phone']
            aadhar_no = request.form['aadhar_no']
            pan_no = request.form['pan_no']
            account_holder = request.form['account_holder']
            account_number = request.form['account_number']
            bank_name = request.form['bank_name']
            branch_name = request.form['branch_name']
            ifsc_code = request.form['ifsc_code']
            branch_city = request.form['branch_city']
            donation_type = request.form['donation_type']
            donation_date = request.form.get('donation_date')
            tax_benefit = 'yes' if request.form.get('tax_benefit') else 'no'
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('donor_register'))

            if not re.match(r'^\d{12}$', aadhar_no):
                flash('Aadhar number must be exactly 12 digits', 'error')
                return redirect(url_for('donor_register'))

            if not re.match(r'^[A-Z]{5}\d{4}[A-Z]$', pan_no.upper()):
                flash('PAN number must be in the format ABCDE1234F', 'error')
                return redirect(url_for('donor_register'))

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM donors WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email is already registered!', 'error')
                return redirect(url_for('donor_register'))

            cursor.execute('''
                INSERT INTO donors (
                    fullname, designation, address, city, taluka, district, state, country,
                    email, phone, aadhar_no, pan_no,
                    account_holder, account_number, bank_name, branch_name,
                    ifsc_code, branch_city, donation_type, donation_date,
                    tax_benefit, password
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                fullname, designation, address, city, taluka, district, state, country,
                email, phone, aadhar_no, pan_no.upper(),
                account_holder, account_number, bank_name, branch_name,
                ifsc_code.upper(), branch_city, donation_type, donation_date,
                tax_benefit, password
            ))

            mysql.connection.commit()
            cursor.close()

            flash('Donor registered successfully! Please log in.', 'success')
            return redirect(url_for('donor_login'))

        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('donor_register'))

    return render_template('donor-register.html')


@app.route('/ngo-register', methods=['GET', 'POST'])
def ngo_register():
    if request.method == 'POST':
        try:
            org_name = request.form['org_name']
            activity_name = request.form['activity_name']
            org_description = request.form['org_description']
            contact_person = request.form['contact_person']
            contact_designation = request.form['contact_designation']
            email = request.form['email']
            phone = request.form['phone']
            org_address = request.form['org_address']
            city = request.form['city']
            state = request.form['state']
            pincode = request.form['pincode']
            website = request.form.get('website', '')
            registration_no = request.form['registration_no']
            registration_date = request.form['registration_date']
            certificate_80g = request.form.get('80g_certificate', '')
            account_holder = request.form['account_holder']
            account_number = request.form['account_number']
            bank_name = request.form['bank_name']
            branch_name = request.form['branch_name']
            ifsc_code = request.form['ifsc_code']
            branch_city = request.form['branch_city']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('ngo_register'))

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM ngos WHERE email = %s OR registration_no = %s", (email, registration_no))
            existing_ngo = cursor.fetchone()

            if existing_ngo:
                flash('NGO with this email or registration number already exists!', 'error')
                return redirect(url_for('ngo_register'))

            cursor.execute('''
                INSERT INTO ngos (org_name, activity_name, org_description, contact_person, 
                                contact_designation, email, phone, org_address, city, state, 
                                pincode, website, registration_no, registration_date, certificate_80g,
                                account_holder, account_number, bank_name, branch_name, ifsc_code, 
                                branch_city, password, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'approved')
            ''', (org_name, activity_name, org_description, contact_person, contact_designation,
                  email, phone, org_address, city, state, pincode, website, registration_no,
                  registration_date, certificate_80g, account_holder, account_number, bank_name,
                  branch_name, ifsc_code, branch_city, password))

            ngo_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO ngo_staff (ngo_id, name, email, password, role)
                VALUES (%s, %s, %s, %s, 'admin')
            ''', (ngo_id, f"{contact_person} (Admin)", email, password))

            cursor.execute('''
                INSERT INTO ngo_staff (ngo_id, name, email, password, role)
                VALUES (%s, %s, %s, %s, 'accountant')
            ''', (ngo_id, f"{contact_person} (Accountant)", email, password))

            mysql.connection.commit()
            cursor.close()

            flash('NGO registered successfully! You can login as both Admin and Accountant with the same email.',
                  'success')
            return redirect(url_for('ngo_login'))

        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')

    return render_template('ngo-register.html')


@app.route('/donor-logout')
def donor_logout():
    session.pop('donor_loggedin', None)
    session.pop('donor_id', None)
    session.pop('donor_name', None)
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('donor_login'))


@app.route('/ngo-logout')
def ngo_logout():
    session.pop('loggedin', None)
    session.pop('staff_id', None)
    session.pop('staff_name', None)
    session.pop('user_role', None)
    session.pop('ngo_id', None)
    session.pop('ngo_name', None)
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('ngo_login'))


@app.route('/donor-dashboard')
def donor_dashboard():
    if 'donor_loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM donors WHERE id = %s', (session['donor_id'],))
        donor = cursor.fetchone()

        cursor.execute('SELECT * FROM ngos WHERE status = "approved"')
        ngos = cursor.fetchall()

        cursor.execute('''
            SELECT n.*, COALESCE(SUM(d.amount), 0) as total_donations, 
                   COUNT(DISTINCT d.donor_id) as donor_count
            FROM ngos n 
            LEFT JOIN donations d ON n.id = d.ngo_id 
            WHERE n.status = 'approved'
            GROUP BY n.id 
            ORDER BY total_donations DESC 
            LIMIT 4
        ''')
        featured_ngos = cursor.fetchall()

        cursor.execute('''
            SELECT d.*, n.org_name as ngo_name 
            FROM donations d 
            JOIN ngos n ON d.ngo_id = n.id 
            WHERE d.donor_id = %s 
            ORDER BY d.donation_date DESC
        ''', (session['donor_id'],))
        donations = cursor.fetchall()

        cursor.execute('''
            SELECT SUM(amount) as total_donated, COUNT(DISTINCT ngo_id) as ngos_supported
            FROM donations 
            WHERE donor_id = %s AND YEAR(donation_date) = 2023
        ''', (session['donor_id'],))
        report_data = cursor.fetchone()

        cursor.execute('''
            SELECT n.activity_name as category, SUM(d.amount) as amount,
                   (SUM(d.amount) / (SELECT SUM(amount) FROM donations WHERE donor_id = %s)) * 100 as percentage
            FROM donations d
            JOIN ngos n ON d.ngo_id = n.id
            WHERE d.donor_id = %s
            GROUP BY n.activity_name
        ''', (session['donor_id'], session['donor_id']))
        category_breakdown = cursor.fetchall()

        cursor.close()

        return render_template('donor-dashboard.html',
                               donor=donor,
                               ngos=ngos,
                               featured_ngos=featured_ngos,
                               donations=donations,
                               total_donated=report_data['total_donated'] or 0,
                               ngos_supported=report_data['ngos_supported'] or 0,
                               tax_benefits=(report_data['total_donated'] or 0) * 0.3,
                               category_breakdown=category_breakdown)
    else:
        flash('Please login first!', 'error')
        return redirect(url_for('donor_login'))


def send_donation_email(to_email, donor_name, ngo_name, amount, donation_type, receipt_pdf_buffer=None):
    try:
        msg = Message(
            subject="🎉 Thank You for Your Donation!",
            sender=app.config['MAIL_USERNAME'],
            recipients=[to_email]
        )
        msg.body = f"""
Dear {donor_name},

Thank you for your generous {donation_type} donation of ₹{amount} to {ngo_name}.
Your support helps us continue making a positive impact.

Please find your donation receipt attached with this email.

With gratitude,
FundDonate Team
        """

        # Attach PDF receipt if provided
        if receipt_pdf_buffer:
            msg.attach(
                filename=f"Donation_Receipt_{donor_name.replace(' ', '_')}.pdf",
                content_type="application/pdf",
                data=receipt_pdf_buffer.getvalue()
            )

        mail.send(msg)
        print("✅ Donation confirmation email with receipt sent successfully.")
    except Exception as e:
        print("❌ Error sending donation email:", e)


def send_reminder_email(to_email, name, donation_type):
    subject = "FundDonate - Donation Reminder"
    body = f"""Hello {name},

This is a friendly reminder for your {donation_type} donation to your chosen NGO.

Thank you for supporting good causes!

- FundDonate Team"""
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to_email])
    msg.body = body
    try:
        mail.send(msg)
        print("✅ Reminder email sent successfully.")
    except Exception as e:
        print("❌ Reminder email failed:", e)


@app.route('/make_donation', methods=['POST'])
def make_donation():
    donor_id = session.get('donor_id')
    ngo_id = request.form['ngo_id']
    amount = request.form['amount']
    donation_type = request.form['donation_type']
    payment_method = request.form['payment_method']
    donation_date = request.form['donation_date']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        INSERT INTO donations (donor_id, ngo_id, amount, donation_type, payment_method, donation_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
    """, (donor_id, ngo_id, amount, donation_type, payment_method, datetime.now()))

    donation_id = cursor.lastrowid

    if donation_type in ['monthly', 'yearly']:
        next_date = datetime.strptime(donation_date, '%Y-%m-%d')
        if donation_type == 'monthly':
            next_date += timedelta(days=30)
        elif donation_type == 'yearly':
            next_date += timedelta(days=365)

        cursor.execute("SELECT fullname, email FROM donors WHERE id = %s", (donor_id,))
        donor = cursor.fetchone()

        scheduler.add_job(
            send_reminder_email,
            'date',
            run_date=next_date,
            args=[donor['email'], donor['fullname'], donation_type],
            id=f"reminder_{donation_id}_{next_date}"
        )

    mysql.connection.commit()
    cursor.close()

    flash("Donation created! Please scan the QR to complete your payment.", "info")
    return redirect(url_for('payment_qr', donation_id=donation_id))


@app.route('/payment_qr/<int:donation_id>')
def payment_qr(donation_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT d.*, n.org_name AS ngo_name
        FROM donations d
        JOIN ngos n ON d.ngo_id = n.id
        WHERE d.id = %s
    """, (donation_id,))
    donation = cursor.fetchone()
    cursor.close()

    return render_template('payment_qr.html', donation=donation)


@app.route('/confirm_payment/<int:donation_id>', methods=['POST'])
def confirm_payment(donation_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("UPDATE donations SET status = 'Completed' WHERE id = %s", (donation_id,))
    mysql.connection.commit()

    cursor.execute("""
        SELECT d.*, donors.fullname, donors.email, n.org_name AS ngo_name
        FROM donations d
        JOIN donors ON d.donor_id = donors.id
        JOIN ngos n ON d.ngo_id = n.id
        WHERE d.id = %s
    """, (donation_id,))
    donation = cursor.fetchone()
    cursor.close()

    if donation:
        # Generate PDF receipt
        pdf_buffer = generate_donation_receipt_pdf(donation)

        send_donation_email(
            to_email=donation['email'],
            donor_name=donation['fullname'],
            ngo_name=donation['ngo_name'],
            amount=donation['amount'],
            donation_type=donation['donation_type'],
            receipt_pdf_buffer=pdf_buffer
        )

        if donation['donation_type'] in ['monthly', 'yearly']:
            next_date = donation['donation_date']
            if isinstance(next_date, str):
                next_date = datetime.strptime(next_date, '%Y-%m-%d')

            if donation['donation_type'] == 'monthly':
                next_date += timedelta(days=30)
            elif donation['donation_type'] == 'yearly':
                next_date += timedelta(days=365)

            scheduler.add_job(
                send_reminder_email,
                'date',
                run_date=next_date,
                args=[donation['email'], donation['fullname'], donation['donation_type']],
                id=f"reminder_{donation_id}_{next_date}"
            )

    flash('✅ Thank you! Your payment has been received. A confirmation email with receipt has been sent.', 'success')
    return redirect(url_for('donor_dashboard'))


def generate_donation_receipt_pdf(donation_data):
    """Generate donation receipt PDF and return as buffer"""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    pdf.setTitle("Donation Receipt")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 100, "DONATION RECEIPT")

    # Organization Info
    pdf.setFont("Helvetica", 10)
    pdf.drawString(100, height - 140, "FundDonate Platform")
    pdf.drawString(100, height - 155, "Email: support@funddonate.org")

    # Receipt Details
    y = height - 200
    details = [
        ("Receipt No:", f"REC{donation_data['id']:06d}"),
        ("Date:", datetime.now().strftime('%d/%m/%Y')),
        ("Donor Name:", donation_data['fullname']),
        ("NGO Name:", donation_data['ngo_name']),
        ("Amount:", f"₹{donation_data['amount']:.2f}"),
        ("Donation Type:", donation_data['donation_type'].title()),
        ("Payment Method:", donation_data['payment_method'].title()),
        ("Status:", "Completed")
    ]

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(100, y, "Transaction Details:")
    y -= 30

    pdf.setFont("Helvetica", 10)
    for label, value in details:
        pdf.drawString(100, y, label)
        pdf.drawString(200, y, value)
        y -= 20

    # Thank you message
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, 200, "Thank You for Your Generous Support!")

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(width / 2, 180, "This receipt is computer generated and does not require signature.")

    pdf.save()
    buffer.seek(0)
    return buffer

@app.route('/download-receipts')
def download_receipts():
    if 'donor_loggedin' not in session:
        return redirect(url_for('donor_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT d.*, n.org_name AS ngo_name
        FROM donations d
        JOIN ngos n ON d.ngo_id = n.id
        WHERE d.donor_id = %s
        ORDER BY d.donation_date DESC
    ''', (session['donor_id'],))
    receipts = cursor.fetchall()
    cursor.close()

    return render_template('download-receipts.html', receipts=receipts)


@app.route('/download-receipt/<int:donation_id>')
def download_receipt(donation_id):
    if 'donor_loggedin' not in session:
        return redirect(url_for('donor_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT 
            d.*, 
            n.org_name AS ngo_name, n.org_address, n.registration_no,
            don.fullname AS donor_full_name, don.address, don.city, don.taluka, don.district, 
            don.state, don.country, don.aadhar_no, don.pan_no
        FROM donations d
        JOIN ngos n ON d.ngo_id = n.id
        JOIN donors don ON d.donor_id = don.id
        WHERE d.id = %s
    ''', (donation_id,))
    donation = cursor.fetchone()
    cursor.close()

    if not donation:
        return "Donation not found", 404

    if donation['donation_date']:
        try:
            donation['donation_date'] = datetime.strptime(str(donation['donation_date']), "%Y-%m-%d")
        except ValueError:
            pass

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("Donation Receipt")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(300, 800, "DONATION RECEIPT")

    pdf.setFont("Helvetica", 12)
    y = 770

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "NGO Details:")
    pdf.setFont("Helvetica", 12)
    y -= 20
    pdf.drawString(60, y, f"Name: {donation['ngo_name']}")
    y -= 15
    pdf.drawString(60, y, f"Address: {donation['org_address']}")
    y -= 15
    pdf.drawString(60, y, f"Registration No: {donation['registration_no']}")

    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Donor Details:")
    pdf.setFont("Helvetica", 12)
    y -= 15
    pdf.drawString(60, y, f"Name: {donation['donor_full_name']}")
    y -= 15
    pdf.drawString(60, y, f"Address: {donation['address']}, {donation['city']}, {donation['taluka']},")
    y -= 15
    pdf.drawString(60, y, f"{donation['district']}, {donation['state']}, {donation['country']}")
    y -= 15
    pdf.drawString(60, y, f"Aadhar No: {donation['aadhar_no']}")
    y -= 15
    pdf.drawString(60, y, f"PAN No: {donation['pan_no']}")

    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Donation Details:")
    pdf.setFont("Helvetica", 12)
    y -= 20
    pdf.drawString(60, y, f"Donation Type: {donation['donation_type']}")
    y -= 15
    pdf.drawString(60, y, f"Payment Method: {donation['payment_method']}")
    y -= 15
    pdf.drawString(60, y, f"Amount Donated: {donation['amount']} Rs")
    y -= 15
    pdf.drawString(60, y,
                   f"Date: {donation['donation_date'].strftime('%d %b %Y') if donation['donation_date'] is not None else 'Date not available'}")
    y -= 15
    pdf.drawString(60, y, f"Status: {donation['status']}")

    y -= 40
    pdf.setFont("Helvetica-Oblique", 12)
    pdf.drawString(50, y, "We sincerely thank you for your generous contribution.")
    y -= 15
    pdf.drawString(50, y, "This receipt serves as an official acknowledgment of your donation.")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    filename = f"Receipt_{donation['id']}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


@app.route('/donation-history')
def donation_history():
    if 'donor_loggedin' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('donor_login'))

    filter_type = request.args.get('filter', 'all')
    selected_month = request.args.get('month')
    donor_id = session['donor_id']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    query = '''
        SELECT d.*, n.org_name AS ngo_name
        FROM donations d
        JOIN ngos n ON d.ngo_id = n.id
        WHERE d.donor_id = %s
    '''
    params = [donor_id]

    if filter_type == 'monthly' and selected_month:
        year, month = selected_month.split('-')
        query += ' AND YEAR(d.donation_date) = %s AND MONTH(d.donation_date) = %s'
        params.extend([year, month])
    elif filter_type == 'yearly':
        one_year_ago = datetime.now() - timedelta(days=365)
        query += ' AND d.donation_date >= %s'
        params.append(one_year_ago)

    query += ' ORDER BY d.donation_date DESC'
    cursor.execute(query, tuple(params))
    donations = cursor.fetchall()

    return render_template('donation-history.html',
                           donations=donations,
                           filter_type=filter_type,
                           selected_month=selected_month)


@app.route('/ngo-login', methods=['GET', 'POST'])
def ngo_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(''' 
            SELECT ns.*, n.org_name, n.id as ngo_id
            FROM ngo_staff ns 
            JOIN ngos n ON ns.ngo_id = n.id 
            WHERE ns.email = %s AND ns.password = %s AND ns.role = %s
        ''', (email, password, role))
        staff = cursor.fetchone()

        if staff:
            session['loggedin'] = True
            session['staff_id'] = staff['id']
            session['staff_name'] = staff['name']
            session['user_role'] = staff['role']
            session['ngo_id'] = staff['ngo_id']
            session['ngo_name'] = staff['org_name']

            flash(f'{role.capitalize()} login successful!', 'success')

            if role == 'admin':
                return redirect(url_for('ngo_admin_dashboard'))
            else:
                return redirect(url_for('ngo_accountant_dashboard'))
        else:
            flash('Invalid email, password or role mismatch!', 'error')

        cursor.close()

    return render_template('ngo-login.html')


@app.route('/ngo-admin-dashboard')
def ngo_admin_dashboard():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']

    # Fetch NGO details
    cursor.execute("SELECT * FROM ngos WHERE id = %s", (ngo_id,))
    ngo = cursor.fetchone()

    # ✅ ADDED: Get donation statistics
    cursor.execute("""
        SELECT 
            COALESCE(SUM(amount), 0) as total_donations,
            COUNT(*) as donation_count
        FROM donations 
        WHERE ngo_id = %s AND status = 'Completed'
    """, (ngo_id,))
    donation_stats = cursor.fetchone()

    # ✅ ADDED: Get expenditure statistics
    cursor.execute("""
        SELECT 
            COALESCE(SUM(amount_spent), 0) as total_expenditures,
            COUNT(*) as expense_count
        FROM expenditures 
        WHERE ngo_id = %s
    """, (ngo_id,))
    expense_stats = cursor.fetchone()

    # ✅ ADDED: Calculate remaining amount
    total_donations = donation_stats['total_donations']
    total_expenditures = expense_stats['total_expenditures']
    remaining_amount = total_donations - total_expenditures

    # ✅ ADDED: Get recent donations
    cursor.execute("""
        SELECT d.*, don.fullname as donor_name
        FROM donations d
        JOIN donors don ON d.donor_id = don.id
        WHERE d.ngo_id = %s
        ORDER BY d.donation_date DESC
        LIMIT 5
    """, (ngo_id,))
    recent_donations = cursor.fetchall()

    # Existing budget requests data (keep as is)
    cursor.execute("""
        SELECT br.*, bp.program_name, s.name AS accountant_name,
               COALESCE(br.approved_amount, 0) AS approved_amount,
               CASE
                   WHEN br.status = 'approved' THEN 'Approved'
                   WHEN br.status = 'rejected' THEN 'Rejected'
                   WHEN br.status = 'partially_approved' THEN 'Partially Approved'
                   ELSE 'Pending'
               END AS display_status
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        JOIN ngo_staff s ON br.requested_by = s.id
        WHERE br.ngo_id = %s AND br.status = 'pending'
        ORDER BY br.id DESC
    """, (ngo_id,))
    pending_requests = cursor.fetchall()

    cursor.execute("""
        SELECT br.*, bp.program_name, s.name AS accountant_name,
               COALESCE(br.approved_amount, 0) AS approved_amount,
               CASE
                   WHEN br.status = 'approved' THEN 'Approved'
                   WHEN br.status = 'rejected' THEN 'Rejected'
                   WHEN br.status = 'partially_approved' THEN 'Partially Approved'
                   ELSE 'Pending'
               END AS display_status
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        JOIN ngo_staff s ON br.requested_by = s.id
        WHERE br.ngo_id = %s
        ORDER BY br.id DESC
    """, (ngo_id,))
    all_requests = cursor.fetchall()

    # Pending budget count
    cursor.execute("SELECT COUNT(*) AS pending_count FROM budget_requests WHERE ngo_id = %s AND status='pending'",
                   (ngo_id,))
    pending_count = cursor.fetchone()['pending_count']

    # Approved budget total
    cursor.execute(
        "SELECT COALESCE(SUM(approved_amount), 0) AS total_approved FROM budget_requests WHERE ngo_id=%s AND status IN ('approved','partially_approved')",
        (ngo_id,))
    total_approved = cursor.fetchone()['total_approved']

    # ✅ ADDED BACK: expense_summary for template compatibility
    expense_summary = {
        'total_spent': total_expenditures,
        'expense_count': expense_stats['expense_count']
    }

    cursor.close()

    return render_template("ngo-admin-dashboard.html",
                           ngo=ngo,
                           pending_requests=pending_requests,
                           all_requests=all_requests,
                           total_donations=total_donations,
                           total_expenditures=total_expenditures,
                           remaining_amount=remaining_amount,
                           recent_donations=recent_donations,
                           donation_count=donation_stats['donation_count'],
                           expense_count=expense_stats['expense_count'],
                           pending_count=pending_count,
                           total_approved=total_approved,
                           expense_summary=expense_summary)  # ✅ Added back


@app.route('/ngo-accountant-dashboard')
def ngo_accountant_dashboard():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']
    staff_id = session['staff_id']

    cursor.execute("SELECT * FROM ngos WHERE id = %s", (ngo_id,))
    ngo = cursor.fetchone()

    # ✅ ADDED: Get donation statistics
    cursor.execute("""
        SELECT 
            COALESCE(SUM(amount), 0) as total_donations,
            COUNT(*) as donation_count
        FROM donations 
        WHERE ngo_id = %s AND status = 'Completed'
    """, (ngo_id,))
    donation_stats = cursor.fetchone()

    # ✅ ADDED: Get expenditure statistics
    cursor.execute("""
        SELECT 
            COALESCE(SUM(amount_spent), 0) as total_expenditures,
            COUNT(*) as expense_count
        FROM expenditures 
        WHERE ngo_id = %s AND recorded_by = %s
    """, (ngo_id, staff_id))
    expense_stats = cursor.fetchone()

    # ✅ ADDED: Calculate remaining amount
    total_donations = donation_stats['total_donations']
    total_expenditures = expense_stats['total_expenditures'] or 0
    remaining_amount = total_donations - total_expenditures

    # ✅ ADDED: Get recent donations
    cursor.execute("""
        SELECT d.*, don.fullname as donor_name
        FROM donations d
        JOIN donors don ON d.donor_id = don.id
        WHERE d.ngo_id = %s
        ORDER BY d.donation_date DESC
        LIMIT 5
    """, (ngo_id,))
    recent_donations = cursor.fetchall()

    # Existing my budget requests (keep as is)
    cursor.execute("""
        SELECT br.*, bp.program_name,
               CASE 
                   WHEN br.status='approved' THEN 'Approved'
                   WHEN br.status='rejected' THEN 'Rejected'
                   WHEN br.status='partially_approved' THEN 'Partially Approved'
                   ELSE 'Pending'
               END AS display_status
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        WHERE br.ngo_id=%s AND br.requested_by=%s
        ORDER BY br.id DESC
    """, (ngo_id, staff_id))
    my_requests = cursor.fetchall()

    cursor.close()

    return render_template("ngo-accountant-dashboard.html",
                           ngo=ngo,
                           my_requests=my_requests,
                           total_donations=total_donations,
                           total_expenditures=total_expenditures,
                           remaining_amount=remaining_amount,
                           recent_donations=recent_donations,
                           donation_count=donation_stats['donation_count'],
                           expense_count=expense_stats['expense_count'] or 0)


@app.route('/admin/create-master-budget', methods=['GET', 'POST'])
def create_master_budget():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    if request.method == 'POST':
        budget_name = request.form['budget_name']
        total_amount = float(request.form['total_amount'])
        fiscal_year = request.form['fiscal_year']
        description = request.form['description']

        cursor = mysql.connection.cursor()

        try:
            cursor.execute('''
                INSERT INTO master_budgets (budget_name, total_amount, fiscal_year, description, created_by, ngo_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (budget_name, total_amount, fiscal_year, description, session['staff_id'], session['ngo_id']))

            master_budget_id = cursor.lastrowid

            programs = request.form.getlist('program_name[]')
            program_amounts = request.form.getlist('program_amount[]')

            for i in range(len(programs)):
                if programs[i].strip():
                    cursor.execute('''
                        INSERT INTO budget_programs (master_budget_id, program_name, allocated_amount)
                        VALUES (%s, %s, %s)
                    ''', (master_budget_id, programs[i].strip(), float(program_amounts[i])))

            mysql.connection.commit()
            flash('Master budget created successfully!', 'success')
            return redirect(url_for('ngo_admin_dashboard'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error creating budget: {str(e)}', 'error')
        finally:
            cursor.close()

    return render_template('admin/create_master_budget.html')


@app.route('/admin/budget-requests')
def admin_budget_requests():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']

    # Get ONLY pending requests (these will disappear after approval/rejection)
    cursor.execute('''
        SELECT br.*, bp.program_name, s.name as accountant_name
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        JOIN ngo_staff s ON br.requested_by = s.id
        WHERE br.ngo_id = %s AND br.status = 'pending'
        ORDER BY br.request_date DESC
    ''', (ngo_id,))
    pending_requests = cursor.fetchall()

    cursor.close()

    print(f"🔧 DEBUG: Found {len(pending_requests)} pending requests")
    for req in pending_requests:
        print(f"🔧 DEBUG: Request {req['id']} - Status: {req['status']}")

    return render_template('admin/budget_requests.html', requests=pending_requests)


@app.route('/admin/approve-request/<int:request_id>', methods=['POST'])
def approve_budget_request(request_id):
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    print(f"🔧 DEBUG: Starting approval process for request {request_id}")
    print(f"🔧 DEBUG: Form data received: {dict(request.form)}")

    action = request.form.get('action')
    approval_notes = request.form.get('approval_notes', '')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        if action == 'approve':
            print("🔧 DEBUG: Processing APPROVE action")
            # Get requested amount and approve fully
            cursor.execute('SELECT requested_amount, program_id FROM budget_requests WHERE id = %s', (request_id,))
            result = cursor.fetchone()
            if result:
                requested_amount = result['requested_amount']
                program_id = result['program_id']

                cursor.execute('''
                    UPDATE budget_requests 
                    SET status = 'approved', approved_amount = %s, 
                        approved_by = %s, approval_date = %s, approval_notes = %s
                    WHERE id = %s
                ''', (requested_amount, session['staff_id'], datetime.now().date(), approval_notes, request_id))

                # ✅ ADDED: Deduct from budget_programs.allocated_amount
                cursor.execute('''
                    UPDATE budget_programs 
                    SET allocated_amount = allocated_amount - %s 
                    WHERE id = %s
                ''', (requested_amount, program_id))

                flash('Request fully approved!', 'success')
                print("DEBUG: Request approved successfully")

        elif action == 'partial':
            print("🔧 DEBUG: Processing PARTIAL action")
            approved_amount = float(request.form.get('approved_amount', 0))

            # Get program_id for deduction
            cursor.execute('SELECT program_id FROM budget_requests WHERE id = %s', (request_id,))
            program_id = cursor.fetchone()['program_id']

            cursor.execute('''
                UPDATE budget_requests 
                SET status = 'partially_approved', approved_amount = %s,
                    approved_by = %s, approval_date = %s, approval_notes = %s
                WHERE id = %s
            ''', (approved_amount, session['staff_id'], datetime.now().date(), approval_notes, request_id))

            # ✅ ADDED: Deduct from budget_programs.allocated_amount
            cursor.execute('''
                UPDATE budget_programs 
                SET allocated_amount = allocated_amount - %s 
                WHERE id = %s
            ''', (approved_amount, program_id))

            flash('Request partially approved!', 'success')
            print("DEBUG: Partial approval successful")

        elif action == 'reject':
            print("🔧 DEBUG: Processing REJECT action")
            cursor.execute('''
                UPDATE budget_requests 
                SET status = 'rejected', approved_amount = 0,
                    approved_by = %s, approval_date = %s, approval_notes = %s
                WHERE id = %s
            ''', (session['staff_id'], datetime.now().date(), approval_notes, request_id))
            flash('Request rejected!', 'success')
            print("DEBUG: Request rejected successfully")

        else:
            print(f"DEBUG: Unknown action: {action}")
            flash('Unknown action!', 'error')

        mysql.connection.commit()

    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error updating request: {str(e)}', 'error')
        print(f"DEBUG Error: {str(e)}")
    finally:
        cursor.close()

    return redirect(url_for('admin_budget_requests'))


@app.route('/accountant/request-funds', methods=['GET', 'POST'])
def request_funds():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']

    if request.method == 'POST':
        program_id = request.form['program_id']
        requested_amount = float(request.form['requested_amount'])
        purpose = request.form['purpose']
        request_date = request.form['request_date']

        try:
            # ✅ ADDED: Get current allocated amount (after any deductions)
            cursor.execute('SELECT allocated_amount, program_name FROM budget_programs WHERE id = %s', (program_id,))
            program_data = cursor.fetchone()

            if not program_data:
                flash('Selected program not found!', 'error')
                return redirect(url_for('request_funds'))

            current_allocated = program_data['allocated_amount']
            program_name = program_data['program_name']

            # ✅ ADDED: Check against current allocated amount
            if requested_amount > current_allocated:
                flash(
                    f'Requested amount (₹{requested_amount}) exceeds current available amount (₹{current_allocated}) for program "{program_name}"!',
                    'error')
                return redirect(url_for('request_funds'))

            cursor.execute('''
                INSERT INTO budget_requests (program_id, requested_by, requested_amount, purpose, request_date, ngo_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (program_id, session['staff_id'], requested_amount, purpose, request_date, ngo_id))

            mysql.connection.commit()
            flash('Fund request submitted successfully!', 'success')
            return redirect(url_for('ngo_accountant_dashboard'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error submitting request: {str(e)}', 'error')

    # ✅ ADDED: Only show programs that still have allocated amount > 0
    cursor.execute('''
        SELECT bp.*, mb.budget_name 
        FROM budget_programs bp
        JOIN master_budgets mb ON bp.master_budget_id = mb.id
        WHERE mb.ngo_id = %s AND bp.allocated_amount > 0
    ''', (ngo_id,))
    programs = cursor.fetchall()

    cursor.close()
    return render_template('accountant/request_funds.html', programs=programs)


@app.route('/accountant/approved-requests')
def approved_requests():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']
    staff_id = session['staff_id']

    cursor.execute('''
        SELECT br.*, bp.program_name, mb.budget_name
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        JOIN master_budgets mb ON bp.master_budget_id = mb.id
        WHERE br.ngo_id = %s AND br.requested_by = %s AND br.status IN ('approved', 'partially_approved')
        ORDER BY br.approval_date DESC
    ''', (ngo_id, staff_id))

    approved_requests = cursor.fetchall()
    cursor.close()

    return render_template('accountant/approved_requests.html', requests=approved_requests)


import os
from werkzeug.utils import secure_filename

# Configure upload settings
app.config['UPLOAD_FOLDER'] = 'static/uploads/receipts'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/accountant-add-expenditure', methods=['GET', 'POST'])
def accountant_add_expenditure():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']
    staff_id = session['staff_id']

    # Get approved budgets and calculate remaining amounts
    cursor.execute('''
        SELECT br.id, bp.program_name, br.approved_amount, br.status
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        WHERE br.ngo_id = %s 
        AND br.requested_by = %s 
        AND br.status IN ('approved', 'partially_approved')
    ''', (ngo_id, staff_id))

    approved_budgets = cursor.fetchall()

    # Calculate remaining amounts for each budget
    available_budgets = []
    for budget in approved_budgets:
        cursor.execute('''
            SELECT COALESCE(SUM(amount_spent), 0) as total_spent 
            FROM expenditures 
            WHERE ngo_id = %s AND program_name = %s
        ''', (ngo_id, budget['program_name']))

        spent = cursor.fetchone()['total_spent']
        remaining = budget['approved_amount'] - spent

        if remaining > 0:
            budget['remaining_amount'] = remaining
            available_budgets.append(budget)

    if request.method == 'POST':
        program_name = request.form['program_name']
        amount_spent = float(request.form['amount_spent'])
        spending_date = request.form['spending_date']
        paid_to = request.form['paid_to']
        payment_method = request.form['payment_method']
        location = request.form['location']
        receipt_number = request.form['receipt_number']
        details = request.form['details']
        notes = request.form['notes']

        # Handle file upload
        receipt_filename = None
        if 'receipt_file' in request.files:
            file = request.files['receipt_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                receipt_filename = f"{timestamp}_{filename}"

                # Create upload directory if it doesn't exist
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                # Save file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
                file.save(file_path)

        # Check if amount doesn't exceed remaining budget
        cursor.execute('''
            SELECT COALESCE(SUM(amount_spent), 0) as total_spent 
            FROM expenditures 
            WHERE ngo_id = %s AND program_name = %s
        ''', (ngo_id, program_name))

        spent = cursor.fetchone()['total_spent']

        cursor.execute('''
            SELECT approved_amount FROM budget_requests br
            JOIN budget_programs bp ON br.program_id = bp.id
            WHERE br.ngo_id = %s AND bp.program_name = %s
        ''', (ngo_id, program_name))

        approved_amount = cursor.fetchone()['approved_amount']
        remaining = approved_amount - spent

        if amount_spent > remaining:
            flash(f"Amount exceeds remaining budget! Available: ₹{remaining}", 'error')
            return redirect(url_for('accountant_add_expenditure'))

        # Insert expenditure with receipt file
        cursor.execute("""
            INSERT INTO expenditures (
                ngo_id, program_name, amount_spent, spending_date, 
                paid_to, payment_method, location, receipt_number, receipt_file,
                details, notes, recorded_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ngo_id, program_name, amount_spent, spending_date,
            paid_to, payment_method, location, receipt_number, receipt_filename,
            details, notes, session['staff_id']
        ))

        mysql.connection.commit()
        cursor.close()

        flash("Expenditure recorded successfully with receipt!", "success")
        return redirect(url_for('ngo_accountant_dashboard'))

    return render_template('accountant-add-expenditure.html', available_budgets=available_budgets)


@app.route('/ngo-accountant/expenditures')
def accountant_view_expenditures():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get all expenditures with budget info
    cursor.execute("SELECT * FROM expenditures WHERE ngo_id = %s ORDER BY spending_date DESC", (ngo_id,))
    expenditures = cursor.fetchall()

    # Calculate budget info for each expenditure
    for exp in expenditures:
        # Get approved amount for this program
        cursor.execute("""
            SELECT approved_amount 
            FROM budget_requests br
            JOIN budget_programs bp ON br.program_id = bp.id
            WHERE br.ngo_id = %s AND bp.program_name = %s
        """, (ngo_id, exp['program_name']))

        budget_data = cursor.fetchone()
        if budget_data:
            approved_amount = budget_data['approved_amount']
            exp['approved_amount'] = approved_amount

            # Calculate total spent BEFORE this expenditure
            cursor.execute("""
                SELECT COALESCE(SUM(amount_spent), 0) as spent_before 
                FROM expenditures 
                WHERE ngo_id = %s AND program_name = %s AND id < %s
            """, (ngo_id, exp['program_name'], exp['id']))

            spent_before = cursor.fetchone()['spent_before']

            # Calculate remaining after this expenditure
            exp['remaining_after'] = approved_amount - (spent_before + exp['amount_spent'])
        else:
            exp['approved_amount'] = 0
            exp['remaining_after'] = 0

    cursor.close()

    return render_template('view_expenditures.html',
                           expenditures=expenditures,
                           user_role='accountant')


@app.route('/ngo-admin/expenditures')
def admin_view_expenditures():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get all expenditures with NGO name
    cursor.execute("""
        SELECT e.*, n.org_name AS ngo_name
        FROM expenditures e
        LEFT JOIN ngos n ON e.ngo_id = n.id
        WHERE e.ngo_id = %s
        ORDER BY e.spending_date DESC
    """, (ngo_id,))

    expenditures = cursor.fetchall()

    # Calculate budget info for each expenditure
    for exp in expenditures:
        # Get approved amount for this program
        cursor.execute("""
            SELECT approved_amount 
            FROM budget_requests br
            JOIN budget_programs bp ON br.program_id = bp.id
            WHERE br.ngo_id = %s AND bp.program_name = %s
        """, (ngo_id, exp['program_name']))

        budget_data = cursor.fetchone()
        if budget_data:
            approved_amount = budget_data['approved_amount']
            exp['approved_amount'] = approved_amount

            # Calculate total spent BEFORE this expenditure
            cursor.execute("""
                SELECT COALESCE(SUM(amount_spent), 0) as spent_before 
                FROM expenditures 
                WHERE ngo_id = %s AND program_name = %s AND id < %s
            """, (ngo_id, exp['program_name'], exp['id']))

            spent_before = cursor.fetchone()['spent_before']

            # Calculate remaining after this expenditure
            exp['remaining_after'] = approved_amount - (spent_before + exp['amount_spent'])
        else:
            exp['approved_amount'] = 0
            exp['remaining_after'] = 0

    cursor.close()

    return render_template('view_expenditures.html',
                           expenditures=expenditures,
                           user_role='admin')


def generate_pdf(expenditures, role='accountant'):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    pdf.setTitle("Expenditure Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 40, "Expenditure Report")

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 65, f"Role: {role.capitalize()}")

    pdf.setFont("Helvetica", 8)
    y = height - 90

    headers = ["ID"]
    if role == 'admin':
        headers.append("NGO Name")
    headers += [
        "Program Name", "Approved Budget (Rs)", "This Expense (Rs)",
        "Remaining After This (Rs)", "Spending Date", "Paid To",
        "Payment Method", "Location", "Receipt No.", "Details"
    ]

    col_widths = [30]
    if role == 'admin':
        col_widths.append(70)

    col_widths += [
        80, 70, 70, 70, 70, 80, 70, 70, 70, 120
    ]

    pdf.setFillColor(colors.HexColor('#2c3e50'))
    pdf.rect(20, y - 5, width - 40, 20, fill=1, stroke=0)
    pdf.setFillColor(colors.white)

    x = 25
    for i, header in enumerate(headers):
        pdf.drawString(x, y, header)
        x += col_widths[i]

    y -= 25
    pdf.setFillColor(colors.black)

    for idx, exp in enumerate(expenditures):
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 8)
            y = height - 50

        if idx % 2 == 0:
            pdf.setFillColor(colors.HexColor('#f8f9fa'))
            pdf.rect(20, y - 3, width - 40, 15, fill=1, stroke=0)
        pdf.setFillColor(colors.black)

        x = 25
        row_data = [str(exp.get('id', '-'))]

        if role == 'admin':
            row_data.append(exp.get('ngo_name', '-'))

        # Calculate remaining budget
        approved_budget = exp.get('approved_budget', 0) or 0
        this_expense = exp.get('amount_spent', 0) or 0
        remaining_after_this = approved_budget - this_expense

        row_data += [
            exp.get('program_name', '-'),
            f"Rs{approved_budget:.2f}",
            f"Rs{this_expense:.2f}",
            f"Rs{remaining_after_this:.2f}",
            exp['spending_date'].strftime('%d %b %Y') if exp.get('spending_date') else '-',
            exp.get('paid_to', '-'),
            exp.get('payment_method', '-'),
            exp.get('location', '-'),
            exp.get('receipt_number', '-'),
            exp.get('details', '-')
        ]

        for i, item in enumerate(row_data):
            text = str(item)
            if len(text) > 20:
                text = text[:17] + '...'
            pdf.drawString(x, y, text)
            x += col_widths[i]

        y -= 18

    pdf.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Expenditure_Report_{role}.pdf",
        mimetype='application/pdf'
    )
@app.route('/download-expenditure-report/admin')
def download_expenditure_report_admin():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']

    cursor.execute("""
        SELECT e.*, n.org_name as ngo_name 
        FROM expenditures e 
        JOIN ngos n ON e.ngo_id = n.id
        WHERE e.ngo_id = %s
        ORDER BY e.spending_date DESC
    """, (ngo_id,))
    expenditures = cursor.fetchall()
    return generate_pdf(expenditures, role='admin')


@app.route('/download-expenditure-report/accountant')
def download_expenditure_report_accountant():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT * FROM expenditures
        WHERE ngo_id = %s
        ORDER BY spending_date DESC
    """, (ngo_id,))
    expenditures = cursor.fetchall()
    return generate_pdf(expenditures, role='accountant')


@app.route('/admin/all-requests')
def admin_all_requests():
    """View all requests (for debugging)"""
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']

    # Get ALL requests regardless of status
    cursor.execute('''
        SELECT br.*, bp.program_name, s.name as accountant_name
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        JOIN ngo_staff s ON br.requested_by = s.id
        WHERE br.ngo_id = %s
        ORDER BY br.request_date DESC
    ''', (ngo_id,))
    all_requests = cursor.fetchall()

    cursor.close()

    return render_template('admin/all_requests.html', requests=all_requests)

@app.route('/download-consolidated-pdf')
def download_consolidated_pdf():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    month = request.args.get('month')

    # Copy ALL the data fetching logic from your admin_monthly_consolidated route
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']

    try:
        year, month_num = month.split('-')
        year = int(year)
        month_num = int(month_num)
    except:
        year = datetime.now().year
        month_num = datetime.now().month
        month = f"{year}-{month_num:02d}"

    # Calculate date ranges
    start_date = datetime(year, month_num, 1)
    if month_num == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month_num + 1, 1) - timedelta(days=1)

    # Get monthly donations
    cursor.execute('''
        SELECT 
            COALESCE(SUM(amount), 0) as total_deposits,
            COUNT(*) as deposit_count
        FROM donations 
        WHERE ngo_id = %s 
        AND status = 'Completed'
        AND donation_date BETWEEN %s AND %s
    ''', (ngo_id, start_date.date(), end_date.date()))
    donation_data = cursor.fetchone()

    # Get monthly expenditures
    cursor.execute('''
        SELECT 
            COALESCE(SUM(amount_spent), 0) as total_expenditures,
            COUNT(*) as expense_count
        FROM expenditures 
        WHERE ngo_id = %s 
        AND spending_date BETWEEN %s AND %s
    ''', (ngo_id, start_date.date(), end_date.date()))
    expense_data = cursor.fetchone()

    # Get monthly budget approvals
    cursor.execute('''
        SELECT 
            COALESCE(SUM(approved_amount), 0) as total_approved,
            COUNT(*) as approval_count
        FROM budget_requests 
        WHERE ngo_id = %s 
        AND approval_date BETWEEN %s AND %s
        AND status IN ('approved', 'partially_approved')
    ''', (ngo_id, start_date.date(), end_date.date()))
    approval_data = cursor.fetchone()

    # Get opening balance (previous month's closing)
    prev_month = start_date - timedelta(days=1)
    cursor.execute('''
        SELECT 
            (COALESCE(SUM(CASE WHEN d.status = 'Completed' THEN d.amount ELSE 0 END), 0) - 
             COALESCE(SUM(e.amount_spent), 0)) as closing_balance
        FROM donations d
        LEFT JOIN expenditures e ON d.ngo_id = e.ngo_id 
            AND e.spending_date <= %s
        WHERE d.ngo_id = %s 
        AND d.donation_date <= %s
    ''', (prev_month.date(), ngo_id, prev_month.date()))

    opening_balance_result = cursor.fetchone()
    opening_balance = opening_balance_result['closing_balance'] if opening_balance_result else 0

    # Calculate current values
    total_deposits = donation_data['total_deposits'] or 0
    total_expenditures = expense_data['total_expenditures'] or 0
    total_approved = approval_data['total_approved'] or 0

    # Calculate balances
    available_balance = opening_balance + total_deposits - total_expenditures
    remaining_budget = total_approved - total_expenditures

    # Get monthly transactions detail
    cursor.execute('''
        SELECT 
            'Donation' as type,
            d.donation_date as date,
            d.amount as amount,
            CONCAT('From: ', don.fullname) as description,
            d.donation_type as category,
            d.status as status
        FROM donations d
        JOIN donors don ON d.donor_id = don.id
        WHERE d.ngo_id = %s 
        AND d.donation_date BETWEEN %s AND %s
        AND d.status = 'Completed'

        UNION ALL

        SELECT 
            'Expenditure' as type,
            e.spending_date as date,
            e.amount_spent as amount,
            CONCAT('Paid to: ', e.paid_to, ' - ', e.details) as description,
            e.program_name as category,
            'Completed' as status
        FROM expenditures e
        WHERE e.ngo_id = %s 
        AND e.spending_date BETWEEN %s AND %s

        UNION ALL

        SELECT 
            'Budget Approval' as type,
            br.approval_date as date,
            br.approved_amount as amount,
            CONCAT('Approved for: ', bp.program_name) as description,
            br.status as category,
            'Completed' as status
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        WHERE br.ngo_id = %s 
        AND br.approval_date BETWEEN %s AND %s
        AND br.status IN ('approved', 'partially_approved')

        ORDER BY date DESC
    ''', (ngo_id, start_date.date(), end_date.date(),
          ngo_id, start_date.date(), end_date.date(),
          ngo_id, start_date.date(), end_date.date()))

    transactions = cursor.fetchall()
    cursor.close()

    # Prepare data for PDF
    consolidated_data = {
        'opening_balance': float(opening_balance),
        'total_deposits': float(total_deposits),
        'total_expenditures': float(total_expenditures),
        'available_balance': float(available_balance),
        'total_approved': float(total_approved),
        'remaining_budget': float(remaining_budget),
        'deposit_count': donation_data['deposit_count'] or 0,
        'expense_count': expense_data['expense_count'] or 0,
        'approval_count': approval_data['approval_count'] or 0,
        'transactions': transactions
    }

    month_name = start_date.strftime('%B %Y')

    # Generate PDF
    return generate_consolidated_pdf(consolidated_data, month_name)

@app.route('/admin/monthly-consolidated')
def admin_monthly_consolidated():  # Keep original name
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ngo_id = session['ngo_id']

    # Get selected month and year from request (default to current month)
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    try:
        year, month = selected_month.split('-')
        year = int(year)
        month = int(month)
    except:
        year = datetime.now().year
        month = datetime.now().month
        selected_month = f"{year}-{month:02d}"

    # Calculate date ranges
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    # Get monthly donations
    cursor.execute('''
        SELECT 
            COALESCE(SUM(amount), 0) as total_deposits,
            COUNT(*) as deposit_count
        FROM donations 
        WHERE ngo_id = %s 
        AND status = 'Completed'
        AND donation_date BETWEEN %s AND %s
    ''', (ngo_id, start_date.date(), end_date.date()))
    donation_data = cursor.fetchone()

    # Get monthly expenditures
    cursor.execute('''
        SELECT 
            COALESCE(SUM(amount_spent), 0) as total_expenditures,
            COUNT(*) as expense_count
        FROM expenditures 
        WHERE ngo_id = %s 
        AND spending_date BETWEEN %s AND %s
    ''', (ngo_id, start_date.date(), end_date.date()))
    expense_data = cursor.fetchone()

    # Get monthly budget approvals
    cursor.execute('''
        SELECT 
            COALESCE(SUM(approved_amount), 0) as total_approved,
            COUNT(*) as approval_count
        FROM budget_requests 
        WHERE ngo_id = %s 
        AND approval_date BETWEEN %s AND %s
        AND status IN ('approved', 'partially_approved')
    ''', (ngo_id, start_date.date(), end_date.date()))
    approval_data = cursor.fetchone()

    # Get opening balance (previous month's closing) - FIXED
    prev_month = start_date - timedelta(days=1)
    cursor.execute('''
        SELECT 
            (COALESCE(SUM(CASE WHEN d.status = 'Completed' THEN d.amount ELSE 0 END), 0) - 
             COALESCE(SUM(e.amount_spent), 0)) as closing_balance
        FROM donations d
        LEFT JOIN expenditures e ON d.ngo_id = e.ngo_id 
            AND e.spending_date <= %s
        WHERE d.ngo_id = %s 
        AND d.donation_date <= %s
    ''', (prev_month.date(), ngo_id, prev_month.date()))

    opening_balance_result = cursor.fetchone()
    opening_balance = opening_balance_result['closing_balance'] if opening_balance_result else 0

    # Calculate current values
    total_deposits = donation_data['total_deposits'] or 0
    total_expenditures = expense_data['total_expenditures'] or 0
    total_approved = approval_data['total_approved'] or 0

    # Calculate balances
    available_balance = opening_balance + total_deposits - total_expenditures
    remaining_budget = total_approved - total_expenditures

    # Get monthly transactions detail - FIXED
    cursor.execute('''
        SELECT 
            'Donation' as type,
            d.donation_date as date,
            d.amount as amount,
            CONCAT('From: ', don.fullname) as description,
            d.donation_type as category,
            d.status as status
        FROM donations d
        JOIN donors don ON d.donor_id = don.id
        WHERE d.ngo_id = %s 
        AND d.donation_date BETWEEN %s AND %s
        AND d.status = 'Completed'

        UNION ALL

        SELECT 
            'Expenditure' as type,
            e.spending_date as date,
            e.amount_spent as amount,
            CONCAT('Paid to: ', e.paid_to, ' - ', e.details) as description,
            e.program_name as category,
            'Completed' as status
        FROM expenditures e
        WHERE e.ngo_id = %s 
        AND e.spending_date BETWEEN %s AND %s

        UNION ALL

        SELECT 
            'Budget Approval' as type,
            br.approval_date as date,
            br.approved_amount as amount,
            CONCAT('Approved for: ', bp.program_name) as description,
            br.status as category,
            'Completed' as status
        FROM budget_requests br
        JOIN budget_programs bp ON br.program_id = bp.id
        WHERE br.ngo_id = %s 
        AND br.approval_date BETWEEN %s AND %s
        AND br.status IN ('approved', 'partially_approved')

        ORDER BY date DESC
    ''', (ngo_id, start_date.date(), end_date.date(),
          ngo_id, start_date.date(), end_date.date(),
          ngo_id, start_date.date(), end_date.date()))

    transactions = cursor.fetchall()

    # Get available months for dropdown - FIXED DATE_FORMAT
    cursor.execute('''
        SELECT DISTINCT DATE_FORMAT(d.donation_date, '%%Y-%%m') as month_year
        FROM donations d
        WHERE d.ngo_id = %s
        UNION
        SELECT DISTINCT DATE_FORMAT(e.spending_date, '%%Y-%%m') as month_year
        FROM expenditures e
        WHERE e.ngo_id = %s
        UNION
        SELECT DISTINCT DATE_FORMAT(br.approval_date, '%%Y-%%m') as month_year
        FROM budget_requests br
        WHERE br.ngo_id = %s AND br.approval_date IS NOT NULL
        ORDER BY month_year DESC
    ''', (ngo_id, ngo_id, ngo_id))

    available_months = cursor.fetchall()

    cursor.close()

    return render_template('admin/monthly_consolidated.html',
                           selected_month=selected_month,
                           available_months=available_months,
                           opening_balance=opening_balance,
                           total_deposits=total_deposits,
                           total_expenditures=total_expenditures,
                           total_approved=total_approved,
                           available_balance=available_balance,
                           remaining_budget=remaining_budget,
                           deposit_count=donation_data['deposit_count'] or 0,
                           expense_count=expense_data['expense_count'] or 0,
                           approval_count=approval_data['approval_count'] or 0,
                           transactions=transactions,
                           month_name=start_date.strftime('%B %Y'))


def generate_consolidated_pdf(consolidated_data, month_name):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Title Section
    pdf.setTitle("Monthly Consolidated Report")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 50, "Monthly Consolidated Sheet")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 75, f"Month: {month_name}")
    pdf.drawCentredString(width / 2, height - 95, "Role: Admin")

    y = height - 130

    # Financial Summary Section
    pdf.setFillColor(colors.HexColor('#2c3e50'))
    pdf.rect(30, y - 10, width - 60, 25, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Financial Summary")
    y -= 40

    # Summary items in a grid layout
    summary_items = [
        {"label": "Opening Balance", "value": f"₹{consolidated_data['opening_balance']:.2f}", "type": "normal"},
        {"label": "Total Deposits", "value": f"₹{consolidated_data['total_deposits']:.2f}", "type": "positive",
         "count": f"{consolidated_data['deposit_count']} transactions"},
        {"label": "Total Expenditures", "value": f"₹{consolidated_data['total_expenditures']:.2f}", "type": "negative",
         "count": f"{consolidated_data['expense_count']} expenses"},
        {"label": "Available Balance", "value": f"₹{consolidated_data['available_balance']:.2f}",
         "type": "positive" if consolidated_data['available_balance'] >= 0 else "negative"},
        {"label": "Budget Approved", "value": f"₹{consolidated_data['total_approved']:.2f}", "type": "positive",
         "count": f"{consolidated_data['approval_count']} approvals"},
        {"label": "Remaining Budget", "value": f"₹{consolidated_data['remaining_budget']:.2f}",
         "type": "positive" if consolidated_data['remaining_budget'] >= 0 else "negative"}
    ]

    # Draw summary boxes in 2x3 grid
    box_width = (width - 80) / 3
    box_height = 60
    start_x = 35
    start_y = y

    for i, item in enumerate(summary_items):
        row = i // 3
        col = i % 3

        x = start_x + col * (box_width + 5)
        y_pos = start_y - row * (box_height + 10)

        # Draw box with background
        pdf.setFillColor(colors.HexColor('#f8f9fa'))
        pdf.rect(x, y_pos - box_height, box_width, box_height, fill=1, stroke=1)

        # Colored left border
        border_color = {
            "normal": '#4e73df',
            "positive": '#28a745',
            "negative": '#dc3545'
        }[item['type']]

        pdf.setFillColor(colors.HexColor(border_color))
        pdf.rect(x, y_pos - box_height, 4, box_height, fill=1, stroke=0)

        # Text content
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(x + 10, y_pos - 20, item['label'])

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x + 10, y_pos - 35, item['value'])

        if 'count' in item:
            pdf.setFont("Helvetica", 8)
            pdf.setFillColor(colors.gray)
            pdf.drawString(x + 10, y_pos - 48, item['count'])

    y = start_y - (2 * (box_height + 10)) - 30

    # Transaction Details Section
    pdf.setFillColor(colors.HexColor('#2c3e50'))
    pdf.rect(30, y - 10, width - 60, 25, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, f"Transaction Details - {len(consolidated_data['transactions'])} transactions")
    y -= 40

    # Table headers
    headers = ["Date", "Type", "Amount (₹)", "Description", "Category", "Status"]
    col_widths = [70, 70, 80, 150, 100, 70]

    # Header background
    pdf.setFillColor(colors.HexColor('#e9ecef'))
    pdf.rect(30, y - 8, width - 60, 20, fill=1, stroke=0)
    pdf.setFillColor(colors.black)

    # Header text
    x = 35
    pdf.setFont("Helvetica-Bold", 10)
    for i, header in enumerate(headers):
        pdf.drawString(x, y, header)
        x += col_widths[i]

    y -= 25

    # Table rows
    pdf.setFont("Helvetica", 9)
    for idx, transaction in enumerate(consolidated_data['transactions']):
        # Check if we need a new page
        if y < 50:
            pdf.showPage()
            y = height - 50

            # Redraw headers on new page
            pdf.setFillColor(colors.HexColor('#e9ecef'))
            pdf.rect(30, y - 8, width - 60, 20, fill=1, stroke=0)
            pdf.setFillColor(colors.black)
            x = 35
            pdf.setFont("Helvetica-Bold", 10)
            for i, header in enumerate(headers):
                pdf.drawString(x, y, header)
                x += col_widths[i]
            y -= 25
            pdf.setFont("Helvetica", 9)

        # Alternate row background
        if idx % 2 == 0:
            pdf.setFillColor(colors.HexColor('#f8f9fa'))
            pdf.rect(30, y - 5, width - 60, 15, fill=1, stroke=0)
        pdf.setFillColor(colors.black)

        # Row data
        x = 35
        row_data = [
            transaction['date'].strftime('%d/%m/%Y') if transaction.get('date') else 'N/A',
            transaction.get('type', 'N/A'),
            f"₹{transaction.get('amount', 0):.2f}",
            transaction.get('description', 'N/A'),
            transaction.get('category', 'N/A'),
            transaction.get('status', 'N/A')
        ]

        for i, item in enumerate(row_data):
            text = str(item)
            # Truncate long text
            if i == 3:  # Description column
                if len(text) > 25:
                    text = text[:22] + '...'
            elif i == 4:  # Category column
                if len(text) > 15:
                    text = text[:12] + '...'
            else:
                if len(text) > 15:
                    text = text[:12] + '...'

            pdf.drawString(x, y, text)
            x += col_widths[i]

        y -= 18

    # Footer
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.gray)
    pdf.drawString(30, 30, f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    pdf.drawRightString(width - 30, 30, f"Page 1")

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f"consolidated_report_{month_name.replace(' ', '_')}.pdf",
                     mimetype='application/pdf')
if __name__ == '__main__':
    app.run(debug=True)
