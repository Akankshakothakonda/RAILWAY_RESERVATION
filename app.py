from flask import (  # type: ignore[reportMissingImports]
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

import mysql.connector  # type: ignore[reportMissingImports]
from mysql.connector import Error  # type: ignore[reportMissingImports]
from config import DB_CONFIG  # type: ignore[reportMissingImports]

import random
from datetime import datetime


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = "railway_reservation_system_secret_key_2026"

# ============================================================
# ACCESS CONTROL
# ============================================================

def admin_required():

    return (
        session.get("role") == "admin"
        and session.get("admin_id") is not None
    )


def user_required():

    return (
        session.get("role") == "user"
        and session.get("user_id") is not None
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    try:

        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )

        return connection

    except Error as e:

        print("Database connection error:", e)

        return None


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not email or not password:

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        conn = get_db_connection()

        if conn is None:
            return "Database connection failed."

        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:

                flash(
                    "Email already registered.",
                    "error"
                )

                return redirect(
                    url_for("register")
                )

            cursor.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    phone,
                    role
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    email,
                    password,
                    phone,
                    "user"
                )
            )

            conn.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Error as e:

            conn.rollback()

            print(
                "Registration error:",
                e
            )

            flash(
                "Registration failed.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        finally:

            cursor.close()
            conn.close()

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter email and password.", "error")
            return redirect(url_for("login"))

        conn = get_db_connection()
        if conn is None:
            return "Database connection failed.", 500

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT user_id, name, email, password, role
                FROM users
                WHERE email = %s
                LIMIT 1
            """, (email,))
            user = cursor.fetchone()

            if not user or user["password"] != password:
                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))

            if user["role"] == "admin":
                flash("Administrator account detected. Please use Admin Login.", "error")
                return redirect(url_for("admin_login"))

            session.clear()
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = "user"
            flash("Login successful.", "success")
            return redirect(url_for("index"))

        except Error as e:
            print("Login error:", e)
            flash("Login error.", "error")
            return redirect(url_for("login"))
        finally:
            cursor.close()
            conn.close()

    return render_template("login.html")


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if admin_required():
        return redirect(url_for("admin"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter admin email and password.", "error")
            return redirect(url_for("admin_login"))

        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed.", "error")
            return redirect(url_for("admin_login"))

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT user_id, name, email, password, role
                FROM users
                WHERE email = %s AND role = 'admin'
                LIMIT 1
            """, (email,))
            admin_user = cursor.fetchone()

            if not admin_user or admin_user["password"] != password:
                flash("Invalid admin credentials.", "error")
                return redirect(url_for("admin_login"))

            session.clear()
            session["admin_id"] = admin_user["user_id"]
            session["admin_name"] = admin_user["name"]
            session["admin_email"] = admin_user["email"]
            session["role"] = "admin"
            flash("Administrator login successful.", "success")
            return redirect(url_for("admin"))

        except Error as e:
            print("Admin login error:", e)
            flash("Database error while logging in.", "error")
            return redirect(url_for("admin_login"))
        finally:
            cursor.close()
            conn.close()

    return render_template("admin_login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Administrator logged out successfully.", "success")
    return redirect(url_for("admin_login"))


# ============================================================
# SEARCH TRAINS
# ============================================================

@app.route(
    "/search",
    methods=["GET", "POST"]
)
def search():

    trains = []

    if request.method == "GET":

        source = request.args.get(
            "source",
            ""
        ).strip()

        destination = request.args.get(
            "destination",
            ""
        ).strip()

        journey_date = request.args.get(
            "journey_date",
            ""
        ).strip()

    else:

        source = request.form.get(
            "source",
            ""
        ).strip()

        destination = request.form.get(
            "destination",
            ""
        ).strip()

        journey_date = request.form.get(
            "journey_date",
            ""
        ).strip()

    if source and destination:

        conn = get_db_connection()

        if conn is None:
            return "Database connection failed."

        cursor = conn.cursor(
            dictionary=True
        )

        try:

            cursor.execute(
                """
                SELECT *
                FROM trains
                WHERE source LIKE %s
                AND destination LIKE %s
                ORDER BY train_number
                """,
                (
                    "%" + source + "%",
                    "%" + destination + "%"
                )
            )

            trains = cursor.fetchall()

            print(
                "SEARCH:",
                source,
                "->",
                destination
            )

            print(
                "TRAINS FOUND:",
                len(trains)
            )

        except Error as e:

            print(
                "Search error:",
                e
            )

        finally:

            cursor.close()
            conn.close()

    return render_template(
        "search.html",
        trains=trains,
        source=source,
        destination=destination,
        journey_date=journey_date
    )


