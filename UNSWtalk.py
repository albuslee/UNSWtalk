#!/web/cs2041/bin/python3.6.3


# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re, shutil, datetime
import logging
from collections import defaultdict
from flask import Flask, render_template, session, request, redirect, url_for, escape
from jinja2 import evalcontextfilter, Markup, escape

students_dir = "dataset-medium";

app = Flask(__name__)

# Show unformatted details for student "n"
# Increment n and store it in the session cookie

# _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
# @app.template_filter('nl2br')
# @evalcontextfilter
# def nl2br(eval_ctx, value):
#     result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\\n', Markup('<br>\n'))
#                           for p in _paragraph_re.split(escape(value)))
#     if eval_ctx.autoescape:
#         result = Markup(result)
#     return result


@app.template_filter('id2nm')
def id2nm_filter(s):
    global password_book
    ids = re.findall(r'z(\d+)', s)
    for id in ids:
        x = escape(s).replace("z"+id, Markup('<a href="/home/'+id+'">'+password_book[id][1]+'</a>'))
        s = x
    return escape(s)


@app.template_filter('nl2br')
def nl2br_filter(s):
    return escape(s).replace("\\n", Markup('<br>'))


@app.route('/', methods=['GET','POST'])
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
        return redirect(url_for('.home', zid = zid))
    return render_template('login.html')


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
            app.logger.info(filename+" was written.")

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
            app.logger.info(filename+" was written.")

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
            app.logger.info(filename+" was written.")
    
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
                        zid = zid, post_lvl1 = post_lvl1, post_lvl2 = post_lvl2, post_lvl3 = post_lvl3)


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


@app.route('/logout', methods=['GET','POST'])
def logout():
    # 判断本次请求的session中是否包含有 'username'属性
    if 'zid' in session:
        session.clear()
    return render_template('login.html')

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


# get password of every studens
password_book = defaultdict()
friend_list = defaultdict()
name_to_zid = defaultdict()
post_list = []
author_post = defaultdict(list)
comment1_post = defaultdict(list)
comment2_post = defaultdict(list)
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

    # copy img to static/img        
    if not os.path.exists(img_directory):
        os.makedirs(img_directory)
    dst = os.path.join("static", "img", zid+".jpg")
    try:
        shutil.copyfile(img_filename, dst)
    except FileNotFoundError:
        app.logger.info(img_filename+"doesn't exist.")

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
