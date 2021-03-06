from flask import Flask, jsonify,request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import argparse
from pandas import json_normalize
from pyparsing import empty
import yaml
import sqlite3
import os
import uuid
import requests

# Se crea la app

def create_app():
    app = Flask(__name__)
    return app
app = create_app()

# Se lee el archivo config.yaml y se le asigna un identificador al consumidor de la api

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    config['basedatos']['consumidor_almacen_api']=str(uuid.uuid1())
    print(config)

# Se especifican argumentos

parser = argparse.ArgumentParser(description="Parametros para ejecutar la aplicacion")
parser.add_argument("--servidor", metavar="string", default="localhost", required=False, help="Especifica la direccion IP que quieres ejecutar")
parser.add_argument("--puerto", type=int, default=5000, required=False, help="Especifica el puerto del servidor")
parser.add_argument("--config", metavar="string", required=True, help="Requiere un archivo de configuracion .yaml") 
parser.add_argument("--key", metavar="string", required=True, help="Requiere la api-key de autentificación") 
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
     key_config=config['basedatos']['consumidor_almacen_api']
    print(config)
    if key!= key_config:
        validacion=False
    else: 
        validacion=True
    return validacion
    
# Se crea la variable para llamar al consumidor de la API

consumidor = config['basedatos']['consumidor_almacen']
    
# Se crea la tabla de la base de datos  

@app.route('/api/tienda/tabla', methods=['POST'])
def crear_tabla():
    key = request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
     try:   
        cur= con.cursor()
        cur.execute('''CREATE TABLE if not exists producto_tienda(
        id integer primary key autoincrement,
        name text,
        description text,
        precio real,
        unidades integer,
        stock blob,
        ventas integer
        )''')
        con.commit()
        return "Tabla creada"
     except:
      print("Tabla no creada")
      return False
    else:
        error='No autorizado'
        return jsonify(error) 

# Se crea el producto en la tabla

@app.route('/api/tienda/producto', methods=['POST'])
def crear_producto():
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) == True:
        cur=con.cursor()
        name = request.form['name'] 
        descripcion = request.form['descripcion'] 
        precio = request.form['precio'] 
        unidades = request.form['unidades'] 

        statement=("INSERT INTO producto_tienda VALUES (null,?, ?, ?, ?,'true','0')")
        cur.execute(statement,[name, descripcion,precio,unidades])
        con.commit()
        return "Producto creado"
    else:
        error='No autorizado'
        return jsonify(error)    

# Se crea la ruta para solicitar las unidades del producto al almacen

@app.route('/api/tienda/solicitar_almacen/<id>', methods=['PUT'])
def incrementar_producto(id):
     id=id
     uds = request.form['unidades'] 
     headers = {consumidor: args.key}
     url = 'http://localhost:5000/api/almacen/producto/'+id
     r = requests.get(url,headers=headers)
     response = (r.json())
     if response=='No autorizado':
       return jsonify('API key inválida')
     else:
        unidades=(response[4])
        if int(unidades)>=int(uds):
          data={'unidades':uds}
          url1 = 'http://localhost:5000/api/almacen/decrementar-producto/'+id
          r1 = requests.put(url1,headers=headers,data=data)
         
          url2 = 'http://localhost:5000/api/tienda/incrementar-producto/'+id
          r2 = requests.put(url2,headers=headers,data=data)

          return jsonify('Se han solicitado' + ' ' + uds + ' ' +'unidades')

 
        else:
           return jsonify('No hay tantas unidades en el almacén')

      

# Se crea la ruta para decrementar una unidad del producto

@app.route('/api/tienda/decrementar-producto', methods=['PUT'])
def decrementar_producto():
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     cur.execute("UPDATE producto_tienda SET unidades = unidades - 1")
     con.commit()
     sentencia = "SELECT * FROM producto_tienda;"
     cur.execute(sentencia)
     titulo = "Los productos se han decrementado en una unidad"
     stock = cur.fetchall()
     return jsonify(titulo, stock)
    else:
        error='No autorizado'
        return jsonify(error)  