# ============================================================
# BOOK TICKET - STEP 1
# ============================================================

@app.route(
    "/book/<int:train_id>",
    methods=["GET", "POST"]
)
def book(train_id):

    if not user_required():
        flash("Please login before booking a ticket.", "error")
        return redirect(url_for("login"))

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # ----------------------------------------------------
        # GET TRAIN
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM trains
            WHERE train_id = %s
            """,
            (train_id,)
        )

        train = cursor.fetchone()

        if not train:

            return "Train not found.", 404

        # ----------------------------------------------------
        # DISPLAY BOOKING PAGE
        # ----------------------------------------------------

        if request.method == "GET":

            return render_template(
                "booking.html",
                train=train
            )

        # ----------------------------------------------------
        # RECEIVE FORM DATA
        # ----------------------------------------------------

        passenger_name = request.form.get(
            "passenger_name",
            ""
        ).strip()

        age = request.form.get(
            "age",
            ""
        ).strip()

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        journey_date = request.form.get(
            "journey_date",
            ""
        ).strip()

        travel_class = request.form.get(
            "travel_class",
            ""
        ).strip()

        berth_preference = request.form.get(
            "berth_preference",
            ""
        ).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not passenger_name:

            flash(
                "Passenger name is required.",
                "error"
            )

            return redirect(
                url_for(
                    "book",
                    train_id=train_id
                )
            )

        if not age:

            flash(
                "Age is required.",
                "error"
            )

            return redirect(
                url_for(
                    "book",
                    train_id=train_id
                )
            )

        if not gender:

            flash(
                "Gender is required.",
                "error"
            )

            return redirect(
                url_for(
                    "book",
                    train_id=train_id
                )
            )

        if not journey_date:

            flash(
                "Journey date is required.",
                "error"
            )

            return redirect(
                url_for(
                    "book",
                    train_id=train_id
                )
            )

        if not travel_class:

            flash(
                "Please select a travel class.",
                "error"
            )

            return redirect(
                url_for(
                    "book",
                    train_id=train_id
                )
            )

        if not berth_preference:

            flash(
                "Please select a berth preference.",
                "error"
            )

            return redirect(
                url_for(
                    "book",
                    train_id=train_id
                )
            )

        # ----------------------------------------------------
        # VALIDATE AGE
        # ----------------------------------------------------

        try:

            age_value = int(age)

            if age_value <= 0 or age_value > 120:

                flash(
                    "Please enter a valid age.",
                    "error"
                )

                return redirect(
                    url_for(
                        "book",
                        train_id=train_id
                    )
                )

        except ValueError:

            flash(
                "Age must be a valid number.",
                "error"
            )

            return redirect(
                url_for(
                    "book",
                    train_id=train_id
                )
            )

        # ----------------------------------------------------
        # VALIDATE JOURNEY DATE
        # ----------------------------------------------------

        try:

            selected_date = datetime.strptime(
                journey_date,
                "%Y-%m-%d"
            ).date()

            today = datetime.today().date()

            if selected_date < today:

                flash(
                    "Journey date cannot be in the past.",
                    "error"
                )

                return redirect(
                    url_for(
                        "book",
                        train_id=train_id
                    )
                )

        except ValueError:

            flash(
                "Invalid journey date.",
                "error"
            )

            return redirect(
                url_for(
                    "book",
                    train_id=train_id
                )
            )

        # ----------------------------------------------------
        # STORE PASSENGER
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO passengers
            (
                user_id,
                name,
                age,
                gender
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                session["user_id"],
                passenger_name,
                age_value,
                gender
            )
        )

        passenger_id = cursor.lastrowid

        # ----------------------------------------------------
        # STORE TEMPORARY BOOKING INFORMATION
        # ----------------------------------------------------

        session["pending_booking"] = {

            "train_id": train_id,

            "passenger_id": passenger_id,

            "journey_date": journey_date,

            "travel_class": travel_class,

            "berth_preference": berth_preference
        }

        conn.commit()

        # ----------------------------------------------------
        # GO TO PAYMENT
        # ----------------------------------------------------

        return redirect(
            url_for(
                "payment",
                train_id=train_id
            )
        )

    except Error as e:

        conn.rollback()

        print(
            "Booking database error:",
            e
        )

        return f"""
        <h2>Booking Error</h2>
        <p>{e}</p>
        <br>
        <a href="/search">Back to Search</a>
        """, 500

    except Exception as e:

        conn.rollback()

        print(
            "Booking error:",
            e
        )

        return f"""
        <h2>Booking Error</h2>
        <p>{e}</p>
        <br>
        <a href="/search">Back to Search</a>
        """, 500

    finally:

        cursor.close()
        conn.close()


# ============================================================
# PAYMENT
# ============================================================

@app.route(
    "/payment/<int:train_id>",
    methods=["GET", "POST"]
)
def payment(train_id):

    if not user_required():
        return redirect(url_for("login"))

    pending_booking = session.get(
        "pending_booking"
    )

    if not pending_booking:

        flash(
            "No pending booking found.",
            "error"
        )

        return redirect(
            url_for("search")
        )

    if pending_booking["train_id"] != train_id:

        return redirect(
            url_for("search")
        )

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # ----------------------------------------------------
        # GET TRAIN
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM trains
            WHERE train_id = %s
            """,
            (train_id,)
        )

        train = cursor.fetchone()

        if not train:

            return "Train not found.", 404

        # ----------------------------------------------------
        # DISPLAY PAYMENT PAGE
        # ----------------------------------------------------

        if request.method == "GET":

            return render_template(
                "payment.html",
                train=train,
                booking=pending_booking
            )

        # ----------------------------------------------------
        # PAYMENT METHOD
        # ----------------------------------------------------

        payment_method = request.form.get(
            "payment_method",
            ""
        ).strip()

        if not payment_method:

            flash(
                "Please select a payment method.",
                "error"
            )

            return redirect(
                url_for(
                    "payment",
                    train_id=train_id
                )
            )

        # ----------------------------------------------------
        # GENERATE UNIQUE PNR
        # ----------------------------------------------------

        while True:

            pnr = str(
                random.randint(
                    1000000000,
                    9999999999
                )
            )

            cursor.execute(
                """
                SELECT booking_id
                FROM bookings
                WHERE pnr = %s
                """,
                (pnr,)
            )

            existing_pnr = cursor.fetchone()

            if not existing_pnr:
                break

        # ----------------------------------------------------
        # FARE
        # ----------------------------------------------------

        fare_table = {

            "1A": 2500.00,

            "2A": 1800.00,

            "3A": 1200.00,

            "SL": 600.00,

            "2S": 300.00
        }

        amount = fare_table.get(
            pending_booking["travel_class"],
            500.00
        )

        # ----------------------------------------------------
        # CREATE PENDING BOOKING
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO bookings
            (
                user_id,
                train_id,
                passenger_id,
                journey_date,
                travel_class,
                berth_preference,
                coach_number,
                berth_number,
                berth_type,
                booking_status,
                seat_number,
                pnr,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                NULL,
                NULL,
                NULL,
                'PENDING',
                NULL,
                %s,
                'PENDING'
            )
            """,
            (
                session["user_id"],
                train_id,
                pending_booking["passenger_id"],
                pending_booking["journey_date"],
                pending_booking["travel_class"],
                pending_booking["berth_preference"],
                pnr
            )
        )

        booking_id = cursor.lastrowid

        # ----------------------------------------------------
        # CREATE PAYMENT RECORD
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO payments
            (
                booking_id,
                amount,
                payment_method,
                payment_status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                'SUCCESS'
            )
            """,
            (
                booking_id,
                amount,
                payment_method
            )
        )

        conn.commit()

        # ----------------------------------------------------
        # CLEAR TEMPORARY SESSION
        # ----------------------------------------------------

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "Payment successful. Booking request submitted for admin approval.",
            "success"
        )

        return redirect(
            url_for(
                "ticket",
                booking_id=booking_id
            )
        )

    except Error as e:

        conn.rollback()

        print(
            "Payment database error:",
            e
        )

        return f"""
        <h2>Payment Error</h2>
        <p>{e}</p>
        <br>
        <a href="/search">Back to Search</a>
        """, 500

    except Exception as e:

        conn.rollback()

        print(
            "Payment error:",
            e
        )

        return f"""
        <h2>Payment Error</h2>
        <p>{e}</p>
        <br>
        <a href="/search">Back to Search</a>
        """, 500

    finally:

        cursor.close()
        conn.close()


