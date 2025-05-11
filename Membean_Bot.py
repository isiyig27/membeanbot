from bdb import Breakpoint
from pickle import TRUE
from pyexpat.errors import messages
from re import S
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import random
import openai
import sys
import os
import logging
from datetime import datetime
from flask_socketio import SocketIO
#from databaseacts import databaseActs



class MembeanBot:

    def __init__(self, bot_id, name, socket_io = None, user_room=None):
        self.running = False
        self.thread = None
        self.name = name
        self.user_room = user_room
        self.socket_io = socket_io
        self.bot_id = bot_id
        self.logger = self.setup_logger()
        self.word = "aaaaaa"
        self.driver = None

    def stop(self):
        """Stops the WebDriver session for this user."""
        if self.driver:
            self.driver.quit()
            self.logger.info("WebDriver closed")
            self.driver = None  # Reset driver instance

    def log_message(self, message):
        if self.socket_io and self.user_room:
            self.socket_io.emit("bot_status", {"status": str(message)}, room=self.user_room)

        else:
            print(message)

    def setup_logger(self):
        """Creates a unique logger for each bot instance."""
        logs_folder = "bot_logs"
        os.makedirs(logs_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
        log_filename = os.path.join(logs_folder, f"log_{self.bot_id}_{self.name}_{timestamp}.txt")

        logger = logging.getLogger(f"bot_{self.bot_id}")
        logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(log_filename, mode="w", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

        if logger.hasHandlers():
            logger.handlers.clear()  # Ensure no duplicate handlers
        logger.addHandler(file_handler)

        return logger

    def getName(self):
        return self.name

    def startMembeanSession(self, email, password):
        self.logger.info("Starting Membean session...")
        options = Options()
        options.binary_location = '/usr/bin/google-chrome'
        options.add_argument("--headless")  #  Ensures Chrome stays invisible
        options.add_argument("--disable-gpu")  #  Prevents GPU-related crashes
        options.add_argument("--no-sandbox")  #  Fixes issues in multi-threading
        options.add_argument("--disable-dev-shm-usage")  # Prevents memory errors
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

        options.add_argument("--memory-pressure-off")  # Reduces memory usage

        service = Service('/usr/local/bin/chromedriver')  # ChromeDriver service
        self.driver = webdriver.Chrome(service=service, options=options)

        openai.api_key= "openai api key not shown for security reasons"
        gptmessages = [
            {"role": "system", "content": "you are a question solver"}
            ]
        new=2
        abc=[]
        self.word="a"
        choicelist=[]
        i=0
        def executeSolveQuestionNormal():
            self.log_message("Solving Question ..")
            self.logger.info("Solving Question ..")
            choices=[]
            choicee=None
            choice=None
            time.sleep(4)
            try:
                question=self.driver.find_element(By.CLASS_NAME,"question").text
                choices=self.driver.find_elements(By.CLASS_NAME,"choice ")
            except Exception as er:
                self.log_message("1001")
                self.driver.save_screenshot("error.png")
                self.log_message(str(er))
                self.logger.info(str(er))
                self.stop()

            optiona=choices[0].text
            optionb=choices[1].text
            optionc=choices[2].text
            try:
                optiond=choices[3].text
                chatgptquestion = "Question = "+question+"\n A) "+optiona+"\n B) "+optionb+"\n C) "+optionc+"\n D) "+optiond+"\n Only answer with the letters A,B,C or D: "
                dispresent = True
            except:
                chatgptquestion = "Question = "+question+"\n A) "+optiona+"\n B) "+optionb+"\n C) "+optionc+"\n Only answer with the letters A,B or C: "
                dispresent = False
            self.log_message(str(chatgptquestion))
            self.logger.info(f"{chatgptquestion}")
            gptmessages.append({"role": "user", "content": chatgptquestion})
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=gptmessages
            )
            answer = completion.choices[0].message.content
            self.log_message(f"answer= {answer}")
            self.logger.info(f"answer= {answer}")
            try:
                a=answer.index(")")
            except ValueError:
                try:
                    a=answer.index(":")
                    a+=3
                except ValueError:
                    a=1
            answerid = answer[a-1].lower()
            if answerid == "a":
                choices[0].click()
            elif answerid == "b":
                choices[1].click()
            elif answerid == "c":
                choices[2].click()
            elif answerid == "d" and dispresent == True:
                choices[3].click()
            else:
                self.log_message("Invalid answer, answering as A")
                self.logger.info("Invalid answer, answering as A")
                choices[0].click()
            self.log_message(f"Question answered as {answer[a-1]}")
            self.logger.info(f"Question answered as {answer[a-1]}")
            time.sleep(3)
        def check_constellation_question():
            try:
                self.driver.find_element(By.XPATH,"//img[@alt = 'constellation question']")
                self.driver.save_screenshot("screenshot.png")
            except NoSuchElementException:
                return False
            return True
        def check_exists_by_class(classs):
            try:
                self.driver.find_element(By.CLASS_NAME,classs)
            except NoSuchElementException:
                return False
            return True
        def check_exists_by_id(id):
            try:
                self.driver.find_element("id",id)
            except NoSuchElementException:
                return False
            return True
        def mainFunction():
            try:
                global login
                ct = 0
                url = "https://membean.com/training_sessions/new"
                self.driver.get(url)
                self.log_message("Starting Membean")
                try:
                    self.driver.find_element("id", "username").send_keys(email)
                    self.driver.find_element("id", "password").send_keys(password)
                    self.driver.find_element(By.XPATH,'//*[@id="login"]/div[4]/button').click()
                except:
                    self.log_message("Login page error")
                    self.logger.info("Login page error")
                    try:
                        self.driver.save_screenshot("loginerror.png")
                    except:
                        self.log_message("Unable to take loginerror screenshot")
                        self.logger.info("Unable to take loginerror screenshot")
                time.sleep(3)
                if check_exists_by_id("Proceed")==True:
                    self.log_message("Login Succesful")
                    login = True
                    self.logger.info("Login Succesful")
                    self.driver.find_element("id","Proceed").click()
                while i==0:
                    ct += 1
                    randomisedvalue=random.randint(30,45)
                    time.sleep(4.5)
                    if check_exists_by_class("choice.answer")==True:
                        self.log_message("Study section")
                        self.logger.info("Study section")
                        time.sleep(3)
                        self.word=self.driver.find_element(By.CLASS_NAME,"wordform").text
                        self.driver.find_element(By.CLASS_NAME,'choice.answer').click()
                        self.log_message("Question answered")
                        self.logger.info("Question answered")
                        self.log_message(f"Waiting {randomisedvalue} seconds before proceeding")
                        self.logger.info(f"Waiting {randomisedvalue} seconds before proceeding")
                        time.sleep(randomisedvalue)
                        self.driver.find_element("id","next-btn").click()
                        self.log_message("Next button clicked")
                        self.logger.info("Next button clicked")
                        time.sleep(2)
                    elif check_constellation_question()==True:
                        choices=self.driver.find_elements(By.CLASS_NAME,"choice ")
                        self.log_message("Constellation question, answering as A")
                        self.logger.info("Constellation question, answering as A")
                        time.sleep(2)
                        self.log_message(f"choices 0  {choices[0]}")
                        choices[0].click()
                    elif check_exists_by_class("letter-wrapper"):
                        self.log_message("Wrting question")
                        self.logger.info("Writing question")
                        for char in self.word:
                            self.driver.find_element("id", "choice").send_keys(char)
                            time.sleep(0.3)
                        self.log_message(f"Ansered as {str(self.word)}")
                        self.logger.info("Ansered as aaaaa")
                    elif check_exists_by_id("Click_me_to_stop"):
                        self.log_message("Session end")
                        self.logger.info("Session end")
                        self.driver.find_element("id","Click_me_to_stop").click()
                        time.sleep(2)

                        self.log_message("Session ended")
                        self.logger.info("Session ended")

                        break
                    else:
                        if ct == 1:
                            try:
                                abc = self.driver.find_element(By.CLASS_NAME,"question").text
                                cba = self.driver.find_elements(By.CLASS_NAME,"choice ")
                            except NoSuchElementException:
                                self.log_message(f"Login credentials incorrect Email = '{email}' , Password = '{password}'")
                                self.logger.info(f"Login credentials incorrect Email = '{email}' , Password = '{password}'")
                                return

                        executeSolveQuestionNormal()
            except Exception as e:
                try:
                    self.driver.save_screenshot("error.png")
                except:
                    self.log_message("Unable to take an error screenshot")
                    self.logger.info("Unable to take an error screenshot")
                self.log_message("Code has ended with an error")
                self.logger.info("Code has ended with an error")
                self.log_message(str(e))
                self.logger.info(str(e))

            finally:
                self.stop()


        mainFunction()
