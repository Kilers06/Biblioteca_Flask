"""Acceso a KeyDB (redis-py)"""
import json
import redis
from redis.exceptions import WatchError

class LibroDuplicadoError(Exception):
    pass

class LibroNoEncontradoError(Exception):
    pass

INDICE = "libros:ids"
CONTADOR = "libros:contador"


def conexion(config):
    return redis.Redis(
        host=config["KEYDB_HOST"], port=config["KEYDB_PORT"],
        db=config["KEYDB_DB"], username=config["KEYDB_USERNAME"],
        password=config["KEYDB_PASSWORD"], ssl=config["KEYDB_SSL"],
        decode_responses=True, socket_connect_timeout=5, socket_timeout=5,
    )


def clave_libro(id_libro):
    return f"libro:{id_libro}"


def clave_unica(titulo, autor):
    return f"libros:unico:{titulo.strip().casefold()}|{autor.strip().casefold()}"


def listar(db, busqueda=""):
    ids = db.zrange(INDICE, 0, -1)
    if not ids:
        return []
    datos = db.mget([clave_libro(i) for i in ids])
    libros = [json.loads(v) for v in datos if v]
    termino = busqueda.strip().casefold()
    if termino:
        libros = [libro for libro in libros if any(
            termino in str(libro.get(campo, "")).casefold()
            for campo in ("titulo", "autor", "genero")
        )]
    return libros


def obtener(db, id_libro):
    valor = db.get(clave_libro(id_libro))
    return json.loads(valor) if valor else None


def validar(datos):
    libro = {campo: str(datos.get(campo, "")).strip()
             for campo in ("titulo", "autor", "genero", "estado")}
    if not all(libro.values()):
        raise ValueError("Todos los campos son obligatorios.")
    libro["estado"] = libro["estado"].lower().replace("leido", "leído")
    if libro["estado"] not in ("leído", "no leído"):
        raise ValueError("El estado debe ser leído o no leído.")
    return libro


def agregar(db, datos):
    libro = validar(datos)
    unica = clave_unica(libro["titulo"], libro["autor"])
    # SET NX reserva la combinación título/autor antes de guardar el JSON.
    id_libro = db.incr(CONTADOR)
    if not db.set(unica, id_libro, nx=True):
        raise LibroDuplicadoError("Ya existe un libro con el mismo título y autor.")
    libro["id"] = id_libro
    try:
        with db.pipeline(transaction=True) as pipe:
            pipe.set(clave_libro(id_libro), json.dumps(libro, ensure_ascii=False))
            pipe.zadd(INDICE, {str(id_libro): id_libro})
            pipe.execute()
    except Exception:
        db.delete(unica)
        raise
    return id_libro


def actualizar(db, id_libro, datos):
    nuevo = validar(datos)
    llave = clave_libro(id_libro)
    # WATCH evita actualizaciones simultáneas basadas en una versión antigua.
    for _ in range(5):
        with db.pipeline() as pipe:
            try:
                pipe.watch(llave)
                texto = pipe.get(llave)
                if not texto:
                    raise LibroNoEncontradoError("El libro ya no existe.")
                anterior = json.loads(texto)
                vieja = clave_unica(anterior["titulo"], anterior["autor"])
                nueva = clave_unica(nuevo["titulo"], nuevo["autor"])
                if vieja != nueva:
                    pipe.watch(nueva)
                    if pipe.exists(nueva):
                        raise LibroDuplicadoError("Ya existe un libro con ese título y autor.")
                actualizado = {"id": id_libro, **nuevo}
                pipe.multi()
                pipe.set(llave, json.dumps(actualizado, ensure_ascii=False))
                if vieja != nueva:
                    pipe.set(nueva, id_libro)
                    pipe.delete(vieja)
                pipe.execute()
                return
            except WatchError:
                continue
    raise ValueError("El libro cambió al mismo tiempo. Inténtalo nuevamente.")


def eliminar(db, id_libro):
    llave = clave_libro(id_libro)
    for _ in range(5):
        with db.pipeline() as pipe:
            try:
                pipe.watch(llave)
                texto = pipe.get(llave)
                if not texto:
                    raise LibroNoEncontradoError("El libro ya no existe.")
                libro = json.loads(texto)
                pipe.multi()
                pipe.delete(llave)
                pipe.zrem(INDICE, str(id_libro))
                pipe.delete(clave_unica(libro["titulo"], libro["autor"]))
                pipe.execute()
                return
            except WatchError:
                continue
    raise ValueError("El libro cambió al mismo tiempo. Inténtalo nuevamente.")
