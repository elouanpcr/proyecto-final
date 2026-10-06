import os, random, difflib, unicodedata
from flask import Flask, render_template, request, session, redirect, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))
app.secret_key = "cambia-esta-clave"  # necesaria para guardar el historial

# Contenedores: puedes cambiar nombres y colores segun tu pais
CONTENEDORES = {
    "azul":    {"nombre": "Papel y cartón",        "color": "#2f6fb5"},
    "amarillo":{"nombre": "Plásticos y envases",   "color": "#e0a800"},
    "verde":   {"nombre": "Vidrio",                "color": "#2e8b57"},
    "gris":    {"nombre": "Metales",               "color": "#6b7480"},
    "marron":  {"nombre": "Orgánicos / compost",   "color": "#8a5a3c"},
    "rojo":    {"nombre": "Residuos peligrosos (punto limpio)", "color": "#c0392b"},
    "negro":   {"nombre": "No reciclable",         "color": "#333b40"},
}

# tiempo = descomposicion aproximada
RESIDUOS = {
    "papel":    ("azul", "2 a 6 meses", "Debe estar limpio y seco. El papel con grasa no se recicla."),
    "carton":   ("azul", "1 año", "Aplana las cajas para ahorrar espacio."),
    "periodico":("azul", "6 meses", "Sepáralo del papel plastificado."),
    "vidrio":   ("verde", "más de 4.000 años", "Enjuaga el envase. No mezcles con espejos ni ampolletas."),
    "botella de vidrio": ("verde", "más de 4.000 años", "Quita la tapa y enjuágala."),
    "botella de plastico": ("amarillo", "450 años", "Aplástala y ciérrala con su tapa."),
    "plastico": ("amarillo", "100 a 500 años", "Revisa el número dentro del triángulo de reciclaje."),
    "bolsa de plastico": ("amarillo", "150 años", "Mejor reutilízala. Si está sucia, va a no reciclable."),
    "tetra pak":("amarillo", "30 años", "Enjuaga y aplana el envase."),
    "lata":     ("gris", "10 a 100 años", "Enjuaga y aplasta para ocupar menos espacio."),
    "aluminio": ("gris", "200 a 500 años", "Es 100% reciclable, sin perder calidad."),
    "cascara de fruta": ("marron", "2 a 5 semanas", "Ideal para compostera."),
    "restos de comida": ("marron", "1 a 4 semanas", "Evita carnes y lácteos en la compostera casera."),
    "pila":     ("rojo", "más de 1.000 años", "Nunca a la basura común: contamina el agua y el suelo."),
    "bateria":  ("rojo", "más de 1.000 años", "Llévala a un punto limpio."),
    "celular":  ("rojo", "no se descompone", "Entrégalo a un punto de reciclaje electrónico."),
    "aceite":   ("rojo", "1 litro contamina 1.000 litros de agua", "Guárdalo en una botella cerrada y llévalo a un punto limpio."),
    "ampolleta":("rojo", "4.000 años", "Las de bajo consumo tienen mercurio."),
    "panal":    ("negro", "500 a 800 años", "No es reciclable: envuélvelo antes de botarlo."),
    "colilla":  ("negro", "10 años", "Una colilla puede contaminar hasta 50 litros de agua."),
}

def norm(t):
    t = unicodedata.normalize("NFD", t.lower().strip())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")

def buscar(texto):
    """Devuelve (clave, sugerencias). Busca exacto, por contenido o parecido."""
    q = norm(texto)
    if q in RESIDUOS:
        return q, []
    for clave in sorted(RESIDUOS, key=len, reverse=True):
        if clave in q or (len(q) > 3 and q in clave):
            return clave, []
    return None, difflib.get_close_matches(q, RESIDUOS.keys(), n=3, cutoff=0.5)

def datos(clave):
    cont, tiempo, tip = RESIDUOS[clave]
    return {"item": clave, "tiempo": tiempo, "tip": tip,
            "cont": cont, **CONTENEDORES[cont]}

@app.route("/", methods=["GET", "POST"])
def index():
    resultado, sugerencias, buscado = None, [], ""
    if request.method == "POST":
        buscado = request.form["item"]
        clave, sugerencias = buscar(buscado)
        if clave:
            resultado = datos(clave)
            hist = session.get("historial", [])
            hist = [h for h in hist if h != clave]
            session["historial"] = ([clave] + hist)[:8]
    return render_template("index.html", resultado=resultado,
                           sugerencias=sugerencias, buscado=buscado,
                           historial=session.get("historial", []))

@app.route("/info", methods=["GET", "POST"])
def info():
    item = request.values.get("item", "")
    clave, sugerencias = buscar(item) if item else (None, [])
    return render_template("info.html", r=datos(clave) if clave else None,
                           item=item, sugerencias=sugerencias)

@app.route("/guia")
def guia():
    grupos = {k: [i for i, v in RESIDUOS.items() if v[0] == k] for k in CONTENEDORES}
    return render_template("guia.html", contenedores=CONTENEDORES, grupos=grupos)

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        items = request.form.getlist("item")
        resp = [(i, request.form.get(f"r_{i}"), RESIDUOS[i][0]) for i in items if i in RESIDUOS]
        puntos = sum(1 for _, r, c in resp if r == c)
        return render_template("quiz.html", resp=resp, puntos=puntos,
                               total=len(resp), contenedores=CONTENEDORES)
    items = random.sample(list(RESIDUOS), 5)
    return render_template("quiz.html", items=items, contenedores=CONTENEDORES)

@app.route("/limpiar")
def limpiar():
    session.pop("historial", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
