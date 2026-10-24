import os, sqlite3
from contextlib import closing
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request

app=Flask(__name__)
DATABASE=os.environ.get("DATABASE_PATH", "adriano_cupcakes.sqlite3")
CATALOGO=[
 ("Chocolate Belga","Chocolate cremoso e cobertura especial",15.90),
 ("Morango","Massa de baunilha e creme de morango",14.50),
 ("Red Velvet","Massa vermelha com cobertura cremosa",16.90),
 ("Doce de Leite","Cupcake recheado com doce de leite",15.50),
 ("Baunilha","Cupcake clássico e delicado",12.90),
 ("Limão Siciliano","Massa cítrica e cobertura suave",14.90)]
def db_open():
    db=sqlite3.connect(DATABASE)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db
def init():
    with closing(db_open()) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS produtos(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,descricao TEXT NOT NULL,preco REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS pedidos(id INTEGER PRIMARY KEY AUTOINCREMENT,cliente TEXT NOT NULL,telefone TEXT NOT NULL,endereco TEXT NOT NULL,pagamento TEXT NOT NULL,total REAL NOT NULL,status TEXT NOT NULL DEFAULT 'Recebido',criado_em TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS itens_pedido(id INTEGER PRIMARY KEY AUTOINCREMENT,pedido_id INTEGER NOT NULL REFERENCES pedidos(id),produto_id INTEGER NOT NULL REFERENCES produtos(id),quantidade INTEGER NOT NULL CHECK(quantidade>0),preco_unitario REAL NOT NULL);
        """)
        if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]==0:
            db.executemany("INSERT INTO produtos(nome,descricao,preco) VALUES(?,?,?)",CATALOGO)
        db.commit()
@app.get("/")
def home(): return render_template("index.html")
@app.get("/api/produtos")
def produtos():
    with closing(db_open()) as db:
        return jsonify([dict(p) for p in db.execute("SELECT * FROM produtos ORDER BY id")])
@app.post("/api/pedidos")
def cadastrar_pedido():
    data=request.get_json(silent=True) or {}
    for campo in ("cliente","telefone","endereco"):
        if not isinstance(data.get(campo),str) or len(data[campo].strip())<3:
            return jsonify(erro="Preencha corretamente: "+campo),400
    if data.get("pagamento") not in ("Pix demonstrativo","Cartão demonstrativo","Boleto demonstrativo"):
        return jsonify(erro="Pagamento demonstrativo inválido"),400
    itens=data.get("itens")
    if not isinstance(itens,list) or not 1<=len(itens)<=40:
        return jsonify(erro="Carrinho vazio ou inválido"),400
    with closing(db_open()) as db:
        validos=[]
        for item in itens:
            if not isinstance(item,dict) or type(item.get("id")) is not int or type(item.get("quantidade")) is not int or not 1<=item["quantidade"]<=50:
                return jsonify(erro="Produto ou quantidade inválidos"),400
            p=db.execute("SELECT * FROM produtos WHERE id=?",(item["id"],)).fetchone()
            if p is None: return jsonify(erro="Produto não encontrado"),400
            validos.append((p,item["quantidade"]))
        centavos=sum(round(p["preco"]*100)*q for p,q in validos)
        cursor=db.execute("INSERT INTO pedidos(cliente,telefone,endereco,pagamento,total,criado_em) VALUES(?,?,?,?,?,?)",
            (data["cliente"].strip()[:120],data["telefone"].strip()[:40],data["endereco"].strip()[:240],data["pagamento"],centavos/100,datetime.now(timezone.utc).isoformat()))
        db.executemany("INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES(?,?,?,?)",
            [(cursor.lastrowid,p["id"],q,p["preco"]) for p,q in validos])
        db.commit()
        return jsonify(numero=cursor.lastrowid,total=centavos/100,status="Recebido"),201
@app.get("/api/pedidos/<int:numero>")
def consultar_pedido(numero):
    telefone=request.args.get("telefone","").strip()
    if not telefone: return jsonify(erro="Informe o telefone do pedido"),400
    with closing(db_open()) as db:
        p=db.execute("SELECT id,status,total,criado_em FROM pedidos WHERE id=? AND telefone=?",(numero,telefone)).fetchone()
        if not p: return jsonify(erro="Pedido não encontrado"),404
        return jsonify(dict(p))
init()
if __name__=="__main__":app.run(debug=os.environ.get("FLASK_DEBUG")=="1")
