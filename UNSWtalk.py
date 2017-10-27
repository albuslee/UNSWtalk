#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re, shutil
import logging
from collections import defaultdict
from flask import Flask, render_template, session, request, redirect, url_for, escape

students_dir = "dataset-medium";

app = Flask(__name__)

# Show unformatted details for student "n"
# Increment n and store it in the session cookie

@app.route('/', methods=['GET','POST'])
def index():
    # 判断本次请求的session中是否包含有 'username'属性
    if 'zid' in session:
        session.clear()
        return render_template('login.html')
    return 'You are not logged in'
@app.route('/login', methods=['GET','POST'])
def login():
    global password_book
    global friend_list
    zid = request.form.get('zid', '')
    zid = re.sub(r'\D', '', zid)
    session['zid'] = zid
    password = request.form.get('password', '')
    print(password)
    if zid in password_book and password == password_book[zid][0]:
        return render_template('home.html', friend_list = friend_list[zid], password_book = password_book)
    return render_template('login.html')

@app.route('/home/<zid>', methods=['GET','POST'])
def start(zid):
    n = session.get('n', 0)
    students = sorted(os.listdir(students_dir))
    student_to_show = students[n % len(students)]
    app.logger.info(student_to_show)
    details_filename = os.path.join(students_dir, student_to_show, "student.txt")
    with open(details_filename) as f:
        details = f.read()
    session['n'] = n + 1
    return render_template('home.html', friend_list = friend_list[zid], password_book = password_book)

@app.route('/result', methods=['GET','POST'])
def result():
    global password_book
    global name_to_zid
    zid_list = []
    name = request.args.get('sch_friend')
    print(name)
    for i in name_to_zid:
        if re.search(name, i, re.IGNORECASE):
            print(i)
            zid_list.append(name_to_zid[i])
    return render_template('result.html', zid_list = zid_list, password_book = password_book)
    

# get password of every studens
password_book = defaultdict()
friend_list = defaultdict()
name_to_zid = defaultdict()
students = sorted(os.listdir(students_dir))
for i in range(len(students)):
    friends = None
    student_to_show = students[i]
    directory = os.path.join("static", "img")
    img_filename = os.path.join(students_dir, student_to_show, "img.jpg")
    details_filename = os.path.join(students_dir, student_to_show, "student.txt")
    file = open(details_filename, 'r')
    for line in file:
        a = re.match(r"zid:\sz(\d+)", line)
        b = re.match(r"password:\s(.+)", line)
        c = re.match(r"friends:\s\((.+)\)", line)
        d = re.match(r"full_name:\s(.+)", line)
        if a:
            zid = a.group(1)
        if b:
            ps = b.group(1)
        if c:
            friends = c.group(1)
        if d:
            full_name = d.group(1)
    if not os.path.exists(directory):
        os.makedirs(directory)
    dst = os.path.join("static", "img", zid+".jpg")
    print(dst)
    try:
        shutil.copyfile(img_filename, dst)
        print("COPY")
    except FileNotFoundError:
        app.logger.info(img_filename+"doesn't exist.")

    password_book[zid] = [ps, full_name]
    friend_list[zid] = [x.strip() for x in friends.split(',')]
    friend_list[zid] = [re.sub(r'\D', '', x) for x in friend_list[zid]]
    name_to_zid[full_name] = zid
print(password_book)




if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True, use_reloader=True)