# ============================================================
# TICKET
# ============================================================

@app.route(
    "/ticket/<int:booking_id>"
)
def ticket(booking_id):

    if not user_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                b.booking_id,

                b.journey_date,

                b.travel_class,

                b.berth_preference,

                b.coach_number,

                b.berth_number,

                b.berth_type,

                b.seat_number,

                b.pnr,

                b.status,

                b.booking_status,

                p.name AS passenger_name,

                p.age,

                p.gender,

                t.train_number,

                t.train_name,

                t.source,

                t.destination,

                t.departure_time,

                t.arrival_time,

                pay.amount,

                pay.payment_method,

                pay.payment_status,

                pay.payment_date

            FROM bookings b

            JOIN passengers p
                ON b.passenger_id =
                   p.passenger_id

            JOIN trains t
                ON b.train_id =
                   t.train_id

            LEFT JOIN payments pay
                ON b.booking_id =
                   pay.booking_id

            WHERE b.booking_id = %s

            AND b.user_id = %s
            """,
            (
                booking_id,
                session["user_id"]
            )
        )

        booking = cursor.fetchone()

        if not booking:

            return "Ticket not found.", 404

        return render_template(
            "ticket.html",
            booking=booking
        )

    except Error as e:

        print(
            "Ticket error:",
            e
        )

        return "Unable to load ticket."

    finally:

        cursor.close()
        conn.close()


# ============================================================
# MY BOOKINGS
# ============================================================

@app.route("/bookings")
def bookings():

    if not user_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                b.booking_id,

                b.journey_date,

                b.travel_class,

                b.berth_preference,

                b.coach_number,

                b.berth_number,

                b.berth_type,

                b.seat_number,

                b.pnr,

                b.status,

                b.booking_status,

                p.name AS passenger_name,

                t.train_number,

                t.train_name,

                t.source,

                t.destination,

                t.departure_time,

                t.arrival_time,

                pay.amount,

                pay.payment_method,

                pay.payment_status

            FROM bookings b

            JOIN passengers p
                ON b.passenger_id =
                   p.passenger_id

            JOIN trains t
                ON b.train_id =
                   t.train_id

            LEFT JOIN payments pay
                ON b.booking_id =
                   pay.booking_id

            WHERE b.user_id = %s

            ORDER BY b.booking_id DESC
            """,
            (
                session["user_id"],
            )
        )

        booking_list = cursor.fetchall()

        return render_template(
            "bookings.html",
            bookings=booking_list
        )

    except Error as e:

        print(
            "Bookings error:",
            e
        )

        return "Unable to load bookings."

    finally:

        cursor.close()
        conn.close()


