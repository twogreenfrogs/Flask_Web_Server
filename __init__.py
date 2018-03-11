'''
To do:
1. logo & site title on the top left, then login and signup on the right
2. menus below with bootstrap
3. custom content management system for blogging
4. notification system based on topics <--> database 
5. file download and upload feature
6. login/signup feature
7. pygal graphing
'''
from flask import Flask, render_template, flash, request, redirect, url_for, session, send_file, jsonify, make_response, Response
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mail import Mail, Message
from utilities import *
from werkzeug import secure_filename
from flask_httpauth import HTTPBasicAuth
import pygal
import os
import collections
import psutil
import requests

DEBUG = True

dict_metrics = collections.defaultdict(int)
app = Flask(__name__)
app.secret_key = 'many random bytes'

### video stream handling ######################################################
def gen():
    while True:
        print 'before---'
        frame = requests.get('http://192.168.1.80/img/snapshot.cgi')
        print 'after---'
        print frame.status_code
        print frame.headers
        yield (b'--ThisRandomString\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.text + b'\r\n')

@app.route('/video_feed/')
def video_feed():
    #http://70.133.220.13/img/video.mjpeg
    return redirect("http://192.168.1.80/img/video.mjpeg", code=302)
    #return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=ThisRandomString')
    
### basic auth handling ############################################################

auth = HTTPBasicAuth()
@auth.get_password
def get_password(username):
    if username == 'admin':
        return 'tch123'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

### user login handling ############################################################   
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'logged_in' in session:
            return func(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))
    return wrapper

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('/home/'))
        
        
class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the Terms of Service', [validators.Required()])
        
@app.route('/login/', methods=["GET","POST"])
def login():
    error = ''
    try:
        c, conn = connection()
        if request.method == "POST":

            data = c.execute("SELECT * FROM users WHERE username = (%s)",
                            (thwart(request.form['username']),))
            
            data = c.fetchone()[2]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                flash("You are now logged in")
                return redirect(url_for("python_programming"))

            else:
                error = "Invalid credentials, try again."

        gc.collect()

        return render_template("login.html", error=error)

    except Exception as e:
        flash(e)
        error = "Invalid credentials, try again."
        return render_template("login.html", error = error)  


#register new user: userid, password
#register new event: event_name, emails, sms_nums, twitter 
#register new blog: title, category, subcategory, summary, blog_file, tags
#register new metric: device_name, metric_name1, metric_name2, metric_name3 etc.

