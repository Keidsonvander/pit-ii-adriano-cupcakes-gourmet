import importlib, os, tempfile, unittest
class TesteCupcakes(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  os.environ["DATABASE_PATH"]=os.path.join(self.tmp.name,"teste.sqlite3")
  import app
  self.client=importlib.reload(app).app.test_client()
 def tearDown(self): self.tmp.cleanup()
 def test_produtos(self):
  r=self.client.get("/api/produtos")
  self.assertEqual(r.status_code,200)
  self.assertEqual(len(r.json),6)
 def test_pedido(self):
  data={"cliente":"Pessoa Teste","telefone":"11999999999","endereco":"Rua Teste, 15","pagamento":"Pix demonstrativo","itens":[{"id":1,"quantidade":2}]}
  r=self.client.post("/api/pedidos",json=data)
  self.assertEqual(r.status_code,201)
  consulta=self.client.get(f"/api/pedidos/{r.json['numero']}?telefone=11999999999")
  self.assertEqual(consulta.status_code,200)
 def test_carrinho_vazio(self):
  data={"cliente":"Pessoa Teste","telefone":"11999999999","endereco":"Rua Teste, 15","pagamento":"Pix demonstrativo","itens":[]}
  self.assertEqual(self.client.post("/api/pedidos",json=data).status_code,400)
if __name__=="__main__":unittest.main()
