from flask import Flask, jsonify
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
    config['basedatos']['consumidor_almacen_api']=str(uuid.uuid1())
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

# Se crea la tabla de la base de datos

@app.route('/almacen/crear-tabla', methods=['POST'])
def crear_tabla():
    cur= con.cursor()
    cur.execute('''CREATE TABLE if not exists producto('name','id','description','precio','unidades','stock')''')
    con.commit()
    return "Tabla creada"

# Se crea el producto en la tabla

@app.route('/almacen/crear-producto', methods=['POST'])
def crear_producto():
    cur=con.cursor()
    cur.execute("INSERT INTO producto VALUES ('Barra de pan', 1, 'Barra de pan artesana', '1.50€', 3, True)")
    con.commit()
    return "Producto creado"

# Se crea la ruta para incrementar las unidades del producto

@app.route('/almacen/incrementar-producto', methods=['PUT'])
def incrementar_producto():
    cur=con.cursor()
    cur.execute("UPDATE producto SET unidades = unidades + 1")
    con.commit()
    sentencia = "SELECT * FROM producto;"
    cur.execute(sentencia)
    titulo = "El producto se ha incrementado en una unidad"
    stock = cur.fetchall()
    return jsonify(titulo, stock)

# Se crea la ruta para decrementar las unidades del producto

@app.route('/almacen/decrementar-producto', methods=['PUT'])
def decrementar_producto():
    cur=con.cursor()
    cur.execute("UPDATE producto SET unidades = unidades - 1")
    con.commit()
    sentencia = "SELECT * FROM producto;"
    cur.execute(sentencia)
    titulo = "El producto se ha decrementado en una unidad"
    stock = cur.fetchall()
    return jsonify(titulo, stock)

# Se crea la ruta para eliminar el producto
    
@app.route('/almacen/eliminar-producto', methods=['DELETE'])
def eliminar_producto():
    cur=con.cursor()
    cur.execute("DROP TABLE producto")
    con.commit
    return "Producto eliminado"

# Se crea la ruta para saber el stock del producto

@app.route('/almacen/leer-producto', methods=['GET'])
def leer_producto():
    cur = con.cursor()
    sentencia = "SELECT * FROM producto;"
    cur.execute(sentencia)
    stock = cur.fetchall()
    return jsonify(stock)
    
# Se ejecuta la aplicacion

if __name__ == '__main__':
    app.run()