# ============================================================
# CANCEL BOOKING
# ============================================================

@app.route(
    "/cancel/<int:booking_id>",
    methods=["POST"]
)
def cancel_booking(booking_id):

    if not user_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # ----------------------------------------------------
        # CHECK OWNERSHIP
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM bookings
            WHERE booking_id = %s
            AND user_id = %s
            """,
            (
                booking_id,
                session["user_id"]
            )
        )

        booking = cursor.fetchone()

        if not booking:

            flash(
                "Booking not found.",
                "error"
            )

            return redirect(
                url_for("bookings")
            )

        # ----------------------------------------------------
        # CHECK STATUS
        # ----------------------------------------------------

        if booking["status"] == "CANCELLED":

            flash(
                "This booking is already cancelled.",
                "error"
            )

            return redirect(
                url_for("bookings")
            )

        # ----------------------------------------------------
        # RELEASE ALLOCATED BERTH
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM berth_allocations
            WHERE booking_id = %s
            """,
            (booking_id,)
        )

        # ----------------------------------------------------
        # CANCEL BOOKING
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE bookings

            SET
                status = 'CANCELLED',
                booking_status = 'CANCELLED'

            WHERE booking_id = %s
            AND user_id = %s
            """,
            (
                booking_id,
                session["user_id"]
            )
        )

        # ----------------------------------------------------
        # REFUND STATUS
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE payments

            SET payment_status =
                'REFUND_PENDING'

            WHERE booking_id = %s
            """,
            (booking_id,)
        )

        conn.commit()

        flash(
            "Booking cancelled successfully.",
            "success"
        )

        return redirect(
            url_for("bookings")
        )

    except Error as e:

        conn.rollback()

        print(
            "Cancel booking error:",
            e
        )

        flash(
            "Unable to cancel booking.",
            "error"
        )

        return redirect(
            url_for("bookings")
        )

    finally:

        cursor.close()
        conn.close()


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin():
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed.", 500
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT COUNT(*) AS total_users FROM users WHERE role = 'user'")
        total_users = cursor.fetchone()["total_users"]

        cursor.execute("SELECT COUNT(*) AS total_trains FROM trains")
        total_trains = cursor.fetchone()["total_trains"]

        cursor.execute("SELECT COUNT(*) AS total_bookings FROM bookings")
        total_bookings = cursor.fetchone()["total_bookings"]

        cursor.execute("SELECT COUNT(*) AS pending_bookings FROM bookings WHERE booking_status = 'PENDING'")
        pending_bookings = cursor.fetchone()["pending_bookings"]

        cursor.execute("SELECT COUNT(*) AS confirmed_bookings FROM bookings WHERE booking_status = 'CONFIRMED'")
        confirmed_bookings = cursor.fetchone()["confirmed_bookings"]

        cursor.execute("SELECT COUNT(*) AS cancelled_bookings FROM bookings WHERE booking_status = 'CANCELLED'")
        cancelled_bookings = cursor.fetchone()["cancelled_bookings"]

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total_revenue
            FROM payments
            WHERE payment_status = 'SUCCESS'
        """)
        total_revenue = cursor.fetchone()["total_revenue"]

        cursor.execute("SELECT * FROM trains ORDER BY train_number")
        trains = cursor.fetchall()

        cursor.execute("""
            SELECT
                b.booking_id, b.journey_date, b.travel_class,
                b.berth_preference, b.coach_number, b.berth_number,
                b.berth_type, b.seat_number, b.pnr,
                b.booking_status, b.status,
                p.name AS passenger_name, p.age, p.gender,
                u.name AS user_name, u.email AS user_email,
                t.train_number, t.train_name, t.source, t.destination,
                pay.amount, pay.payment_method, pay.payment_status
            FROM bookings b
            JOIN passengers p ON b.passenger_id = p.passenger_id
            JOIN users u ON b.user_id = u.user_id
            JOIN trains t ON b.train_id = t.train_id
            LEFT JOIN payments pay ON b.booking_id = pay.booking_id
            ORDER BY CASE WHEN b.booking_status = 'PENDING' THEN 0 ELSE 1 END,
                     b.booking_id DESC
        """)
        booking_requests = cursor.fetchall()

        return render_template(
            "admin.html",
            total_users=total_users,
            total_trains=total_trains,
            total_bookings=total_bookings,
            pending_bookings=pending_bookings,
            confirmed_bookings=confirmed_bookings,
            cancelled_bookings=cancelled_bookings,
            total_revenue=total_revenue,
            trains=trains,
            booking_requests=booking_requests
        )

    except Error as e:
        print("Admin error:", e)
        return "Unable to load admin dashboard.", 500
    finally:
        cursor.close()
        conn.close()


# ============================================================
# ADMIN - ACCEPT BOOKING
# ============================================================

@app.route("/admin/accept-booking/<int:booking_id>", methods=["POST"])
def accept_booking(booking_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed.", 500
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        cursor.execute("""
            SELECT booking_id, train_id, journey_date,
                   travel_class, berth_preference, booking_status
            FROM bookings
            WHERE booking_id = %s
            FOR UPDATE
        """, (booking_id,))
        booking = cursor.fetchone()

        if not booking:
            conn.rollback()
            flash("Booking not found.", "error")
            return redirect(url_for("admin"))

        if booking["booking_status"] != "PENDING":
            conn.rollback()
            flash("This booking has already been processed.", "error")
            return redirect(url_for("admin"))

        # First honor requested berth type.
        cursor.execute("""
            SELECT tb.berth_id, tb.coach_number,
                   tb.berth_number, tb.berth_type
            FROM train_berths tb
            WHERE tb.train_id = %s
              AND tb.travel_class = %s
              AND tb.berth_type = %s
              AND NOT EXISTS (
                  SELECT 1 FROM berth_allocations ba
                  WHERE ba.berth_id = tb.berth_id
                    AND ba.journey_date = %s
                    AND ba.allocation_status = 'ALLOCATED'
              )
            ORDER BY tb.berth_id
            LIMIT 1
            FOR UPDATE
        """, (
            booking["train_id"],
            booking["travel_class"],
            booking["berth_preference"],
            booking["journey_date"]
        ))
        berth = cursor.fetchone()

        # If requested type is unavailable, allocate any berth in class.
        if not berth:
            cursor.execute("""
                SELECT tb.berth_id, tb.coach_number,
                       tb.berth_number, tb.berth_type
                FROM train_berths tb
                WHERE tb.train_id = %s
                  AND tb.travel_class = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM berth_allocations ba
                      WHERE ba.berth_id = tb.berth_id
                        AND ba.journey_date = %s
                        AND ba.allocation_status = 'ALLOCATED'
                  )
                ORDER BY tb.berth_id
                LIMIT 1
                FOR UPDATE
            """, (
                booking["train_id"],
                booking["travel_class"],
                booking["journey_date"]
            ))
            berth = cursor.fetchone()

        if not berth:
            conn.rollback()
            flash("No berth is available for this class and journey date.", "error")
            return redirect(url_for("admin"))

        cursor.execute("""
            INSERT INTO berth_allocations
                (berth_id, booking_id, journey_date, allocation_status)
            VALUES (%s, %s, %s, 'ALLOCATED')
        """, (
            berth["berth_id"], booking_id, booking["journey_date"]
        ))

        seat_number = f'{berth["coach_number"]}-{berth["berth_number"]}'

        cursor.execute("""
            UPDATE bookings
            SET coach_number = %s,
                berth_number = %s,
                berth_type = %s,
                seat_number = %s,
                booking_status = 'CONFIRMED',
                status = 'CONFIRMED'
            WHERE booking_id = %s
        """, (
            berth["coach_number"],
            berth["berth_number"],
            berth["berth_type"],
            seat_number,
            booking_id
        ))

        # DO NOT set train_berths.status = 'BOOKED'.
        # berth_allocations makes occupancy date-specific.
        conn.commit()

        flash(
            f'Booking accepted. Coach {berth["coach_number"]} / '
            f'Berth {berth["berth_number"]} allocated.',
            "success"
        )
        return redirect(url_for("admin"))

    except Error as e:
        conn.rollback()
        print("Accept booking error:", e)
        flash("Unable to accept booking. Please refresh and try again.", "error")
        return redirect(url_for("admin"))
    finally:
        cursor.close()
        conn.close()


# ============================================================
# ADMIN - REJECT BOOKING
# ============================================================

@app.route("/admin/reject-booking/<int:booking_id>", methods=["POST"])
def reject_booking(booking_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed.", 500
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE bookings
            SET booking_status = 'REJECTED', status = 'REJECTED'
            WHERE booking_id = %s AND booking_status = 'PENDING'
        """, (booking_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            flash("Booking not found or already processed.", "error")
            return redirect(url_for("admin"))

        cursor.execute("""
            UPDATE payments
            SET payment_status = 'REFUND_PENDING'
            WHERE booking_id = %s
        """, (booking_id,))

        conn.commit()
        flash("Booking rejected successfully. Payment marked for refund.", "success")
        return redirect(url_for("admin"))

    except Error as e:
        conn.rollback()
        print("Reject booking error:", e)
        flash("Unable to reject booking.", "error")
        return redirect(url_for("admin"))
    finally:
        cursor.close()
        conn.close()


# ============================================================
# ADMIN - TRAIN MASTER
# ============================================================

@app.route("/admin/trains")
def admin_trains():
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed.", 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM trains ORDER BY train_number")
        trains = cursor.fetchall()
        return render_template("admin_trains.html", trains=trains, total_trains=len(trains))
    except Error as e:
        print("Admin train master error:", e)
        return "Unable to load train master.", 500
    finally:
        cursor.close()
        conn.close()


