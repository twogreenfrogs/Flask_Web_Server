import MySQLdb
import gc
import os
from MySQLdb import escape_string as thwart
from pprint import pprint

### SQL examples ######################################################################################
"""
http://cse.unl.edu/~sscott/ShowFiles/SQL/CheatSheet/SQLCheatSheet.html
http://www.tutorialspoint.com/python/python_database_access.htm
mysql --user=root -p
SHOW DATABASES;
CREATE DATABASE events;
USE events;
CREATE TABLE events (uid INT(11) AUTO_INCREMENT PRIMARY KEY, event_name VARCHAR(50), emails VARCHAR(1000), sms_nums VARCHAR(1000), twitters tinyint(1));
INSERT INTO events ( event_name, emails, sms_nums, twitters ) VALUES ("3G_OVERAGE", "test@test.com", "+14044404", 1);
SELECT * FROM events;
SELECT * FROM events where event_name='3G_OVERAGE';
UPDATE events SET emails='test@test.com, test1@test.com', sms_nums='+14041111' WHERE event_name='UPGRADE_FAIL';
DELETE FROM events WHERE event_name='3G_OVERAGE';

blog meta data:
CREATE DATABASE blogs_data;
USE blogs_data
CREATE TABLE blogs_data (blog_id INT(11) AUTO_INCREMENT PRIMARY KEY, title VARCHAR(100), category VARCHAR(100), subcategory VARCHAR(100), summary VARCHAR(1000), blog_file VARCHAR(100), tags VARCHAR(100), date DATE);                                        
SHOW TABLES in blogs_data;
INSERT INTO blogs_data ( title, category, subcategory, summary, blog_file, tags, date ) VALUES ('REST API design smmmary', 'python_programming', '', 'This blog quickly explains REST API design, available HTTP Methods, and how to use them.\nRead more...', 'rest_api_design_summary.html', 'python', NOW() );
INSERT INTO blogs_data ( title, category, subcategory, summary, blog_file, tags, date ) VALUES ('Upload files to dropbox', 'python_programming', '', 'Sometimes moving files around is time-consuming and tedious in corporate network due to many security measures.\nThis is simple script to upload files to Dropbox using script.\nRead more...', 'upload_files_to_dorpbox.html', 'python', NOW() );
INSERT INTO blogs_data ( title, category, subcategory, summary, blog_file, tags, date ) VALUES ('Simple custom Shell in C', 'c_programming', '', 'Here is how to implement simple custom shell in C.\nRead more...', 'custom_clash_shell.html', 'c', NOW() );
INSERT INTO blogs_data ( title, category, subcategory, summary, blog_file, tags, date ) VALUES ('How to automate JIRA update', 'python_programming', '', 'This blog quickly explains how to use jira python module to interact with JIRA REST API\nRead more...', 'automate_jira_rest_api.html', 'python', NOW() );
INSERT INTO blogs_data ( title, category, subcategory, summary, blog_file, tags, date ) VALUES ('Find failure point when Internet fails', 'shell_programming', '', 'This shell script is to find failure node when Internet connection fails\nRead more...', 'find_node_of_failure_in_internet.html', 'shell', NOW() );
INSERT INTO blogs_data ( title, category, subcategory, summary, blog_file, tags, date ) VALUES ('Bringing up 3G modem in Linux', 'python_programming', '', 'This blog explains how to bring up 3G modem(Ericsson F5321) in Linux and use for Internet connection.\nRead more...', 'rest_api_client_class.html', 'python, shell', NOW() );
UPDATE blogs_data SET blog_file='setup_3g_modem_in_linux.html' WHERE title='Bringing up 3G modem in Linux';
UPDATE blogs_data SET blog_file='simulate_dlc_servers.html' WHERE title='dhcp, dns, ntp server simulation with scapy';
commit;
SELECT * from blogs_data ORDER BY date DESC LIMIT 3;
SELECT * FROM blogs_data where category='python_programming' limit 3;
DROP TABLE blog_data;
"""