@app.route('/register/', methods=["GET","POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    register_type = request.form['register_type']
    print "***", register_type
    
    if request.method == "POST" and register_type == 'account':
        try:
            form = RegistrationForm(request.form)
    
            if request.method == "POST" and form.validate():
                username  = form.username.data
                email = form.email.data
                password = sha256_crypt.encrypt((str(form.password.data)))
                c, conn = connection()
    
                x = c.execute("SELECT * FROM users WHERE username = (%s)",
                              (thwart(username),))
    
                if int(x) > 0:
                    flash("That username is already taken, please choose another")
                    return render_template('register.html', form=form)
    
                else:
                    c.execute("INSERT INTO users (username, password, email, tracking) VALUES (%s, %s, %s, %s)",
                              (thwart(username), thwart(password), thwart(email), thwart("/introduction-to-python-programming/")))
                    
                    conn.commit()
                    flash("Thanks for registering!")
                    c.close()
                    conn.close()
                    gc.collect()
    
                    session['logged_in'] = True
                    session['username'] = username
    
                    return redirect(url_for('python_programming'))
                
            return render_template("register.html", form=form)
    
        except Exception as e:
            return(str(e))    

    elif request.method == "POST" and register_type == 'blog':
        #update new blog in database
        #INSERT INTO blogs_data ( title, category, subcategory, summary, blog_file, tags, date ) VALUES ('REST API design smmmary', 'python_programming', '', 'This blog quickly explains REST API design, available HTTP Methods, and how to use them.\nRead more...', 'rest_api_design_summary.html', 'python', NOW() );
        title = request.form['b_title']
        category = request.form['b_category']
        subcategory = request.form['b_subcategory']
        summary = request.form['b_summary']
        blog_file = request.form['b_blog_file']
        tags = request.form['b_tags']
        print title, category, subcategory, summary, blog_file, tags
        
        try:
            with Database(host='localhost', db='blogs_data') as cursor:
                cursor.execute("SELECT * FROM blogs_data where title='{}';".format(title))
                if cursor.fetchone():
                    flash('Error: title already exist. Try different title')
                    return render_template("register.html")
                            
                query_str = "INSERT INTO blogs_data (title, category, subcategory, summary, blog_file, tags, date) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', NOW() );".format(
                                                                                                                                          title,
                                                                                                                                          category,
                                                                                                                                          subcategory,
                                                                                                                                          summary,
                                                                                                                                          blog_file,
                                                                                                                                          tags,
                                                                                                                                          )
                print 'query_str:', query_str   
                cursor.execute(query_str)
                flash('Success: blog registered OK!!!')
                return render_template("register.html")
                        
        except Exception as e:
            return(str(e)) 

    elif request.method == "POST" and register_type == 'event':
        #INSERT INTO events ( event_name, emails, sms_nums, twitters ) VALUES ("3G_OVERAGE", "test@test.com", "+14044404", 1);
        event_name = request.form['e_event_name']
        emails = request.form['e_emails']
        sms_nums = request.form['e_sms_nums']
        twitters = 1 if request.form['e_twitter'] else 0
        print event_name, emails, sms_nums, twitters
        
        try:
            with Database(host='localhost', db='events') as cursor:
                cursor.execute("SELECT * FROM events where event_name='{}';".format(event_name))
                if cursor.fetchone():
                    flash('Error: Event exist already!!!')
                    return render_template("register.html")
                            
                query_str = "INSERT INTO events (event_name, emails, sms_nums, twitters) VALUES ('{}', '{}', '{}', '{}');".format(event_name,
                                                                                                                                  emails,
                                                                                                                                  sms_nums,
                                                                                                                                  twitters,
                                                                                                                                  )
                print 'query_str:', query_str   
                cursor.execute(query_str)
                flash('Success: Event registered OK!!!')
                return render_template("register.html")
                        
        except Exception as e:
            return(str(e)) 
                

### rest API handling ############################################################   
# get all events
@app.route('/api/events/', methods=['GET'])
@auth.login_required
def get_events():
    with Database(host='localhost', user=SQL_USERNAME, passwd=SQL_PASSWORD, db='events') as cursor:
        cursor.execute("SELECT * FROM events;")
        results = cursor.fetchall()
        events = []
        for result in results:
            event_dict = {}
            event_dict['event_name'] = result[1]
            event_dict['emails'] = result[2].split(',')     # 'email1, email2, email3' in Database. Convert it to list
            event_dict['sms_nums'] = result[3].split(',') # 'sms1, sms2, sms3' in Database. Convert it to list
            event_dict['twitter'] = True if int(result[4]) == 1 else False  # '1' or '0' in Database. Convert it to Boolean
            events.append(event_dict)
    return jsonify({'events': events})

# get individual event
@app.route('/api/events/<string:event_name>/', methods=['GET'])
@auth.login_required
def get_event(event_name):
    with Database(host='localhost', user=SQL_USERNAME, passwd=SQL_PASSWORD, db='events') as cursor:
        query_str = "SELECT * FROM events where event_name='{}';".format(event_name)
        cursor.execute(query_str)
        result = cursor.fetchone()

        if len(result) == 0:
            return jsonify({'error': 'event not found'})
        else:
            event_dict = {}
            event_dict['event_name'] = result[1]
            event_dict['emails'] = result[2].split(',') 
            event_dict['sms_nums'] = result[3].split(',')
            event_dict['twitter'] = True if int(result[4]) == 1 else False          
            return jsonify({'event': event_dict})

# create event
@app.route('/api/events/', methods=['POST'])
@auth.login_required
def create_event():
    if not request.json or not 'event_name' in request.json:
        return jsonify({'error': 'no event_name'}) 
    
    new_event = {
        'event_name': request.json['event_name'],
        'emails': ','.join(request.json.get('emails', "")),          # convert list to string
        'sms_nums': ','.join(request.json.get('sms_nums', "")),      # convert list to string
        'twitters': 1 if request.json.get('twitters', False) else 0, # convert Booleaan to 1/0
    }

    with Database(host='localhost', user=SQL_USERNAME, passwd=SQL_PASSWORD, db='events') as cursor:
        cursor.execute("SELECT * FROM events where event_name='{}';".format(request.json['event_name']))
        if cursor.fetchone():
            return jsonify({'error': 'event_name already exist'}) 
                    
        query_str = "INSERT INTO events (event_name, emails, sms_nums, twitters) VALUES ('{}', '{}', '{}', '{}');".format(new_event['event_name'],
                                                                                                                          new_event['emails'],
                                                                                                                          new_event['sms_nums'],
                                                                                                                          new_event['twitters'],
                                                                                                                          )
        print 'query_str:', query_str   
        cursor.execute(query_str)

        cursor.execute("SELECT * FROM events;")
        results = cursor.fetchall()
        events = []
        for result in results:
            event_dict = {}
            event_dict['event_name'] = result[1]
            event_dict['emails'] = result[2].split(',') 
            event_dict['sms_nums'] = result[3].split(',') 
            event_dict['twitter'] = True if int(result[4]) == 1 else False 
            events.append(event_dict)               

    return jsonify({'events': events})

# update event: Need to remove duplicates
@app.route('/api/events/<string:event_name>/', methods=['PUT'])
@auth.login_required
def update_event(event_name):
    if not request.json:
        return jsonify({'error': 'not json data'})

    with Database(host='localhost', user=SQL_USERNAME, passwd=SQL_PASSWORD, db='events') as cursor:
        query_str = "SELECT * FROM events where event_name='{}';".format(event_name)
        cursor.execute(query_str)
        result = cursor.fetchone()

        if len(result) == 0:
            return jsonify({'error': 'event not found'})

        existing_event = {
                        'event_name': result[1],
                        'emails': result[2].split(','),                # convert csv string to list
                        'sms_nums': result[3].split(','),              # convert csv string to list
                        'twitters': True if result[4] == 1 else False, # convert Booleaan 
                        }
        
        new_event = {
                    'event_name': request.json['event_name'],
                    'emails': request.json.get('emails', ""),          
                    'sms_nums': request.json.get('sms_nums', ""),      # convert list to string
                    'twitters': request.json.get('twitters', False), # convert Booleaan to 1/0
                    }
    
        # need sanity check for each data(if unicode etc.)
        update_event = {
                        'event_name': existing_event['event_name'],  # don't allow changing event_name
                        'emails': ','.join(list(set(new_event['emails'] + existing_event['emails']))),          
                        'sms_nums': ','.join(list(set(new_event['sms_nums'] + existing_event['sms_nums']))),  
                        'twitters': 1 if new_event['twitters'] else 0                       
                        }
        
        print '***', update_event

        query_str = "UPDATE events set event_name='{}', emails='{}', sms_nums='{}', twitters='{}' where event_name = '{}';".format(update_event['event_name'],
                                                                                                                                   update_event['emails'],
                                                                                                                                   update_event['sms_nums'],
                                                                                                                                   update_event['twitters'],
                                                                                                                                   event_name,
                                                                                                                                   )
        print 'query_str:', query_str   
        cursor.execute(query_str)
    
        query_str = "SELECT * FROM events where event_name='{}';".format(event_name)
        cursor.execute(query_str)
        result = cursor.fetchone()

        if len(result) == 0:
            return jsonify({'error': 'event not found'})
        else:
            event_dict = {}
            event_dict['event_name'] = result[1]
            event_dict['emails'] = result[2].split(',')
            event_dict['sms_nums'] = result[3].split(',')
            event_dict['twitter'] = True if result[4] == 1 else False
               
            print '***event_dict', event_dict       
            return jsonify({'event': event_dict})

# delete event
@app.route('/api/events/<string:event_name>/', methods=['DELETE'])
@auth.login_required
def delete_event(event_name):
    # assume already authenticated. So execute
    with Database(host='localhost', user=SQL_USERNAME, passwd=SQL_PASSWORD, db='events') as cursor:
        query_str = "SELECT * FROM events where event_name='{}';".format(event_name)
        cursor.execute(query_str)
        result = cursor.fetchone()

        if result is None:
            return jsonify({'error': 'event not found'})
        
        query_str = "DELETE FROM events WHERE event_name='{}';".format(event_name)
        print 'delete query:', query_str
        cursor.execute(query_str)
        
        # check if this event is gone
        query_str = "SELECT * FROM events where event_name='{}';".format(event_name)
        print 'select query:', query_str
        cursor.execute(query_str)
        result = cursor.fetchone()
        print 'delete result:', result
        if result is None:
            return jsonify({'result': True})
        else:
            return jsonify({'result': False})
        
# trigger event(sms, email, twitter)
@app.route('/api/events/trigger/<string:event_name>', methods=['POST'])
@auth.login_required
def trigger_event(event_name):
    query_str = "SELECT * FROM events where event_name='{}';".format(event_name)
    print 'select query:', query_str
    
    with Database(host='localhost', user=SQL_USERNAME, passwd=SQL_PASSWORD, db='events') as cursor:
        cursor.execute(query_str)
        result = cursor.fetchone()
        if result is None:
            return jsonify({'error': 'event not found'})
        
        emails = result[2].split(',')
        sms_nums = result[3].split(',')
        
        print 'targets', request.json['targets']
        if 'email' in request.json.get('targets', ''):
            for email in emails:
                print 'send email to {}'.format(email)
            
        if 'sms' in request.json.get('targets', ''):
            for sms_num in sms_nums:
                print 'send sms to {}'.format(sms_num)
    
        if 'twitters' in request.json.get('targets', ''):
            print 'send twitter'
    
    return jsonify({'result': True})

### file sharing handling ######################################################
@try_except  
@app.route('/upload/',methods = ['POST'])
def upload_file():
    print 'got upload request...'
    if request.method =='POST':
        print 'parsing filename...'
        file = request.files['file']
        print 'filename:', file
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join('/var/www/FlaskApp/FlaskApp/static/upload',filename))
            message = 'file: {} uploaded successfully !!!'.format(filename)
    return render_template("sharing_and_fun.html", message=message)

### graphing data ##############################################################
@try_except
@app.route('/pygalexample/')
def pygalexample():
    # AJAX invoke this, collect new data and display new graph
    data = fetch_data()
    
    #contstruct graph from fetched data
    graph = pygal.Line()
    graph.title = '% Change Coolness of programming languages over time.'
    graph.x_labels = ['2011','2012','2013','2014','2015','2016']
    graph.add('Python',  [15, 31, 89, 200, 356, 900])
    graph.add('Java',    [15, 45, 76, 80,  91,  95])
    graph.add('C++',     [5,  51, 54, 102, 150, 201])
    graph.add('All others combined!',  [5, 15, 21, 55, 92, 105])
    graph_data = graph.render_data_uri()
    return render_template("graphing.html", graph_data = graph_data)

@try_except
@app.route('/metric/<string:graph_file>')
def graph(graph_file):
    """
    This graph file fetches metric using Ajax and plot chart
    """
    return render_template(graph_file)

@try_except
@app.route('/metric/', methods = ['GET', 'POST'])
def metric():
    #POST updates data.
    #GET returns data for plotting in client side
    """
    POST JSON format:
    { 'metric_name1': 'metric_value1',
      'metric_name2': 'metric_value2',
      'metric_name3': 'metric_value3',
    }
    return:
    {'error': False/True}
    ======
    GET JSON(or support URL encording??) format:
    {metric_names: [metric_name1, metric_name2, metric_name3]
    return:
    {'error': False/True}
    {'metric_name1':metric_value1, 'metric_name2': metric_value2, 'metric_name3': metric_value3]
    """
    global dict_metrics
    if request.method == 'GET':
        #print 'metric_names:', request.json['metric_names']
        #print 'request.args:', request.args
        data = collections.defaultdict(int)
        for key in request.args:
            metric_name = request.args.get(key)
            if metric_name == 'cpuUsage':
                #data[metric_name] = random.randint(1, 100)
                data[metric_name] = psutil.cpu_percent()
            elif metric_name == 'memoryUsage':
                data[metric_name] = psutil.virtual_memory().percent
            elif metric_name == 'diskUsage':
                data[metric_name] = (float(psutil.disk_usage('/').used)/psutil.disk_usage('/').total) * 100
            if metric_name == 'dlcCpuUsage':
                data[metric_name] = dict_metrics[metric_name]
            elif metric_name == 'dlcMemoryUsage':
                data[metric_name] = dict_metrics[metric_name]
            elif metric_name == 'dlcDiskUsage':
                data[metric_name] = dict_metrics[metric_name]
        #print 'return data:', data
        return jsonify(data)
    
    elif request.method == 'POST':
        try:
            print request.json
            for key, val in request.json.items():
                dict_metrics[key] = request.json[key]
        except Exception as err:
            print err
            return jsonify({'error': True})
        else:
            return jsonify({'error': False})
    else:
        pass
                    
### front-end pages ############################################################
@try_except    
@app.route('/')
@app.route('/home/')
def homepage():
    blogs = []
    #construct blogs from Database
    with Database(host='localhost', db='blogs_data') as cursor:
        cursor.execute("SELECT * from blogs_data ORDER BY date DESC LIMIT 9;")
        rows = cursor.fetchall()
        blogs = []
        for row in rows:
            # title, category, subcategory, summary, blog_file, tags, date
            blog = {}
            blog['title'] = row[1]
            blog['category'] = row[2]
            blog['subcategory'] = row[3]
            blog['summary'] = row[4]
            blog['blog_file'] = row[5]
            blog['tags'] = row[6]
            blog['date'] = row[7]
            blogs.append(blog)
    pprint(blogs)
    return render_template("home.html", blogs=blogs)

@try_except
@app.route('/python_programming/')
def python_programming():
    blogs = []
    #construct blogs from Database
    with Database(host='localhost', db='blogs_data') as cursor:
        cursor.execute("SELECT * FROM blogs_data where category='python_programming' ORDER BY date DESC LIMIT 9;")
        rows = cursor.fetchall()
        blogs = []
        for row in rows:
            # title, category, subcategory, summary, blog_file, tags, date
            blog = {}
            blog['title'] = row[1]
            blog['category'] = row[2]
            blog['subcategory'] = row[3]
            blog['summary'] = row[4]
            blog['blog_file'] = row[5]
            blog['tags'] = row[6]
            blog['date'] = row[7]
            blogs.append(blog)
    pprint(blogs)
    return render_template("python_programming.html", blogs=blogs)

@try_except    
@app.route('/shell_programming/')
def shell_programming():
    blogs = []
    #construct blogs from Database
    with Database(host='localhost', db='blogs_data') as cursor:
        cursor.execute("SELECT * FROM blogs_data where category='shell_programming' ORDER BY date DESC LIMIT 9;")
        rows = cursor.fetchall()
        blogs = []
        for row in rows:
            # title, category, subcategory, summary, blog_file, tags, date
            blog = {}
            blog['title'] = row[1]
            blog['category'] = row[2]
            blog['subcategory'] = row[3]
            blog['summary'] = row[4]
            blog['blog_file'] = row[5]
            blog['tags'] = row[6]
            blog['date'] = row[7]
            blogs.append(blog)
    pprint(blogs)
    return render_template("shell_programming.html", blogs=blogs)

@try_except    
@app.route('/c_programming/')
def c_programming():
    blogs = []
    #construct blogs from Database
    with Database(host='localhost', db='blogs_data') as cursor:
        cursor.execute("SELECT * FROM blogs_data where category='c_programming' ORDER BY date DESC LIMIT 9;")
        rows = cursor.fetchall()
        blogs = []
        for row in rows:
            # title, category, subcategory, summary, blog_file, tags, date
            blog = {}
            blog['title'] = row[1]
            blog['category'] = row[2]
            blog['subcategory'] = row[3]
            blog['summary'] = row[4]
            blog['blog_file'] = row[5]
            blog['tags'] = row[6]
            blog['date'] = row[7]
            blogs.append(blog)
    pprint(blogs)
    return render_template("c_programming.html", blogs=blogs)

@try_except
@app.route('/embedded_system/')
def embedded_system():
    blogs = []
    #construct blogs from Database
    with Database(host='localhost', db='blogs_data') as cursor:
        cursor.execute("SELECT * FROM blogs_data where category='embedded_system' ORDER BY date DESC LIMIT 9;")
        rows = cursor.fetchall()
        blogs = []
        for row in rows:
            # title, category, subcategory, summary, blog_file, tags, date
            blog = {}
            blog['title'] = row[1]
            blog['category'] = row[2]
            blog['subcategory'] = row[3]
            blog['summary'] = row[4]
            blog['blog_file'] = row[5]
            blog['tags'] = row[6]
            blog['date'] = row[7]
            blogs.append(blog)
    pprint(blogs)
    return render_template("embedded_system.html", blogs=blogs)

@try_except
@app.route('/tools_tips/')
def tools_tips():
    blogs = []
    #construct blogs from Database
    with Database(host='localhost', db='blogs_data') as cursor:
        cursor.execute("SELECT * FROM blogs_data where category='tools_tips' ORDER BY date DESC LIMIT 9;")
        rows = cursor.fetchall()
        blogs = []
        for row in rows:
            # title, category, subcategory, summary, blog_file, tags, date
            blog = {}
            blog['title'] = row[1]
            blog['category'] = row[2]
            blog['subcategory'] = row[3]
            blog['summary'] = row[4]
            blog['blog_file'] = row[5]
            blog['tags'] = row[6]
            blog['date'] = row[7]
            blogs.append(blog)
    pprint(blogs)
    return render_template("tools_tips.html", blogs=blogs)

@try_except
@app.route('/sharing_and_fun/')
def sharing_and_fun():
    print 'current dir:', os.getcwd()
    download_folder_files = list_folder_files('/var/www/FlaskApp/FlaskApp/static/download')
    graph = pygal.Line()
    graph.title = '% Change Coolness of programming languages over time.'
    graph.x_labels = ['2011','2012','2013','2014','2015','2016']
    graph.add('Python',  [15, 31, 89, 200, 356, 900])
    graph.add('Java',    [15, 45, 76, 80,  91,  95])
    graph.add('C++',     [5,  51, 54, 102, 150, 201])
    graph.add('All others combined!',  [5, 15, 21, 55, 92, 105])
    graph_data = graph.render_data_uri()
    return render_template("sharing_and_fun.html", download_folder_files=download_folder_files, graph_data = graph_data)

@try_except
@app.route('/blogs/<string:category>/<string:blog_file_name>')
def blogs(category, blog_file_name):
    blog_file = 'blogs/' + category + '/' + blog_file_name
    return render_template(blog_file)


@app.route('/log/')
def tail_logfile():
    root_dir = '/var/log/remote/'
    #logfile = root_dir + ip_addr + '/' + ip_addr + '.log'
    logfile = '/var/log/remote/68.153.78.54/68.153.78.54.log'
    def generate():
        with open(logfile) as f:
            while True:
                yield f.read()
                sleep(1)

    return app.response_class(generate(), mimetype='text/plain')


@try_except
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

                
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
