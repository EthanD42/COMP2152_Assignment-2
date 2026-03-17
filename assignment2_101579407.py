"""
Author: Ethan Dennis
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import socket
import threading
import sqlite3
import os
import platform
import datetime

# TODO: Print Python version and OS name (Step iii)
print(f"Python Version: {platform.python_version()}")
print(f"Operating System:", os.name)

# TODO: Create the common_ports dictionary (Step iv)
# Add a 1-line comment above it explaining what it stores

# This dictionary stores common port numbers and their respective service names
common_ports =  {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}


# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"


class NetworkTool:
    def __init__(self, target):
        self.__target = target

# Q3: What is the benefit of using @property and @target.setter?
# TODO: Your 2-4 sentence answer here... (Part 2, Q3)
# 
# Q3: The decorator and the setter method allow us to control access to the private attribute of __target.
#  By using @property, we can define a getter method that makes it so we can  use it  to retrieve the value of target while at the same time, keeping it encapsulated.
#  The @target.setter makes it so  we can  add validation logic when setting the value of target,
#  therefore making sure  that it cannot be set to an empty string. This helps  to have  better data integrity and encapsulation for our class.


    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value == "":
            return
        self.__target = value

    def __del__(self):
        print("NetworkTool instance  has been destroyed")



# Q1: How does PortScanner reuse code from NetworkTool?
# TODO: Your 2-4 sentence answer here... (Part 2, Q1)

# Q1: The PortScanner class inherits from the NetworkTool parent class, which makes it so it can reuse the __init__, 
# target getter/setter, and __del__ methods without having to rewrite them.
#  like for example, PortScanner calls super().__init__(target) to initialize the private __target attribute and use the validation logic already defined in the  NetworkTool.
#  This inheritance makes sure  that PortScanner automatically enforces the same rules for setting and accessing the target IP, so programmers do not have to write the same code twice.
#  It also allows PortScanner to extend functionality with scanning methods while keeping the core network handling consistent.



# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)
# - Constructor: call super().__init__(target), initialize self.scan_results = [], self.lock = threading.Lock()
# - Destructor: print "PortScanner instance destroyed", call super().__del__()

class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance has been destroyed")
        super().__del__()

    def scan_port(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            result = sock.connect_ex((self.target, port))

            if result == 0:
                status = "Open"
            else:
                status = "Closed"

            service_name = common_ports.get(port, "Unknown")

            self.lock.acquire()
            self.scan_results.append((port, status, service_name))
            self.lock.release()

        except socket.error as e:
            print(f" a Socket error has occured  on port {port}: {e}")

        finally:
            sock.close()

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

    def scan_range(self, start_port, end_port):
        threads = []

        for port in range(start_port, end_port + 1):
            t = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()


# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error

def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                port INTEGER,
                status TEXT,
                service TEXT,
                scan_date TEXT
            )
        """)

        for port, status, service in results:
            cursor.execute("""
                INSERT INTO scans (target, port, status, service, scan_date)
                VALUES (?, ?, ?, ?, ?)
            """, (target, port, status, service, datetime.datetime.now()))

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print(f" a SQLite error has occured: {e}")


# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection

def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()

        for row in rows:
            print(f"[{row[5]}] {row[1]} --- Port {row[2]}: {row[4]} ({row[3]})")

        conn.close()

    except sqlite3.Error:
        print("No past scans were found.")


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    pass
    try:
        target = input("Enter target IP address (default 127.0.0.1): ")
        if not target:
            target = "127.0.0.1"

        start_port = int(input("Enter start port (1-1024): "))
        end_port = int(input("Enter end port (1-1024): "))

        if not (1 <= start_port <= 1024) or not (1 <= end_port <= 1024):
            raise ValueError("The port must be between 1 and 1024.")

        if end_port < start_port:
            raise ValueError("The end port must be greater than or equal to the start port.")

        scanner = PortScanner(target)
        print(f"Scanning {target} from port {start_port} to {end_port}...")
        scanner.scan_range(start_port, end_port)
        open_ports = scanner.get_open_ports()
        print(f"Scan results for the target {target}:")
        for port, status, service in open_ports:
            print(f"Port {port}: {status} ({service})")
        print(f"Total open ports found: {len(open_ports)}")

        save_results(target, scanner.scan_results)

        see_history = input("Would you like to see past scan history? (yes/no): ").lower()
        if see_history == "yes":
            load_past_scans()

    except ValueError as e:
        print(f"Invalid input: {e}")


# Q5: New Feature Proposal
# TODO: Your 2-3 sentence description here... (Part 2, Q5)

# Q5: One feature I would add is for the program to  automatically hightlight  any open ports that are in the common_ports dictionary. 
# This would make it easier for users to quickly see which important services, like SSH or HTTP, are exposed on the currrent  target machine. 
# It could use a list comprehension to filter scan_results for only the open ports that match keys in common_ports, 
# then display them separately at the top of the results. 


# Diagram: See diagram_studentID.png in the repository root