class Database(object):
    SQL_USERNAME = 'root'
    SQL_PASSWORD = 'DlDlsWn@#3760'
    
    class DB_NONE(Exception):
        """
        Raise DB_NONE Exception
        """
    
    def __init__(self, host='localhost', user=None, passwd=None, db=None):
        self.host = host
        self.user = user or Database.SQL_USERNAME
        self.passwd = passwd or Database.SQL_PASSWORD
        if not db:
            raise DB_NONE("database name: None")
        else:
            self.db = db

    def connect(self):
        self.conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db)
        self.cursor = conn.cursor()
        return self.cursor

    def disconnect(self):
        try:
            self.conn.commit()
        except:
            self.conn.rollback()
            
        self.cursor.close()
        self.conn.close()
        gc.collect()
    
    def execute_and_fetch(self, query_str, all=True):
        try:
            cur.execute(query_str)
        except MySQLdb.Error, e:
            try:
                print "MySQL Error [%d]: %s".format(e.args[0], e.args[1])
            except IndexError:
                print "MySQL Error: %s".format(str(e))
        else:
            rows = cur.fetchall()
            return rows
            
    def __enter__(self):
        self.conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db)
        self.cursor = self.conn.cursor()
        return self.cursor
    
    def __exit__(self, etype, einst, etcb):
        if etype is not None:
            print etype
            print einst
            print etcb
        else:        
            try:
                self.conn.commit()
            except:
                self.conn.rollback()
                
            self.cursor.close()
            self.conn.close()
            gc.collect()


class Notification(object):
    TWILIO_SID = ""
    TWILIO_TOKEN = ""
    TO_CELLNUM = ""
    FROM_CELLNUM = ""
    
    EMAIL_USERNAME = ''
    EMAIL_PASSWORD = ''
    
    TWITTER_KEY = ''
    TWITTER_SECRET = ''
    TWITTER_TOKEN = ''
    TWITTER_TOKEN_SECRET = ''
    
    def __init__(self):
        self.smtpserver = smtplib.SMTP("smtp.live.com", 587)
        self.smtpserver.ehlo()
        self.smtpserver.starttls()
        self.smtpserver.ehlo
        self.smtpserver.login(Notification.EMAIL_USERNAME, Notification.EMAIL_PASSWORD)
        self.twilo = TwilioRestClient(Notification.TWILIO_SID, Notification.TWILIO_TOKEN)
        self.twitter = Twython(Notification.TWITTER_KEY, 
                               Notification.TWITTER_SECRET, 
                               Notification.TWITTER_TOKEN, 
                               Notification.TWITTER_TOKEN_SECRET,
                               )
        
    def send_mail(self, subject='Event Notification', body=None,to_email='inzoolee@hotmail.com'):
        try:
            header = 'To:' + to_email + '\n' + 'From: ' + EMAIL_USER
            header = header + '\n' + 'Subject: ' + subject + '\n'
            msg = header + '\n' + body + ' \n\n'
            self.smtpserver.sendmail(EMAIL_USERNAME, to_email, msg)
            self.smtpserver.close()
            return True
        except:
            return False
    
    def send_twitter(txt='Event Notification'):
        try:
            self.twitter.update_status(status=txt)
            return True
        except:
            return False    
    
    def send_sms(txt='Event Notification'):
        try:
            message = self.twilo.messages.create(to=sms, from_=FROM_CELLNUM, body=txt)
            return True 
        except:
            return False

### utility functions ######################################################################
def list_folder_files(path=None):
    from os import listdir
    from os.path import isfile, join
    folder_files = [f for f in os.listdir(path) if os.path.isfile(join(path, f))]
    return folder_files

def try_except(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            err_msg = 'In func: {} <br>'.format(func.__name__)
            err_msg += str(err)
            return (err_msg)
    return wrapper


def dprint(*args, **kwargs):
    #dprint( 'var1 value: {var1}', 'var2 value: {var2}', var1=1, var2=2 )
    #output: var1 value: 1, var2 value:2
    if DEBUG == True:
        try:
            print ', '.join(args).format(**kwargs)
        except KeyError:
            # deal with missing keys
            class format_dict(dict):
                def __missing__(self, key):
                    return '...'
            missing_kwargs = format_dict(kwargs) 
            print ', '.join(args).format(**missing_kwargs)
    
if __name__ == '__main__':
    dprint('val1: {val1}, val2: {val2}', val1=1, val2=2)
    sys.exit(0)
    
    # unittest
    with Database(host='localhost', user=SQL_USERNAME, passwd=SQL_PASSWORD, db='events') as cursor:
        cursor.execute("SELECT * FROM events;")
        results = cursor.fetchall()
        events = []
        for result in results:
            event_dict = {}
            event_dict['event_name'] = result[1]
            event_dict['emails'] = result[2]
            event_dict['sms_nums'] = result[3]
            events.append(event_dict)

    print events
    print

    # unittest
    with Database(host='localhost', user=SQL_USERNAME, passwd=SQL_PASSWORD, db='frogs') as cursor:
        cursor.execute("SELECT * FROM users;")
        results = cursor.fetchall()
        events = []
        for result in results:
            event_dict = {}
            event_dict['username'] = result[1]
            event_dict['password'] = result[2]
            event_dict['email'] = result[3]
            event_dict['settings'] = result[4]
            event_dict['trackning'] = result[5]
            event_dict['rank'] = result[6]
            events.append(event_dict)

    print events 
        
        
