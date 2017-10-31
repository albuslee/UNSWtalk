#!/web/cs2041/bin/python3.6.3


# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re, shutil, datetime, time
import logging
from collections import defaultdict
from flask import Flask, flash, render_template, session, request, redirect, url_for, escape
from jinja2 import evalcontextfilter, Markup, escape
from werkzeug import secure_filename

students_dir = "dataset-medium";
UPLOAD_FOLDER = os.path.join("static", "img")
app = Flask(__name__)
# directory save upload img
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# translate zid into full name with link
@app.template_filter('id2nm')
def id2nm_filter(s):
    global password_book
    ids = re.findall(r'z(\d+)', s)
    for id in ids:
        x = escape(s).replace("z"+id, Markup('<a href="/home/'+id+'">'+password_book[id][1]+'</a>'))
        s = x
    return escape(s)

# translate \n to <br>
@app.template_filter('nl2br')
def nl2br_filter(s):
    return escape(s).replace("\\n", Markup('<br>'))

# login check the zid and password
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    global password_book
    global friend_list
    global students_dir
    zid = request.form.get('zid', '')
    zid = re.sub(r'\D', '', zid)
    session['zid'] = zid
    password = request.form.get('password', '')
    print(password)
    if zid in password_book and password == password_book[zid][0]:

        # copy img to static/img 
        students = sorted(os.listdir(students_dir))
        for i in range(len(students)):
            student_to_show = students[i]
            img_directory = os.path.join("static", "img")
            img_filename = os.path.join(students_dir, student_to_show, "img.jpg")
            details_filename = os.path.join(students_dir, student_to_show, "student.txt")
            file = open(details_filename, 'r')
            for line in file:
                a = re.match(r"zid:\sz(\d+)", line)
                if a:
                    id = a.group(1)
            for i in range(len(students)):   
                if not os.path.exists(img_directory):
                    os.makedirs(img_directory)
                dst = os.path.join("static", "img", id+".jpg")
                try:
                    shutil.copyfile(img_filename, dst)
                except FileNotFoundError:
                    pass
                    #app.logger.info(img_filename+"doesn't exist.")

        return redirect(url_for('.home', zid = zid))
    return render_template('login.html')