# ============================================================
# ADMIN - BOOKING REQUESTS
# ============================================================

@app.route("/admin/bookings")
def admin_bookings():
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed.", 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.*, p.name AS passenger_name, p.age, p.gender,
                   u.name AS user_name, u.email AS user_email,
                   t.train_number, t.train_name, t.source, t.destination,
                   pay.amount, pay.payment_method, pay.payment_status
            FROM bookings b
            JOIN passengers p ON b.passenger_id = p.passenger_id
            JOIN users u ON b.user_id = u.user_id
            JOIN trains t ON b.train_id = t.train_id
            LEFT JOIN payments pay ON b.booking_id = pay.booking_id
            ORDER BY CASE WHEN b.booking_status = 'PENDING' THEN 0 ELSE 1 END,
                     b.booking_id DESC
        """)
        booking_requests = cursor.fetchall()
        return render_template("admin_bookings.html", booking_requests=booking_requests)
    except Error as e:
        print("Admin bookings error:", e)
        return "Unable to load booking requests.", 500
    finally:
        cursor.close()
        conn.close()


# ============================================================
# ADMIN - ADD TRAIN
# ============================================================

@app.route("/admin/add-train", methods=["GET", "POST"])
def add_train():
    if not admin_required():
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        train_number = request.form.get("train_number", "").strip()
        train_name = request.form.get("train_name", "").strip()
        source = request.form.get("source", "").strip()
        destination = request.form.get("destination", "").strip()
        departure_time = request.form.get("departure_time", "").strip()
        arrival_time = request.form.get("arrival_time", "").strip()
        total_seats = request.form.get("total_seats", "").strip()

        if not all([
            train_number,
            train_name,
            source,
            destination,
            departure_time,
            arrival_time,
            total_seats
        ]):
            flash("Please fill all train details.", "error")
            return redirect(url_for("add_train"))

        try:
            total_seats = int(total_seats)
            if total_seats <= 0:
                flash("Total seats must be greater than 0.", "error")
                return redirect(url_for("add_train"))
        except ValueError:
            flash("Total seats must be a valid number.", "error")
            return redirect(url_for("add_train"))

        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed.", "error")
            return redirect(url_for("add_train"))

        cursor = conn.cursor(dictionary=True)

        try:
            # Prevent duplicate train numbers.
            cursor.execute("""
                SELECT train_id
                FROM trains
                WHERE train_number = %s
                LIMIT 1
            """, (train_number,))

            if cursor.fetchone():
                flash(f"Train number {train_number} already exists.", "error")
                return redirect(url_for("add_train"))

            # Add the train.
            cursor.execute("""
                INSERT INTO trains
                (
                    train_number,
                    train_name,
                    source,
                    destination,
                    departure_time,
                    arrival_time,
                    total_seats
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                train_number,
                train_name,
                source,
                destination,
                departure_time,
                arrival_time,
                total_seats
            ))

            train_id = cursor.lastrowid

            # Create 250 demo berth records for every new train:
            # 1A/H1, 2A/A1, 2S/D1, 3A/B1 and SL/S1,
            # with 50 berths in each class.
            classes = [
                ("1A", "H1"),
                ("2A", "A1"),
                ("2S", "D1"),
                ("3A", "B1"),
                ("SL", "S1")
            ]

            berth_types = [
                "LOWER",
                "MIDDLE",
                "UPPER",
                "SIDE LOWER",
                "SIDE UPPER"
            ]

            for travel_class, coach_number in classes:
                for berth_number in range(1, 51):
                    berth_type = berth_types[(berth_number - 1) % 5]

                    cursor.execute("""
                        INSERT INTO train_berths
                        (
                            train_id,
                            travel_class,
                            coach_number,
                            berth_number,
                            berth_type,
                            status
                        )
                        VALUES (%s, %s, %s, %s, %s, 'AVAILABLE')
                    """, (
                        train_id,
                        travel_class,
                        coach_number,
                        str(berth_number),
                        berth_type
                    ))

            # Commit the train and all its berth records together.
            conn.commit()

            flash(
                f"Train {train_number} added successfully with 250 berth records.",
                "success"
            )
            return redirect(url_for("admin_trains"))

        except Error as e:
            conn.rollback()
            print("Add train error:", e)
            flash(f"Unable to add train: {e}", "error")
            return redirect(url_for("add_train"))

        finally:
            cursor.close()
            conn.close()

    return render_template("add_train.html")


