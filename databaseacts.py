from sqlite3 import InterfaceError
import mysql.connector
import bcrypt
import mysql
from datetime import datetime
class databaseActs:

    def __init__(self):
        self.mydb = None
        self.mycursor = None
        self.connection = False
        self.connect()

    def connect(self):
        try:
            self.mydb = mysql.connector.connect(
                database="membean",
                host="127.0.0.1",
                user="user",
                password="password"
                )
            self.mycursor = self.mydb.cursor()
            self.connection = True

        except mysql.connector.Error as err:
            print("Database connection failed: ", err)
            self.connection = False 

    def reconnect(self):
        if self.mydb is None or not self.mydb.is_connected():
            self.mydb = mysql.connector.connect()
            print("Reconnecting")
            self.connect()

    def close(self):
        if self.mydb and self.mydb.is_connected():
            self.mycursor.close()
            self.mydb.close()
            self.connection = False

    def checkExists(self, checkemail):
        self.reconnect()
        self.mycursor.execute("SELECT COUNT(*) FROM users WHERE Email = %s;", (checkemail,))
        count = self.mycursor.fetchone()[0]
        self.close()
        return count > 0  # Returns True if email exists

    def signUp(self,name,surname,email,password):
        self.reconnect()
        self.mycursor.execute("SELECT 1 FROM users WHERE Email = %s LIMIT 1;", (email,))
        exists = self.mycursor.fetchone()
        if exists:
            return False 
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            self.mycursor.execute(
                "INSERT INTO users (FirstName, LastName, Email, Password, Status) VALUES (%s, %s, %s, %s, %s);",
                (name, "surnameplaceholder", email, hashed_password, 0))
            self.mydb.commit()
            self.mycursor.execute(
                "INSERT INTO membean_cred (ID, Email, Password) VALUES ((SELECT ID FROM users WHERE email = %s), %s, %s);",
                (email, email, password))
            self.mydb.commit()
            print("Signup succesful")
            self.close()
            return True
        except (mysql.connector.errors.IntegrityError):
            print("A bug has occured (mysql.connector.errors.IntegrityError), email already exists in users, you are registered")
            self.close()
            return False



    def returnPassword(self, mail):
        self.reconnect()
        self.mycursor.execute("SELECT Password FROM users WHERE Email = %s; ", (mail,))
        resultt = self.mycursor.fetchone()
        if resultt == None:
            self.close()
            return None
        self.close()
        return resultt[0]

    def get_user_id(self, email):
        self.reconnect()
        self.mycursor.execute(
            "SELECT ID FROM users WHERE Email = %s;", (email,))
        result = self.mycursor.fetchone()
        self.close()
        return result[0]
    def get_username(self, id):
        self.reconnect()
        self.mycursor.execute(
            "SELECT FirstName FROM users WHERE ID = %s;", (id,))
        result = self.mycursor.fetchone()
        self.close()
        return result[0]
    def get_email_by_id(self, id):
        self.reconnect()
        self.mycursor.execute(
            "SELECT Email FROM membean_cred WHERE ID = %s;", (id,))
        result = self.mycursor.fetchone()
        self.close()
        if result == None:
            return None
        return result[0]
    
    def get_password_by_id(self, id):
        self.reconnect()
        self.mycursor.execute(
            "SELECT Password FROM membean_cred WHERE ID = %s;", (id,))
        result = self.mycursor.fetchone()
        self.close()
        if result == None:
            return None
        return result[0]

    def get_scheduled_sessions(self, user_id):
        self.reconnect()
        self.mycursor.execute("SELECT * FROM schedule WHERE user_id = %s;", (user_id,))
        results = self.mycursor.fetchall()
        scheduled_sessions = [{"id": row[0], "time": row[2].strftime('%Y-%m-%d %H:%M:%S'), "pending": row[4] } for row in results]
        return scheduled_sessions

    def new_schedule_entry(self, user_id, time):
        self.reconnect()
        if len(self.get_scheduled_sessions(user_id)) >= 2:
            return False
        self.mycursor.execute("INSERT INTO schedule (user_id, time) VALUES (%s, %s);", (user_id, time))
        self.mydb.commit()
        self.close()
        return True

    def delete_schedule_entry(self, user_id, id):
        self.reconnect()
        self.mycursor.execute(
            "DELETE FROM schedule WHERE user_id = %s AND id = %s;", (user_id, id))
        self.mydb.commit()
        self.close()
        return True

    def get_pending_sessions(self):
        self.reconnect()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.mycursor.execute("SELECT * FROM schedule WHERE time <= %s AND pending = 1;", (current_time, ))
        sessionss = self.mycursor.fetchall()
        self.close()
        return [{"id": a[0], "user_id": a[1],} for a in sessionss]
    
    def set_pending_false(self, id):
        self.reconnect()
        print(id)
        self.mycursor.execute(f"UPDATE schedule SET pending = 0 WHERE id = {id};")
        self.mydb.commit()
        self.close()
    
