from fileinput import filename
from flask import Flask, redirect, render_template, request, url_for, flash, session
from databaseacts import databaseActs
import time
import re
import bcrypt
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import shutil
from Membean_Bot import MembeanBot
import threading
from loginfo import loginfo
import eventlet


class Server:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = "e27ec955046bf17dc14006a9aecb8124bfcea8f282d43e709ed4d5625310c7b0"
        self.loginfo = loginfo()
        self.running_bots = {}
        self.scheduled_sessions = {}
        self.lock = threading.Lock()
        session_folder = os.path.abspath("flask_session")
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)
            print(f"Created session folder at: {session_folder}")

        self.setup_routes()
        self.db = databaseActs()

        # Flask Session Config
        self.app.config["SESSION_FILE_DIR"] = session_folder
        self.app.config["SESSION_PERMANENT"] = False
        self.app.config["SESSION_TYPE"] = "filesystem"
        Session(self.app)

        self.clear_all_sessions()

        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="gevent", logger=True)
        self.setup_socket_events()

        if not os.path.exists(session_folder):
            os.makedirs(session_folder)
            print(f"Created session folder at: {session_folder}")


    def clear_all_sessions(self):
        session_folder = "./flask_session"  # Default folder for Flask filesystem sessions
        if os.path.exists(session_folder):
            shutil.rmtree(session_folder)  # Delete the entire folder
            print("All sessions cleared on server restart!")

    def is_valid_school_email(self, email):
        """Validates if an email follows the 'xxxxxx.##@robcol.k12.tr' format."""

        pattern = r"^[a-z]{6}\.[0-9]{2}@robcol\.k12\.tr$"
        return bool(re.match(pattern, email))

    def setup_socket_events(self):

        @self.socketio.on("connect")
        def handle_connect():
            if "user_id" in session:
                user_room = f"user_{session['user_id']}"
                join_room(user_room)
                print(f"User {session['user_id']} connected and joined room {user_room}")

        @self.socketio.on("disconnect")
        def handle_disconnect():
            if "user_id" in session:
                user_room = f"user_{session['user_id']}"
                leave_room(user_room)
                print(f"User {session['user_id']} disconnected and left room {user_room}")

        @self.socketio.on("start_bot")
        def start_bot():
            print("startbutton")
            if "user_id" not in session:
                print("999")
                return
            user_id = session["user_id"]
            user_room = f"user_{session['user_id']}"
            print("user_id", user_id)
            with self.lock:
                if user_id in self.running_bots:
                    print(f"Bot already running for user {user_id}")
                    self.socketio.emit("bot_status", {"status": "Bot is already running"}, room=user_room)
                    return
   
            name = self.db.get_username(session['user_id'])

            socketio = self.socketio
            bot = MembeanBot(name=name, bot_id=user_id, socket_io=socketio, user_room=user_room)


            def run_bot(id_):
                #get email and password using id
                email = self.db.get_email_by_id(id_)
                password = self.db.get_password_by_id(id_)
                if email is None or password is None:
                    print("Email or password is None")
                    return
                try:
                    bot.startMembeanSession(email, password)
                finally:
                    with self.lock:
                        if id_ in self.running_bots:
                            del self.running_bots[id_]
                    self.socketio.emit("bot_status", {"status": "Bot is stopped!"}, room=user_room)
            bot_thread = threading.Thread(target=run_bot, args=(user_id, ))
            bot_thread.start()
            with self.lock:
                self.running_bots[user_id] = bot
            print(f"Bot started for user {user_id}")



    def setup_routes(self):
        #usage --> self.app.add_url_rule("/route", "function_name", self.method)
        #ex. ----> self.app.add_url_rule("/", "index", self.index)
        #ex. ----> self.app.add_url_rule("/start_bot", "start_bot", self.start_bot, methods=["POST"])
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/signin", "signin", self.signin, methods=["GET", "POST"])
        self.app.add_url_rule("/signup", "signup", self.signup, methods=["GET", "POST"])
        self.app.add_url_rule("/dashboard", "dashboard", self.dashboard)
        self.app.add_url_rule("/logout", "logout", self.logout)
        self.app.add_url_rule("/view_log/<filename>", "view_log", self.view_log)
        self.app.add_url_rule("/schedule_sessions", "schedule_sessions", self.schedule_page)


    def dashboard(self):
        if "user_id" not in session:
            flash("You must be logged in to view this page.", "danger")
            return redirect(url_for("signin"))

        user_id = session["user_id"]

        last_log = self.loginfo.get_last_log_info(id = user_id)
        duration = None
        start_time = None
        filename = None

        if last_log:
            start_time = last_log["start_time"]
            filename = last_log["filename"]
            duration = self.loginfo.get_session_duration(filename)


        return render_template("newdashboard.html", user_id=user_id, start_time=start_time, filename=filename, duration=duration)


    def schedule_page(self):
        if "user_id" not in session:
            flash("You must be logged in to schedule a session.", "danger")
            return redirect(url_for("signin"))
        user_id = session["user_id"]
        scheduled_sessions = self.db.get_scheduled_sessions(user_id)
        return render_template("schedule_sessions.html", sessions=scheduled_sessions)


    def view_log(self, filename):
        log_path = os.path.join("bot_logs", filename)
        
        if not os.path.exists(log_path):
            flash("Log file not found.", "danger")
            return redirect(url_for("dashboard"))

        with open(log_path, "r", encoding="utf-8") as log_file:
            log_content = log_file.read()

        return render_template("view_log.html", log_content=log_content, filename=filename)

    def index(self):
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return render_template("index.html")

    def signin(self):
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            print("POST signin")
            email = request.form["email"]
            password = request.form["pass"]
            if not self.is_valid_school_email(email):
                flash("Email format is incorrect! , (xxxxxx.##@robcol.k12.tr)", "danger")
                return redirect(url_for("signin"))
            if not self.db.checkExists(email):
                flash("Email doesnt exist !!!", "danger")
                exists = False
                return redirect(url_for("signin"))

            hashed_pass = self.db.returnPassword(email)

            if self.is_valid_school_email(email) and hashed_pass != None:
                if bcrypt.checkpw(password.encode(), hashed_pass.encode()):
                    flash("You have successfully signed in!", "success")

                    # Fetch user ID from the database
                    user_id = self.db.get_user_id(email)

                    print("900")
                    # Store user session
                    session["user_id"] = user_id
                    session["email"] = email  # Store email for reference
                    print("sessionnn", session)
                    return redirect(url_for("dashboard"))   
                else:
                    print("901")
                    flash("Password is incorrect!", "danger")
                    return redirect(url_for("signin"))
            else:
                print("902")
                flash("Something went wrong!", "danger")
                return redirect(url_for("signin"))

        return render_template("signin.html")

    def signup(self):
        if request.method == "POST":
            print("POST signup")
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["pass"]
            if not self.is_valid_school_email(email):
                flash("Email format is incorrect! , (xxxxxx.##@robcol.k12.tr)", "danger")
                return redirect(url_for("signup"))

            if self.db.checkExists(email):
                flash("Email already exists in the database !!!", "danger")
                return redirect(url_for("signup"))

            
            a = self.db.signUp(name, "surnameplacholder", email, password)
            if a:
                flash("You have successfully signed up!", "success")
                return redirect(url_for("index"))
            else:
                flash("Email already exists in the database !!!", "danger")
                return redirect(url_for("index"))
                

        return render_template("signup.html", encoding="utf-8")

    def logout(self):
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("signin"))

    def run(self, host="0.0.0.0", port=5000, debug=True):
        self.socketio.run(self.app ,host=host, port=port, debug=debug)
    


if __name__ == "__main__":
    server = Server()
    server.run()




