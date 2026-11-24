# Biblioteca web con Flask y KeyDB

Aplicación web en Python que implementa operaciones CRUD sobre libros serializados como JSON en KeyDB, utilizando `redis-py`. Tiene páginas HTML, CSS y mensajes visuales con Flask.

## Requisitos

- Python 3.9 o superior
- Docker Desktop con motor activo

## 1. KeyDB en Docker

Si ya tienes un contenedor llamado `biblioteca_keydb`, usa:

```powershell
docker start biblioteca_keydb
docker exec biblioteca_keydb keydb-cli ping
```

Debe responder `PONG`. Si nunca has creado el contenedor, ejecuta una sola vez:

```powershell
docker run -d --name biblioteca_keydb -p 127.0.0.1:6379:6379 -v biblioteca_keydb_data:/data --restart unless-stopped eqalpha/keydb keydb-server /etc/keydb/keydb.conf --appendonly yes
```

## 2. Instalar dependencias

Desde la terminal de VS Code, dentro de la carpeta de este proyecto:

```powershell
python -m pip install -r requirements.txt
```

## 3. Configuración

Crear un `.env` a partir de la plantilla:

```powershell
Copy-Item .env.example .env
```

Para uso local, `KEYDB_HOST=localhost` y `KEYDB_PORT=6379`. Cambia `FLASK_SECRET_KEY` por una cadena larga, aleatoria y privada. No publiques `.env` en GitHub. Puedes generar una clave desde PowerShell y Python:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

## 4. Ejecutar Flask

```powershell
python app.py
```

Abre en tu navegador **http://127.0.0.1:5000**.

## Rutas

| Ruta | Método | Función |
| --- | --- | --- |
| `/` | GET | Listar y buscar (`?buscar=...`) |
| `/agregar` | GET/POST | Formulario y registro |
| `/editar/<id_libro>` | GET/POST | Formulario y actualización |
| `/eliminar/<id_libro>` | POST | Eliminar un libro |

## Estructuras de KeyDB

Compatible con las claves del anterior proyecto de terminal:

- `libro:<id>`: STRING JSON con los campos `id`, `titulo`, `autor`, `genero`, `estado`.
- `libros:contador`: STRING con el siguiente ID (`INCR`).
- `libros:ids`: ZSET con los IDs.
- `libros:unico:<titulo>|<autor>`: STRING para evitar títulos/autores duplicados.

Ejemplo de libro:

```json
{"id":1,"titulo":"Cien años de soledad","autor":"Gabriel García Márquez","genero":"Novela","estado":"leído"}
```

Para comprobar los datos:

```powershell
docker exec -it biblioteca_keydb keydb-cli
```

Dentro de la consola KeyDB: `SCAN 0`, `GET libro:1`, `ZRANGE libros:ids 0 -1`. Sal con `exit`.

## Organización

- `app.py`: rutas Flask y mensajes con `flash`.
- `keydb_store.py`: operaciones de almacenamiento mediante `redis-py`.
- `config.py`: variables de entorno cargadas desde `.env`.
- `templates/`: vistas HTML Jinja2.
- `static/style.css`: estilos de interfaz.

**Uso:** aplicación local de desarrollo académico. No desplegar públicamente sin añadir autenticación, protección CSRF, manejo robusto de secretos y ajustes de seguridad de producción.
