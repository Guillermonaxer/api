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

# Se escriben las modificaciones anteriores con el id añadido



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
    

    
# Se crea la tabla de la base de datos  

@app.route('/api/tienda/crear-tabla', methods=['POST'])
def crear_tabla():
    key=request.headers.get('key')
    if solicitar_permisos(key) ==True:
     cur= con.cursor()
     cur.execute('''CREATE TABLE if not exists producto_tienda('name','id','description','precio','unidades','stock','ventas')''')
     con.commit()
     return "Tabla creada"
    else:
        error='No autorizado'
        return jsonify(error)  

# Se crea el producto en la tabla

@app.route('/api/tienda/crear-producto', methods=['POST'])
def crear_producto():
    key=request.headers.get('key')
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     cur.execute("INSERT INTO producto_tienda VALUES ('Barra de pan', 3, 'Barra de pan prueba', '1.50€', 3, True, 0)")
     con.commit()
     return "Producto creado"
    else:
        error='No autorizado'
        return jsonify(error)   

# Se crea la ruta para solicitar las unidades del producto al almacen

@app.route('/api/tienda/solicitar_almacen/<id>/<uds>', methods=['GET'])
def incrementar_producto(id,uds):
     id=id
     uds=uds
     headers = {'key':args.key,'Content-type': 'application/json', 'charset': 'utf-8'}
     url = 'http://localhost:5000/api/almacen/leer-producto/'+id
     r = requests.get(url,headers=headers)
     response = (r.json())
     if response=='No autorizado':
       return jsonify('API key inválida')
     else:
        unidades=(response[4])
        if int(unidades)>=int(uds):
    
          url1 = 'http://localhost:5000/api/almacen/decrementar-producto/'+id+"/"+uds
          r1 = requests.put(url1,headers=headers)
         
          url2 = 'http://localhost:5000/api/tienda/decrementar-producto/'+id+"/"+uds
          r2 = requests.put(url2,headers=headers)

          return jsonify(int(uds))

 
        else:
           return jsonify('No hay tantas unidades en el almacén')

      

# Se crea la ruta para decrementar las unidades del producto

@app.route('/api/tienda/decrementar-producto', methods=['PUT'])
def decrementar_producto():
    key=request.headers.get('key')
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     cur.execute("UPDATE producto_tienda SET unidades = unidades - 1")
     con.commit()
     sentencia = "SELECT * FROM producto_tienda;"
     cur.execute(sentencia)
     titulo = "El producto se ha decrementado en una unidad"
     stock = cur.fetchall()
     return jsonify(titulo, stock)
    else:
        error='No autorizado'
        return jsonify(error)  

@app.route('/api/tienda/decrementar-producto/<id>/<uds>', methods=['PUT'])
def decrementar_producto_uds(id,uds):
    key=request.headers.get('key')
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     uds=uds
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


@app.route('/api/tienda/incrementar-producto/<uds>', methods=['PUT'])
def incrementar_producto_uds(uds):
    key=request.headers.get('key')
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     uds=uds
     cur.execute("UPDATE producto_tienda SET unidades = unidades +"+uds)
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

@app.route('/api/tienda/precio_producto/<id>/<precio>', methods=['PUT'])
def cambiar_precio(id,precio):
    key=request.headers.get('key')
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     precio=precio
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


@app.route('/api/tienda/venta_producto/<id>/<uds>', methods=['PUT'])
def venta_producto(id,uds):
    id=id
    headers = {'key':args.key,'Content-type': 'application/json', 'charset': 'utf-8'}
    url = 'http://localhost:5000/api/tienda/leer-producto/'+id
    r = requests.get(url,headers=headers)
    response = (r.json())
    uds=uds
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
              cur.execute("UPDATE producto_tienda SET ventas = ventas + 1")
              con.commit()

              return jsonify('venta realizada con éxito')
        else:
               error='No hay unidades en la tienda suficientes'
               return jsonify(error)
# Se crea la ruta para eliminar el producto
    
@app.route('/api/tienda/eliminar-producto', methods=['DELETE'])
def eliminar_producto():
    key=request.headers.get('key')
    if solicitar_permisos(key) ==True:
     cur=con.cursor()
     cur.execute("DROP TABLE producto_tienda")
     con.commit
     return "Producto eliminado"
    else:
        error='No autorizado'
        return jsonify(error)  

# Se crea la ruta para saber el stock del producto

@app.route('/api/tienda/leer-producto', methods=['GET'])
def leer_producto():
    key=request.headers.get('key')
    if solicitar_permisos(key) ==True:
      cur = con.cursor()
      sentencia = "SELECT * FROM producto_tienda;"
      cur.execute(sentencia)
      stock = cur.fetchall()
    
      return jsonify(stock)
    else:
        error='No autorizado'
        return jsonify(error)  

@app.route('/api/tienda/leer-producto/<id>', methods=['GET'])
def leer_producto_determinado(id):
    key=request.headers.get('key')
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
    app.run()
