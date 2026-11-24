"""Aplicación web de biblioteca con Flask y KeyDB."""
from flask import Flask, flash, redirect, render_template, request, url_for
from redis.exceptions import RedisError

from config import Config
from keydb_store import (
    LibroDuplicadoError, LibroNoEncontradoError, agregar, actualizar,
    conexion, eliminar, listar, obtener,
)

app = Flask(__name__)
app.config.from_object(Config)
db = conexion(app.config)


@app.route("/")
def inicio():
    buscar = request.args.get("buscar", "").strip()
    try:
        libros = listar(db, buscar)
    except (RedisError, ValueError) as error:
        flash(f"No se pudo consultar KeyDB: {error}", "danger")
        libros = []
    return render_template("index.html", libros=libros, buscar=buscar)


@app.route("/agregar", methods=["GET", "POST"])
def crear_libro():
    if request.method == "POST":
        try:
            agregar(db, request.form)
            flash("Libro agregado correctamente.", "success")
            return redirect(url_for("inicio"))
        except (ValueError, LibroDuplicadoError) as error:
            flash(str(error), "danger")
        except RedisError:
            flash("Error de conexión con KeyDB.", "danger")
    return render_template("formulario.html", titulo_pagina="Agregar libro", libro=request.form if request.method == "POST" else {}, accion="crear_libro")


@app.route("/editar/<int:id_libro>", methods=["GET", "POST"])
def editar_libro(id_libro):
    try:
        libro = obtener(db, id_libro)
        if libro is None:
            flash("No se encontró el libro solicitado.", "warning")
            return redirect(url_for("inicio"))
        if request.method == "POST":
            try:
                actualizar(db, id_libro, request.form)
                flash("Libro actualizado correctamente.", "success")
                return redirect(url_for("inicio"))
            except (ValueError, LibroDuplicadoError, LibroNoEncontradoError) as error:
                flash(str(error), "danger")
                libro = request.form
        return render_template("formulario.html", titulo_pagina="Editar libro", libro=libro, accion="editar_libro", id_libro=id_libro)
    except RedisError:
        flash("No se pudo comunicar con KeyDB.", "danger")
        return redirect(url_for("inicio"))


@app.route("/eliminar/<int:id_libro>", methods=["POST"])
def eliminar_libro(id_libro):
    try:
        eliminar(db, id_libro)
        flash("Libro eliminado correctamente.", "success")
    except LibroNoEncontradoError as error:
        flash(str(error), "warning")
    except (ValueError, RedisError):
        flash("No se pudo eliminar el libro.", "danger")
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
