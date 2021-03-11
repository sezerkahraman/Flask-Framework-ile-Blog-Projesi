from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.handlers.sha2_crypt import sha256_crypt
from functools import wraps
from flask import g, request, redirect, url_for
## Kullanıcı kayıt formu
class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)])
    username=StringField("Kullanıcı Adı:",validators=[validators.length(min=5,max=35)])
    email=StringField("Email Adresi",validators=[validators.Email(message="Geçerli email giriniz...")])
    password=PasswordField("Parola:",validators=[validators.DataRequired(message="Lütfen bir parola belirleyiniz"),
    validators.EqualTo(fieldname="confirm",message="Parolalar uyuşmuyor")
    ])
    confirm=PasswordField("Parola Doğrula")
class LoginForm(Form):
    username=StringField("Kullanıcı Adı:")
    password=PasswordField("Parola:")

app=Flask(__name__)
app.secret_key="skblog"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="skblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)
#Kullanıcı Girişi Decoratorı
from functools import wraps
from flask import g, request, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
       if "logged_in"in session:
            return f(*args, **kwargs)
       else:
            flash("Bu sayfayı görüntüleyebilmek için önce giriş yapmalısınız")
            return redirect(url_for("login"))
    return decorated_function
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()

    sorgu="Select * From articles where author = %s"
    result=cursor.execute(sorgu,(session["username"],))

    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)

    else:
        return render_template("dashboard.html")
#Kayıt olma
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)

    if request.method =="POST"and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()

        sorgu="INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla kayıt oldunuz","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)

    return render_template("register.html")
#login işlemi
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method =="POST":
        username=form.username.data
        password_entered=form.password.data

        cursor=mysql.connection.cursor()
    
        sorgu="Select * From users where username=%s"

        result=cursor.execute(sorgu,(username,))

        if(result>0):
            data=cursor.fetchone()
            real_password=data["password"]
            
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yaptınız")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            
            
            else:
                flash("Parolanızı Yanlış Girdiniz")
                return redirect(url_for("login"))



        else:
             flash("Hatalı kullanıcı adı girdiniz")
             return redirect(url_for("login"))


    return render_template("login.html",form=form)
#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where id=%s"
    result=cursor.execute(sorgu,(id,))
    if result>0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")




@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Makale Oluştur
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form=articleform(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data

        cursor=mysql.connection.cursor()

        sorgu="Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()

        flash("Makale Başarıyla Eklendi","dangers")
        return redirect(url_for("dashboard"))
    return render_template("addarticles.html",form=form)
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles"
    result=cursor.execute(sorgu)
    if result >0:
        articles=cursor.fetchall()
        return  render_template("articles.html",articles=articles)
    else:
        
         return render_template("articles.html")

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where author=%s and id=%s"

    result=cursor.execute(sorgu,(session["username"],id))

    if result>0:
        sorgu2="Delete  From articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz bulunmamaktadır")
        return redirect(url_for("index"))
#Makale Güncelle
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        
        sorgu="Select * From articles where id=%s and author=%s"

        result=cursor.execute(sorgu,(id,session["username"]))

        if result==0:
            flash("Böyle bir makale yok veya yetkiniz yok","danger")
            return redirect(url_for("index"))

        else:
            article=cursor.fetchone()
            form=articleform()

            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)
    else:
        #POST REQUEST KISMI
        form=articleform(request.form)

        newtitle=form.title.data
        newcontent=form.content.data

        sorgu2="Update articles Set title=%s,content=%s where id=%s"

        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newtitle,newcontent,id))
        mysql.connection.commit()

        flash("Makele başarıyla güncellendi....")
        return redirect(url_for("dashboard"))
#MAKALE FORM
class articleform(Form):
    title=StringField("Başlık",validators=[validators.Length(min=5)])
    content=TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])
#ARAMA URL
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        
        keyword=request.form.get("keyword")

        cursor=mysql.connection.cursor()

        sorgu="Select * from articles where title like '%" + str(keyword)+"%'"
        
        result=cursor.execute(sorgu)

        
        if result==0:
            flash("Aranan kelimeye uygun makale bulunamadı")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)

if __name__ == "__main__":
    app.run(debug=True)
