from flask import Flask, jsonify
from flask_cors import CORS
from flask import request, abort
from pymongo import MongoClient
from dataclasses import dataclass, asdict
import random
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# MongoDB Connection
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["meu_banco"]
colecao = db["meus_dados"]

@dataclass
class Vitima:
    etnia: str
    idade: int

@dataclass
class Caso:
    data_do_caso: str
    tipo_do_caso: str
    localizacao: str
    vitima: Vitima

    def to_dict(self):
        return {
            "data_do_caso": self.data_do_caso,
            "tipo_do_caso": self.tipo_do_caso,
            "localizacao": self.localizacao,
            "vitima": asdict(self.vitima)
        }

def gerar_dados_aleatorios(n=20):
    tipos_casos = ["Furto", "Assalto", "Violencia domestica", "Trafico"]
    locais = ["Centro", "Bairro A", "Bairro B", "Zona Rural"]
    etnias = ["Branca", "Preta", "Parda", "Indigena", "Amarela"]
    casos = []
    base_date = datetime.now()
    for i in range(n):
        caso = Caso(
            data_do_caso=(base_date - timedelta(days=random.randint(0, 365))).date().isoformat(),
            tipo_do_caso=random.choice(tipos_casos),
            localizacao=random.choice(locais),
            vitima=Vitima(
                etnia=random.choice(etnias),
                idade=random.randint(1, 90)
            )
        )
        casos.append(caso.to_dict())
    return casos

if __name__ == "__main__":
    if colecao.count_documents({}) == 0:
        print("Inserindo dados iniciais...")
        dados_iniciais = gerar_dados_aleatorios(20)
        colecao.insert_many(dados_iniciais)
    app.run(debug=True)

def validar_caso_json(data):
    try:
        vitima = data["vitima"]
        assert isinstance(vitima, dict)
        assert all(k in vitima for k in ("etnia", "idade"))
        datetime.fromisoformat(data["data_do_caso"])
        assert isinstance(data["tipo_do_caso"], str)
        assert isinstance(data["localizacao"], str)
    except:
        return False
    return True

with open("model.pkl", "rb") as f:
    data = pickle.load(f)
    modelo = data["pipeline"]
    label_encoder = data["label_encoder"]

@app.route('/api/casos', methods=['GET'])
def listar_casos():
    documentos = list(colecao.find({}, {"_id":0}))
    return jsonify(documentos), 200


@app.route('/api/casos', methods=['POST'])
def criar_caso():
    data = request.get_json()
    if not data or not validar_caso_json(data):
        abort(400, "JSON inválido ou campos faltando.")
    colecao.insert_one(data)
    return jsonify({"message": "Caso criado com sucesso"}), 201

@app.route('/api/casos/<string:data_caso>', methods=['GET'])
def buscar_caso(data_caso):
    caso = colecao.find_one({"data_do_caso": data_caso}, {"_id": 0})
    if not caso:
        abort(404, "Caso não encontrado.")
    return jsonify(caso), 200

@app.route('/api/casos/<string:data_caso>', methods=['DELETE'])
def deletar_caso(data_caso):
    resultado = colecao.delete_one({"data_do_caso": data_caso})
    if resultado.deleted_count == 0:
        abort(404, "Caso não encontrado.")
    return jsonify({"message": "Caso deletado"}), 200

@app.route('/api/associacoes', methods=['GET'])
def associacoes():
    documentos = list(colecao.find({}, {"_id": 0}))
    if not documentos:
        return jsonify({"message": "Sem dados na coleção"}), 400
    lista = []
    for d in documentos:
        vitima = d.get("vitima", {})
        lista.append({
            "idade": vitima.get("idade"),
            "etnia": vitima.get("etnia"),
            "localizacao": d.get("localizacao"),
            "tipo_do_caso": d.get("tipo_do_caso")
        })
    df = pd.DataFrame(lista).dropna()
    try:
        X = df[["idade", "etnia", "localizacao"]]
        # Placeholder para análise futura
        return jsonify({"message": "Endpoint pronto para implementar análise"}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao processar modelo: {str(e)}"}), 500

@app.route('/api/predizer', methods=['POST'])
def predizer():
    dados = request.get_json()
    if not dados or not all(k in dados for k in ("idade", "etnia", "localizacao")):
        return jsonify({"erro": "JSON inválido. Esperando: idade, etnia, localizacao"}), 400
    try:
        df = pd.DataFrame([dados])
        y_prob = modelo.predict_proba(df)[0]
        y_pred_encoded = modelo.predict(df)[0]
        y_pred = label_encoder.inverse_transform([y_pred_encoded])[0]
        classes = label_encoder.classes_
        resultado = {
            "classe_predita": y_pred,
            "probabilidades": {classe: round(prob, 4) for classe, prob in zip(classes, y_prob)}
        }
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao fazer predição: {str(e)}"}),500