# home page shows post, comments, replies and friend list
@app.route('/home/<zid>', methods=['GET','POST'])
def home(zid):
    if not 'zid' in session:
        return redirect(url_for('.login'))
    if not zid:
        zid = session['zid']
    global friend_list
    global password_book
    global author_post
    global comment1_post
    global comment2_post
    global students_dir
    # if submit a post
    if request.method == 'POST':
        comment = None
        reply = None
        dic = request.values.to_dict()
        keys = dic.keys()
        print(dic)
        for k in keys:
            if 'comment' in k:
                key = k.replace('comment', '')
                comment = dic[k]
            if 'reply' in k:
                key = k.replace('reply', '')
                reply = dic[k]
        if comment:
            cur_post = author_post[zid][int(key)]
            print(cur_post)
            print(comment1_post[zid, cur_post])
            if comment1_post[zid, cur_post]:
                latest_post = comment1_post[zid, cur_post][-1]
                num = latest_post.split('.')[0].split('-')[1]
                new_post = latest_post.replace(num+'.', str(int(num)+1)+'.') # '8-1.txt'
            else:
                new_post = cur_post.replace('.txt', '')+'-0.txt' # '8-0.txt'
            comment1_post[zid, cur_post].append(new_post)
            filename = os.path.join(students_dir, 'z'+zid, new_post)
            file = open(filename, 'w')
            file.write("from: z"+session['zid']+"\n")
            file.write("message: "+comment+"\n")
            file.write("time: "+datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+")+"\n")
            file.close()
            #app.logger.info(filename+" was written.")

        if reply:
            cur_post = author_post[zid][int(key.split('-')[0])]
            cur_comment = comment1_post[zid, cur_post][int(key.split('-')[1])]
            if comment2_post[zid, cur_comment]:
                latest_post = comment2_post[zid, cur_comment][-1]
                num = latest_post.split('.')[0].split('-')[2]
                new_post = latest_post.replace(num+'.', str(int(num)+1)+'.') # '8-0-1.txt'
            else:
                new_post = cur_comment.replace('.txt', '')+'-0.txt' # '8-0-0.txt'
            comment2_post[zid, cur_comment].append(new_post)
            filename = os.path.join(students_dir, 'z'+zid, new_post)
            file = open(filename, 'w')
            file.write("from: z"+session['zid']+"\n")
            file.write("message: "+reply+"\n")
            file.write("time: "+datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+")+"\n")
            file.close()
            #app.logger.info(filename+" was written.")

        # write new post and savs
        post = request.form.get('post')
        if post:
            latest_post = author_post[zid][0]
            new_post = latest_post.replace(latest_post.split('.')[0], str(int(latest_post.split('.')[0])+1))
            author_post[zid].insert(0, new_post)
            filename = os.path.join(students_dir, 'z'+zid, new_post)
            file = open(filename, 'w')
            file.write("from: z"+zid+"\n")
            file.write("message: "+post+"\n")
            file.write("time: "+datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+")+"\n")
            file.close()
            #app.logger.info(filename+" was written.")
    
    # get 3 level post
    post_lvl1 = defaultdict(list)
    post_lvl2 = defaultdict(list)
    post_lvl3 = defaultdict(list)
    for i in author_post[zid]:
        filename = os.path.join(students_dir, 'z'+zid, i)
        file = open(filename, 'r', encoding='utf-8')
        for line in file:
            message = re.match(r"message:\s(.+)", line)
            time = re.match(r"time:\s(.+)\+", line)
            if message:
                mes = message.group(1)
            if time:
                ti = time.group(1).replace('T', ' ')
        post_lvl1[i] = [mes,ti]
        print(i)
        for j in comment1_post[(zid, i)]:
            filename = os.path.join(students_dir, 'z'+zid, j)
            file = open(filename, 'r', encoding='utf-8')
            for line in file:
                message = re.match(r"message:\s(.+)", line)
                time = re.match(r"time:\s(.+)\+", line)
                frm = re.match(r"from:\sz(\d+)", line)
                if message:
                    mes = message.group(1)
                if time:
                    ti = time.group(1).replace('T', ' ')
                if frm:
                    frm_zid = frm.group(1)
            post_lvl2[i].append([mes, ti, frm_zid, j])
            for k in comment2_post[(zid, j)]:
                filename = os.path.join(students_dir, 'z'+zid, k)
                file = open(filename, 'r', encoding='utf-8')
                for line in file:
                    message = re.match(r"message:\s(.+)", line)
                    time = re.match(r"time:\s(.+)\+", line)
                    frm = re.match(r"from:\sz(\d+)", line)
                    if message:
                        mes = message.group(1)
                    if time:
                        ti = time.group(1).replace('T', ' ')
                    if frm:
                        frm_zid = frm.group(1)
                post_lvl3[j].append([mes, ti, frm_zid])
    print("postlvl2",post_lvl2)
    return render_template('home.html', friend_list = friend_list[zid], password_book = password_book, \
                        zid = zid, post_lvl1 = post_lvl1, post_lvl2 = post_lvl2, post_lvl3 = post_lvl3, time = datetime.datetime.now())

# result page of friends and posts
@app.route('/result', methods=['GET','POST'])
def result():
    global password_book
    global name_to_zid
    global post_list
    if request.args.get('option') == 'Friend':
        zid_list = []
        name = request.args.get('option_content')
        print(name)
        for i in name_to_zid:
            if re.search(name, i, re.IGNORECASE):
                print(i)
                zid_list.append(name_to_zid[i])
        return render_template('result.html', zid_list = zid_list, password_book = password_book)
    elif request.args.get('option') == 'Post':
        p_list = []
        post = request.args.get('option_content')
        print(post)
        for i in post_list:
            if re.search(post, i[0], re.IGNORECASE):
                print(i)
                p_list.append(i)
        print(p_list)
        return render_template('result.html', p_list = p_list, password_book = password_book)

# show profile and can change detail information, upload img
@app.route('/profile/<zid>', methods=['GET','POST'])
def profile(zid):
    global students_dir
    details_filename = os.path.join(students_dir, 'z'+zid, "student.txt")
    old_details_filename = os.path.join(students_dir, 'z'+zid, "old_student.txt")
    if request.form.get('upload', '') == 'Upload' and 'file' in request.files:
        submitted_file = request.files['file']
        if submitted_file:
            filename = secure_filename(zid+".jpg")
            submitted_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("File uploaded: Thanks!", "success")
            return redirect(url_for('.profile', zid = zid))
    elif request.form.get('change', '') == 'Save Changes':
        # change details
        full_name = request.form.get('full_name', '')
        email = request.form.get('email', '')
        home = request.form.get('home', '')
        interests = request.form.get('interests', '')
        print("Im in post !!!!")
        i = 0
        os.rename( details_filename, old_details_filename )
        f = open(details_filename, 'w')
        source = open(old_details_filename, 'r')
        for line in source:
            b = re.match(r"full_name:\s(.+)", line)
            c = re.match(r"email:\s(.+)", line)
            d = re.match(r"home_suburb:\s(.+)", line)
            e = re.match(r"interests:\s(.+)", line)
            if b and full_name:
                f.write(line.replace(line, "full_name: "+full_name+os.linesep))
            elif c and email:
                f.write(line.replace(line, "email: "+email+os.linesep))
            elif d and home:
                f.write(line.replace(line, "home_suburb: "+home+os.linesep))
            elif e and interests:
                i = 1
                f.write(line.replace(line, "interests: "+interests+os.linesep))
            else:
                f.write(line)
        if i == 0:
            f.write( "interests: "+interests+os.linesep)
        f.close()
        source.close()
        return redirect(url_for('.profile', zid = zid))

    interests = ''
    home = ''
    email =''
    file = open(details_filename, 'r')
    for line in file:
        a = re.match(r"zid:\sz(\d+)", line)
        b = re.match(r"full_name:\s(.+)", line)
        c = re.match(r"email:\s(.+)", line)
        d = re.match(r"home_suburb:\s(.+)", line)
        e = re.match(r"interests:\s(.+)", line)
        if a:
            zid = a.group(1)
        if b:
            full_name = b.group(1)
        if c:
            email = c.group(1)
        if d:
            home = d.group(1)
        if e:
            interests = e.group(1)
    profile_list = [zid, full_name, email, home, interests]
    return render_template('profile.html', zid = zid, profile_list = profile_list, time = datetime.datetime.now())

# log out
@app.route('/logout', methods=['GET','POST'])
def logout():
    if 'zid' in session:
        session.clear()
    return redirect(url_for('.login'))

# get all posts 
def getPost(filename):
    mes = None
    ti = None
    frm_zid = None
    file = open(filename, 'r', encoding='utf-8')
    for line in file:
        message = re.match(r"message:\s(.+)", line)
        time = re.match(r"time:\s(.+)\+", line)
        frm = re.match(r"from:\sz(\d+)", line)
        if message:
            mes = message.group(1)
        if time:
            ti = time.group(1).replace('T', ' ')
        if frm:
            frm_zid = frm.group(1)
    if mes and ti and frm_zid:
        return [mes, ti, frm_zid]



password_book = defaultdict()   # get password and full name of every studens
friend_list = defaultdict()     # get friend list
name_to_zid = defaultdict()     # change full name to zid
post_list = []                  # get all posts
author_post = defaultdict(list)     # first level post
comment1_post = defaultdict(list)   # second level comment
comment2_post = defaultdict(list)   # third level reply
students = sorted(os.listdir(students_dir))
for i in range(len(students)):
    friends = None
    student_to_show = students[i]
    directory = os.path.join(students_dir, student_to_show)
    img_directory = os.path.join("static", "img")
    img_filename = os.path.join(students_dir, student_to_show, "img.jpg")
    details_filename = os.path.join(students_dir, student_to_show, "student.txt")

    # choose necessary data from student.txt
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

    # # copy img to static/img        
    # if not os.path.exists(img_directory):
    #     os.makedirs(img_directory)
    # dst = os.path.join("static", "img", zid+".jpg")
    # try:
    #     shutil.copyfile(img_filename, dst)
    # except FileNotFoundError:
    #     app.logger.info(img_filename+"doesn't exist.")

    # get posts and comments
    for file in sorted(os.listdir(directory)):
        post = re.match(r"(\d+)\.txt", file)
        comment_1 = re.match(r"(\d+)-(\d+)\.txt", file)
        comment_2 = re.match(r"(\d+-\d+)-(\d+)\.txt", file)
        if post:
            author_post[zid].append(file)
            post_directory = os.path.join(directory, file)
            post_list.append(getPost(post_directory))
        if comment_1:
            comment1_post[zid, comment_1.group(1)+'.txt'].append(file)
            post_directory = os.path.join(directory, file)
            post_list.append(getPost(post_directory))
        if comment_2:
            comment2_post[zid, comment_2.group(1)+'.txt'].append(file)
            post_directory = os.path.join(directory, file)
            post_list.append(getPost(post_directory))

    # store data in dictionary
    password_book[zid] = [ps, full_name]
    friend_list[zid] = [x.strip() for x in friends.split(',')]
    friend_list[zid] = [re.sub(r'\D', '', x) for x in friend_list[zid]]
    name_to_zid[full_name] = zid
for x in author_post:
    author_post[x].sort(key = lambda x: int(x.split('.')[0]), reverse = True)
for x in comment1_post:
    comment1_post[x].sort(key = lambda x: int(x.split('.')[0].split('-')[1]))
for x in comment2_post:
    comment2_post[x].sort(key = lambda x: int(x.split('.')[0].split('-')[2]))
post_list = [x for x in post_list if x]
print(post_list)




if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True, use_reloader=True)
