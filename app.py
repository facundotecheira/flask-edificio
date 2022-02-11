from flask import Flask,render_template,request,url_for,redirect,flash,session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os
import bcrypt


app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask-edificio'
app.config['Images_folder'] = './static/img'

mysql = MySQL(app)

app.secret_key = 'mysecretkey'

semilla = bcrypt.gensalt()

# Ruta index del proyecto


@app.route('/')
def index():
    if 'admin' in session:
        return redirect('/admin')

    if 'nombre' in session:
        b_dep = session['b_departamento']
        b_em = session['b_emsa']
        b_sam = session['b_samsa']
        fech = session['fecha']
        num = session['numeros']
        nombreI = session['nombre']

        return render_template('lista_boletas.html',b_departamento = b_dep,b_emsa=b_em,b_samsa=b_sam,fecha=fech,numero=num,nombre=nombreI)
    else:
        return render_template('index.html')

# Ruta de acceso

@app.route('/admin')
def admin():
    if 'admin' in session:
        return render_template ('admin.html')
    else:
        return redirect('/')

# Ruta de acceso de los usuarios

@app.route('/login_user',methods=['POST'])
def login_user():
    if request.method == 'POST':
        dniLogin = request.form['dnilogin']
        passwordLogin = request.form['passlogin']
        password_encode = passwordLogin.encode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute('SELECT nombre,password,id,departamento FROM users WHERE dni = %s',[dniLogin])
        usuario = cur.fetchone()

        if dniLogin == "1234" and passwordLogin == "silencer":
            session['admin'] ='1234'
            return redirect('/admin')

        if usuario is None:
            flash('El inquilino no esta registrado')
            return redirect('/')  
    
        
        if usuario != '':
            password_encriptado_encode = usuario[1].encode('utf-8')
            if bcrypt.checkpw(password_encode,password_encriptado_encode):
                
                session['nombre'] = usuario[0]
                nombreI = session['nombre']
                
                cur = mysql.connection.cursor()
                cur.execute('SELECT boleta_departamento,boleta_emsa,boleta_samsa,fecha,num_departamento FROM boletas where num_departamento= %s',[usuario[3]] )
                boletas = cur.fetchone()

                if boletas:
                    session['b_departamento'] = boletas[0]
                    session['b_emsa'] = boletas[1]
                    session['b_samsa'] = boletas[2]
                    session['fecha'] = boletas[3]
                    session['numeros'] = boletas[4]

                    

                    
                    return render_template('lista_boletas.html',b_departamento=boletas[0],b_emsa=boletas[1],b_samsa=boletas[2],fecha=boletas[3],numero=boletas[4],nombre=nombreI)
                else:
                    return ''
            else:
                flash('Error contraseña incorrecta')
                return redirect('/')

       
# Ruta para agregar inquilinos

@app.route('/add_inquilinos',methods=['POST'])
def add_inquilinos():
    if request.method == 'POST':
        dni_inquilino = request.form['dni_inquilino']
        nombre_inquilino = request.form['nombre_inquilino']
        departamento = request.form['departamento']
        password_inquilino = request.form['password_inquilino']
        password_encode = password_inquilino.encode('utf-8')
        password_encriptado = bcrypt.hashpw(password_encode,semilla)
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE dni = %s ',[dni_inquilino])
        usuario = cur.fetchone()
        if usuario:
            flash('Ese inquilino ya existe')
            return redirect ('/cargar_nuevos_inquilinos') 
        else:
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO users (dni,nombre,departamento,password) VALUES (%s,%s,%s,%s)',
            (dni_inquilino,nombre_inquilino,departamento,password_encriptado))
            mysql.connection.commit()
            flash('Nuevo usuario registrado correctamente')
            return redirect('/cargar_nuevos_inquilinos')

# Ruta que muestra la pestaña de agregar usuarios

@app.route('/cargar_nuevos_inquilinos')
def cargar_inquilino():
    if 'admin' in session:
        return render_template('/cargar_nuevos_inquilinos.html')
    else:
        return redirect ('/')

# Ruta que muestra la lista de inquilinos registrados

@app.route('/ver_inquilinos')
def ver_inquilinos():
    if 'admin' in session:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users')
        data = cur.fetchall()
        if data == ():
            flash('Actualmente no tiene inquilinos registrados')
            return render_template('lista_inquilinos.html')
        else:
            return render_template ('lista_inquilinos.html',contacts=data)
    else:
        return redirect('/')


# Ruta que muestra la pestaña para cargar usuarios

@app.route('/cargar_boletas')
def cargar_boletas():
    if 'admin' in session:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users')
        data = cur.fetchall()
        if data == ():
            flash('No hay inquilinos registrados')
            return redirect('/cargar_nuevos_inquilinos')
        else:
            return render_template('cargar_boletas.html')
    else:
        return redirect('/')

# Ruta para cerrar sesion en la plataforma

@app.route('/salir')
def salir():
    session.clear()
    return redirect('/')

# Ruta para agregar nuevas boletas

@app.route('/add_boletas',methods = ['POST'])
def add_boletas():
    if request.method == 'POST':
        boleta_departamento = request.files['boleta_departamento'] 
        filename = secure_filename(boleta_departamento.filename)
        hola = filename

        boleta_emsa = request.files['boleta_emsa']
        filename = secure_filename(boleta_emsa.filename)
        hola2 = filename

        boleta_samsa = request.files['boleta_samsa']
        filename = secure_filename(boleta_samsa.filename)
        hola3 = filename
        
        departamento = request.form['departamento']

            

        if hola =='' and hola2=='' and hola3=='' or departamento== 'Departamento...':
            flash('Debes cargar almenos una boleta y seleccionar un departamento')
            redirect ('/cargar_boletas')
        else:

            cur = mysql.connection.cursor()
            cur.execute('SELECT boleta_departamento,boleta_emsa,boleta_samsa FROM boletas WHERE num_departamento = %s',[departamento])
            data = cur.fetchall()
            
            if data != ():
                if data [0][0] != '':
                    borrar_depto = data[0][0]
                    try:
                        os.remove(os.path.join(app.config['Images_folder'],borrar_depto))
                    except:
                        print('No existe el archivo')
            
                if data [0][1] != '':
                    borrar_emsa = data[0][1]
                    try:
                        os.remove(os.path.join(app.config['Images_folder'],borrar_emsa))
                    except:
                        print('No existe el archivo')
                    
                if data [0][2] != '':
                    borrar_samsa = data[0][2]
                    try:
                        os.remove(os.path.join(app.config['Images_folder'],borrar_samsa))
                    except:
                        print('No existe el archivo')

                cur = mysql.connection.cursor()
                cur.execute('UPDATE boletas SET boleta_departamento = %s, boleta_emsa= %s, boleta_samsa= %s  WHERE num_departamento = %s' ,(hola,hola2,hola3,departamento))
                mysql.connection.commit()
                
                if hola:
                    boleta_departamento.save(os.path.join(app.config['Images_folder'],hola))
            
                if hola2:
                    boleta_emsa.save(os.path.join(app.config['Images_folder'],hola2))
            
                if hola3:
                    boleta_samsa.save(os.path.join(app.config['Images_folder'],hola3))         
            else:
                cur = mysql.connection.cursor()
                cur.execute('INSERT INTO boletas (boleta_departamento,boleta_emsa,boleta_samsa,num_departamento) VALUES (%s,%s,%s,%s)',
                (hola,hola2,hola3,departamento))
                mysql.connection.commit()
                
                if hola:
                    boleta_departamento.save(os.path.join(app.config['Images_folder'],hola))
            
                if hola2:
                    boleta_emsa.save(os.path.join(app.config['Images_folder'],hola2))
            
                if hola3:
                    boleta_samsa.save(os.path.join(app.config['Images_folder'],hola3))
            
            flash('Boletas cargadas correctamente')
            return redirect('/cargar_boletas')
    return redirect ('/cargar_boletas')
   

# Ruta para eliminar inquilinos

@app.route('/delete/<id>/<depto>')
def delete_inquilino(id,depto):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM users WHERE id = %s',[id])
    mysql.connection.commit()

    # cur = mysql.connection.cursor()
    # cur.execute('DELETE FROM boletas WHERE num_departamento = %s',[depto])
    # mysql.connection.commit()
    
    flash('Inquilino eliminado exitosamente')
    return redirect('/ver_inquilinos')

# Ruta para eitar la informacion de los inquilinos 

@app.route('/edit_inquilinos/<id>',methods=['POST'])
def editar_inquilino(id):
    if request.method == 'POST':
        dni_inquilino = request.form['dni_inquilino']
        nombre_inquilino = request.form['nombre_inquilino']
        departamento = request.form['departamento']
        cur = mysql.connection.cursor()
        cur.execute('UPDATE users SET dni = %s, nombre= %s,departamento = %s  WHERE id = %s' ,(dni_inquilino,nombre_inquilino,departamento,id))
        mysql.connection.commit()
        flash('Datos actualizados correctamente')
        return redirect ('/ver_inquilinos')

# Ruta que muestra la pestaña para editar inquilinos

@app.route('/editar/<id>/')
def editar(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM users WHERE id = %s',[id])
    data = cur.fetchone()
    return render_template ('edit.html',contact = data)
    

# Secuencia que inicia el servidor
  
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3000,debug=True)

