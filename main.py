import schedule, sqlite3, threading, time, psutil, os, sys, datetime
from pynotifier import Notification

try:
    from PyQt5.QtWinExtras import QtWin
    myappid = 'darkmode.python.scheudule.program'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)    
except ImportError:
    pass

def resource_path(relative_path):
    """is used for pyinstaller so it can read the relative path"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

db = resource_path('./db/bandwidth.db')
logoico = resource_path('./gui/logo.ico')
logopng = resource_path('./gui/logo.png')

try:
    if not os.path.isfile(db):
        os.mkdir('./db/')
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE results (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        net_in INTEGER,
        net_out INTEGER,
        resulttime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )''')
        conn.commit()
        conn.close()
    else:
        pass
except FileExistsError:
    pass
    


class Database():
    """Used to insert and select data from the SQLite3 database"""

    def insertData(self, net_in, net_out):
        """insert data to the database"""
        try:
            sqliteConnection = sqlite3.connect(db)
            c = sqliteConnection.cursor()

            sqlite_insert_with_param = """INSERT INTO results 
            (net_in, net_out) 
            VALUES (?,?);"""

            data_tuple = (net_in,net_out)
            c.execute(sqlite_insert_with_param, data_tuple)
            sqliteConnection.commit()

            c.close()

        except sqlite3.Error as error:
            print("Failed to insert Python variable into sqlite table", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()


class ContinuousScheduler(schedule.Scheduler):
    """this is a class which uses inheritance to act as a normal Scheduler,
        but also can run_continuously() in another thread"""
        #https://stackoverflow.com/questions/46453938/python-schedule-library-needs-to-get-busy-loop
    def run_continuously(self, interval=1):
            """Continuously run, while executing pending jobs at each elapsed
            time interval.
            @return cease_continuous_run: threading.Event which can be set to
            cease continuous run.
            Please note that it is *intended behavior that run_continuously()
            does not run missed jobs*. For example, if you've registered a job
            that should run every minute and you set a continuous run interval
            of one hour then your job won't be run 60 times at each interval but
            only once.
            """
            cease_continuous_run = threading.Event()

            class ScheduleThread(threading.Thread):
                """The job that should run continuous"""
                @classmethod
                def run(cls):
                    # I've extended this a bit by adding self.jobs is None
                    # now it will stop running if there are no jobs stored on this schedule
                    while not cease_continuous_run.is_set() and self.jobs:
                        # for debugging
                        # print("ccr_flag: {0}, no. of jobs: {1}".format(cease_continuous_run.is_set(), len(self.jobs)))
                        self.run_pending()
                        time.sleep(interval)

            continuous_thread = ScheduleThread()
            continuous_thread.start()
            return cease_continuous_run


def message(info):
    """Notifications to the user"""
    name = "Bandwidth Monitor"
    try:
        if os.name == 'posix':
            os.system("""
                    osascript -e 'display notification "{}" with title "{}"'
                    """.format(info, name))
        elif os.name == 'nt':
            Notification(
                title=name,
                description=info,
                icon_path=logoico,
                duration=3,
                urgency=Notification.URGENCY_CRITICAL
            ).send()
        else:
            Notification(
                title=name,
                description=info,
                icon_path=logopng, 
                duration=3,
                urgency=Notification.URGENCY_CRITICAL
            ).send()
    except Exception:
        pass

def net_usage():
    send = Database()

    while True:
        net_stat = psutil.net_io_counters()
        net_in_1 = net_stat.bytes_recv
        net_out_1 = net_stat.bytes_sent

        time.sleep(0.75)

        net_stat = psutil.net_io_counters()
        net_in_2 = net_stat.bytes_recv
        net_out_2 = net_stat.bytes_sent

        net_in = round((net_in_2 - net_in_1) / 1024 / 1024, 3)
        net_out = round((net_out_2 - net_out_1) / 1024 / 1024, 3)

        print(f"Current net-usage IN: {net_in} MB/s, OUT: {net_out} MB/s")

        if net_in > 0.003:
            send.insertData(net_in, net_out)
        elif net_out > 0.003:
            send.insertData(net_in, net_out)



thread = threading.Thread(target=net_usage)
#mess_thr = threading.Thread(target=message)
#monitor = ContinuousScheduler()
#monitor.every(1).seconds.do(net_usage)
#monitor.run_continuously()

thread.start()
#mess_thr.start()

message("Bandwidth Monitor running - saving data to database!")
