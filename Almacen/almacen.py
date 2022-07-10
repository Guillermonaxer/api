import os
import sqlite3
import yaml
import argparse
import http.server
import socketserver

# Se pasan argumentos

parser = argparse.ArgumentParser(description="Run a simple HTTP server")
parser.add_argument("--servidor", metavar="string", default="localhost", required=False, help="Especifica la direccion IP que quieres ejecutar")
parser.add_argument("--puerto", metavar=int, default=5000, required=False, help="Especifica el puerto del servidor")
parser.add_argument("--config", metavar="string", required=True, help="Requiere un archivo de configuracion")
parser.add_argument("--insertar", metavar="string", required=False, help="Inserta datos en la tabla")
parser.add_argument("--incrementar", metavar="string", required=False, help="Incrementa en uno el producto")
parser.add_argument("--decrementar", metavar="string", required=False, help="Decrementa en uno el producto")
parser.add_argument("--delete", metavar="string", required=False, help="Elimina la tabla")
args = parser.parse_args()

# Se abre archivo config.yaml

with open('config.yaml', 'r') as f:
  config = yaml.load(f, Loader=yaml.FullLoader)

# Se crea la base de datos

db_filename = config['basedatos']['path']

db_is_new = not os.path.exists(db_filename)

con = sqlite3.connect(db_filename)

if db_is_new:
    print('La base de datos se ha creado')
else:
    print('La base de datos ya existe')

# Se crea la tabla

cur= con.cursor()
cur.execute('''CREATE TABLE if not exists producto('name','id','description','precio','unidades','stock')''')
con.commit()

# Se crea el producto

cur= con.cursor()
if args.insertar is not None:
    cur.execute("INSERT INTO producto VALUES ('Barra de pan', 1, 'Barra de pan artesana', '1.50€', 3, True)")
    con.commit()

# Incrementa el producto

cur= con.cursor()
if args.incrementar is not None:
    cur.execute("UPDATE producto SET unidades = unidades + 1")
    con.commit()

# Decrementa el producto

cur= con.cursor()
if args.decrementar is not None:
    cur.execute("UPDATE producto SET unidades = unidades - 1")
    con.commit()
    
# Elimina la tabla

cur= con.cursor()
if args.delete is not None:
    cur.execute("DROP TABLE producto")
    con.commit

# Lee la tabla

cur = con.cursor()
sentencia = "SELECT * FROM producto;"
cur.execute(sentencia)
stock = cur.fetchall()
print(stock)

con.close()

# Se ejecuta el servidor

IP = config['hosts']['IP']
PUERTO = config['hosts']['puerto']

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer((IP, PUERTO), Handler) as httpd:
    print("Aplicacion ejecutada")
    httpd.serve_forever()