@app.route('/api/tienda/decrementar-producto/<id>', methods=['PUT'])
def decrementar_producto_uds(id):
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     uds = request.form['unidades']
     cur.execute("UPDATE producto_tienda SET unidades = unidades -"+uds+" where id="+id)
     con.commit()
     sentencia = "SELECT * FROM producto_tienda;"
     cur.execute(sentencia)
     titulo = "El producto se ha decrementado en"+" " +uds+ " "+"unidades"
     stock = cur.fetchall()
     return jsonify(titulo, stock)
    else:
        error='No autorizado'
        return jsonify(error)


@app.route('/api/tienda/incrementar-producto/<id>', methods=['PUT'])
def incrementar_producto_uds(id):
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     uds = request.form['unidades']
     cur.execute("UPDATE producto_tienda SET unidades = unidades +"+uds+" where id="+id)
     con.commit()
     sentencia = "SELECT * FROM producto_tienda;"
     cur.execute(sentencia)
     titulo = "El producto se ha incrementado en"+" " +uds+ " "+"unidades"
     stock = cur.fetchall()
     return jsonify(titulo, stock)
    else:
        error='No autorizado'
        return jsonify(error)

    
#ruta para modificar el precio de un producto    

@app.route('/api/tienda/precio_producto/<id>', methods=['PUT'])
def cambiar_precio(id):
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     precio = request.form['precio']
     cur.execute("UPDATE producto_tienda SET precio ="+precio+" where id="+id )
     con.commit()
     sentencia = "SELECT * FROM producto_tienda;"
     cur.execute(sentencia)
     titulo = "El precio se ha cambiado a"+" " +precio
     stock = cur.fetchall()
     return jsonify(titulo, stock)
    else:
        error='No autorizado'
        return jsonify(error)


#ruta para venta


@app.route('/api/tienda/venta_producto/<id>', methods=['PUT'])
def venta_producto(id):
    id=id
    headers = {consumidor: args.key,'Content-type': 'application/json', 'charset': 'utf-8'}
    url = 'http://localhost:5000/api/tienda/leer-producto/'+id
    r = requests.get(url,headers=headers)
    response = (r.json())
    uds = request.form['unidades']
    if response=='No autorizado':
       return jsonify('API key inválida')
    else:
        unidades=(response[4])
        if int(unidades)>=int(uds):
#verificamos que tiene precio:


            precio= (response[3])
            if precio != empty:
              url2 = 'http://localhost:5000/api/tienda/decrementar-producto/'+id+"/"+uds
              r2 = requests.put(url2,headers=headers)
              cur=con.cursor()
              precio=precio
              cur.execute("UPDATE producto_tienda SET ventas = ventas + 1 where id="+id)
              con.commit()

              return jsonify('venta realizada con éxito')
        else:
               error='No hay unidades en la tienda suficientes'
               return jsonify(error)
           
# Se crea la ruta para eliminar el producto
    
@app.route('/api/tienda/eliminar-producto/<id>', methods=['DELETE'])
def eliminar_producto(id):
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     cur.execute("DELETE FROM producto_tienda where id="+id)
     con.commit
     return "Producto eliminado"
    else:
        error='No autorizado'
        return jsonify(error)  

# Se crea la ruta para saber la información de un producto
 

@app.route('/api/tienda/leer-producto/<id>', methods=['GET'])
def leer_producto_determinado(id):
    key=request.headers.get(consumidor)
    if solicitar_permisos(key) ==True:
      cur = con.cursor()
      sentencia = "SELECT*FROM producto_tienda where id="+id
      cur.execute(sentencia)
      stock = cur.fetchone()
    
      return jsonify(stock)
    else:
        error='No autorizado'
        return jsonify(error)  


# Se crea la ruta y la funcion para acceder a la documentacion de la API

@app.route('/services/spec')
def get_spec():
    return send_from_directory(app.root_path, "api_doc_tienda.yaml")

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
    app.run(host=args.servidor,port=args.puerto)