# ============================================================
# ADMIN - DELETE TRAIN
# ============================================================

@app.route(
    "/admin/delete-train/<int:train_id>",
    methods=["POST"]
)
def delete_train(train_id):

    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM bookings
            WHERE train_id = %s
            """,
            (train_id,)
        )

        booking_count = cursor.fetchone()[0]

        if booking_count > 0:

            flash(
                "Cannot delete this train because bookings exist.",
                "error"
            )

            return redirect(
                url_for("admin")
            )

        cursor.execute(
            """
            DELETE FROM trains
            WHERE train_id = %s
            """,
            (train_id,)
        )

        conn.commit()

        flash(
            "Train deleted successfully.",
            "success"
        )

        return redirect(
            url_for("admin")
        )

    except Error as e:

        conn.rollback()

        print(
            "Delete train error:",
            e
        )

        flash(
            "Unable to delete train.",
            "error"
        )

        return redirect(
            url_for("admin")
        )

    finally:

        cursor.close()
        conn.close()


# ============================================================
# LIVE TRAIN STATUS
# ============================================================

@app.route(
    "/live-status",
    methods=["GET", "POST"]
)
def live_status():

    train = None
    status_data = None

    if request.method == "POST":

        train_number = request.form.get(
            "train_number",
            ""
        ).strip()

        conn = get_db_connection()

        if conn is None:
            return "Database connection failed."

        cursor = conn.cursor(
            dictionary=True
        )

        try:

            cursor.execute(
                """
                SELECT *
                FROM trains
                WHERE train_number = %s
                """,
                (train_number,)
            )

            train = cursor.fetchone()

            if train:

                status_data = {

                    "live_status":
                        "RUNNING",

                    "delay":
                        0,

                    "current_location":
                        train["source"],

                    "previous_station":
                        train["source"],

                    "next_station":
                        train["destination"],

                    "current_speed":
                        65,

                    "status_message":
                        "Train is running as scheduled."
                }

        except Error as e:

            print(
                "Live status error:",
                e
            )

        finally:

            cursor.close()
            conn.close()

    return render_template(
        "live_status.html",
        train=train,
        status_data=status_data
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    <a href="/">Go Home</a>
    """, 404


@app.errorhandler(500)
def internal_server_error(error):

    return """
    <h1>500 - Internal Server Error</h1>
    <p>Something went wrong on the server.</p>
    <a href="/">Go Home</a>
    """, 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )