from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, jsonify,request, send_from_directory
import argparse
import yaml
import sqlite3
import os
import uuid

# Se crea la app

def create_app():
    app = Flask(__name__)
    return app
app = create_app()


# Se lee el archivo config.yaml y se le asigna un identificador al consumidor de la api

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    config['basedatos']['consumidor_almacen_api'] = str(uuid.uuid1())
    print(config)


# Se escriben las modificaciones anteriores con el id añadido

with open('config.yaml', "w") as payload:
    payload.write(yaml.dump(config))


# Se especifican argumentos

parser = argparse.ArgumentParser(description="Parametros para ejecutar la aplicacion")
parser.add_argument("--servidor", metavar="string", default="localhost", required=False, help="Especifica la direccion IP que quieres ejecutar")
parser.add_argument("--puerto", type=int, default=5000, required=False, help="Especifica el puerto del servidor")
parser.add_argument("--config", metavar="string", required=True, help="Requiere un archivo de configuracion .yaml") 
args = parser.parse_args()


# Se crea la base de datos si no existe

db_filename = config['basedatos']['path']
db_is_new = not os.path.exists(db_filename)
con = sqlite3.connect(db_filename, check_same_thread=False)

if db_is_new:
    print('La base de datos se ha creado')
else:
    print('La base de datos ya existe')
 
# Se crea la función que valida si la api key es correcta 

def solicitar_permisos(key):
    with open('config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        key_config = config['basedatos']['consumidor_almacen_api']
    print(config)
    if key != key_config:
        validacion = False
    else: 
        validacion = True
    return validacion
    

# Se define la variable 'consumidor' para asignar un nombre al consumidor del almacen

consumidor = config['basedatos']['consumidor_almacen']


# Se crea la ruta y la funcion para crear la tabla en la base de datos  

@app.route('/api/almacen/tabla', methods=['POST'])
def crear_tabla():
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
     try:   
        cur= con.cursor()
        cur.execute('''CREATE TABLE if not exists producto(
        id integer primary key autoincrement,
        name text,
        description text,
        precio real,
        unidades integer,
        stock blob
        )''')
        con.commit()
        return "Tabla creada"
     except:
      print("Tabla no creada")
      return False
    else:
        error='No autorizado'
        return jsonify(error)  


# Se crea la ruta y la funcion para eliminar la tabla de la base de datos

@app.route('/api/almacen/tabla', methods=['DELETE'])
def eliminar_tabla():
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        cur.execute("DROP TABLE producto")
        return "Tabla eliminada"
    else:
        error = 'No autorizado'
        return jsonify(error)


# Se crea el producto en la tabla

@app.route('/api/almacen/producto', methods=['POST'])
def crear_producto():
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur=con.cursor()
        name = request.form['name'] 
        descripcion = request.form['descripcion'] 
        precio = request.form['precio'] 
        unidades = request.form['unidades'] 

        statement=("INSERT INTO producto VALUES (null,?, ?, ?, ?,'true')")
        cur.execute(statement,[name, descripcion,precio,unidades])
        con.commit()
        return "Producto creado"
    else:
        error='No autorizado'
        return jsonify(error)   
 

# Se crea la ruta para incrementar en uno las unidades del producto

@app.route('/api/almacen/incrementar-producto', methods=['PUT'])
def incrementar_producto():
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        cur.execute("UPDATE producto SET unidades = unidades + 1")
        con.commit()
        sentencia = "SELECT * FROM producto;"
        cur.execute(sentencia)
        titulo = "El producto se ha incrementado en una unidad"
        stock = cur.fetchall()
        return jsonify(titulo, stock)
    else:
        error='No autorizado'
        return jsonify(error)   

# Se crea la ruta y la funcion para decrementar tantas unidades como queramos

@app.route('/api/almacen/decrementar-producto/<id>', methods=['PUT'])
def decrementar_producto_uds(id):
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) ==True:
        cur = con.cursor()
        id = id
        uds = request.form['unidades'] 
        cur.execute("UPDATE producto_tienda SET unidades = unidades -"+uds+" where id="+id)
        con.commit()
        sentencia = "SELECT * FROM producto_tienda;"
        cur.execute(sentencia)
        titulo = "El producto se ha decrementado en"+" " +uds+ " "+"unidades"
        stock = cur.fetchall()
        return jsonify(titulo, stock)
    else:
        error = 'No autorizado'
        return jsonify(error)
    
# Se crea la ruta y la funcion para incrementar tantas unidades como queramos

@app.route('/api/almacen/incrementar-producto/<id>', methods=['PUT'])
def incrementar_producto_uds(id):
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        id = id
        uds = request.form['unidades'] 
        cur.execute("UPDATE producto SET unidades = unidades +"+uds)
        con.commit()
        sentencia = "SELECT * FROM producto;"
        cur.execute(sentencia)
        titulo = "El producto se ha incrementado en"+" " +uds+ " "+"unidades"
        stock = cur.fetchall()
        return jsonify(titulo, stock)
    else:
        error = 'No autorizado'
        return jsonify(error)

# Se crea la ruta y la funcion para decrementar las unidades del producto en uno

@app.route('/api/almacen/decrementar-producto', methods=['PUT'])
def decrementar_producto():
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        cur.execute("UPDATE producto SET unidades = unidades - 1")
        con.commit()
        sentencia = "SELECT * FROM producto;"
        cur.execute(sentencia)
        titulo = "El producto se ha decrementado en una unidad"
        stock = cur.fetchall()
        return jsonify(titulo, stock)
    else:
        error = 'No autorizado'
        return jsonify(error)  


# Se crea la ruta y la funcion para eliminar el producto de la tabla en caso de que haya uno
    
@app.route('/api/almacen/producto', methods=['DELETE'])
def eliminar_producto():
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        cur.execute("DELETE FROM producto")
        con.commit
        return "Producto eliminado"
    else:
        error = 'No autorizado'
        return jsonify(error)  


# Se crea la ruta y la funcion para eliminar un producto de la tabla en caso de que haya varios
    
@app.route('/api/almacen/producto/<id>', methods=['DELETE'])
def eliminar_producto_id(id):
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        cur.execute("DELETE FROM producto where id="+id)
        con.commit
        return "Producto eliminado"
    else:
        error = 'No autorizado'
        return jsonify(error)

# Se crea la ruta y la funcion para saber el stock del producto en caso de que haya uno

@app.route('/api/almacen/producto', methods=['GET'])
def leer_producto():
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        sentencia = "SELECT * FROM producto;"
        cur.execute(sentencia)
        stock = cur.fetchall()
        return jsonify(stock)
    else:
        error = 'No autorizado'
        return jsonify(error)  
    

# Se crea la ruta y la funcion para saber el stock del producto en caso de que haya varios

@app.route('/api/almacen/producto/<id>', methods=['GET'])
def leer_producto_id(id):
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        sentencia = "SELECT * FROM producto where id="+id
        cur.execute(sentencia)
        stock = cur.fetchall()
        return jsonify(stock)
    else:
        error = 'No autorizado'
        return jsonify(error)                     

# Se crea la ruta y la funcion para leer un id determinado de un producto

@app.route('/api/almacen/producto/<id>', methods=['GET'])
def leer_producto_determinado(id):
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur = con.cursor()
        sentencia = "SELECT * FROM producto where id="+id
        cur.execute(sentencia)
        stock = cur.fetchone()
        return jsonify(stock)
    else:
        error = 'No autorizado'
        return jsonify(error) 


# Se crea la ruta y la funcion para acceder a la documentacion de la API

@app.route('/services/spec')
def get_spec():
    return send_from_directory(app.root_path, "api_doc.yaml")

SWAGGER_URL = '/api/docs'
API_URL = '/services/spec' 

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)

app.register_blueprint(swaggerui_blueprint)


# Se ejecuta la aplicacion

if __name__ == '__main__':
    app.run()
