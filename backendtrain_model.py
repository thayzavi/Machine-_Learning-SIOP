import pandas as pd 
from pymongo import MongoClient
from xgboost import XGBClassifier 
from sklearn.preprocessing import OneHotEncoder, LabelEncoder 
from sklearn.compose import ColumnTransformer 
from sklearn.pipeline import Pipeline 
import pickle 

# 1. Conectar no MongoDB e puxar dados [cite: 1]
client = MongoClient("mongodb://localhost:27017/") 
db = client["meu_banco"] 
colecao = db["meus_dados"] 

dados = list(colecao.find({}, {"_id": 0}))

# 2. Preparar DataFrame flat [cite: 1]
lista = [] 
for d in dados: 
    lista.append({ 
        "idade": d["vitima"]["idade"],
        "etnia": d["vitima"]["etnia"], 
        "localizacao": d["localizacao"], 
        "tipo_do_caso": d["tipo_do_caso"] 
    }) [cite: 1]
df = pd.DataFrame(lista) 

# 3. Variaveis explicativas e alvo
X = df[["idade", "etnia", "localizacao"]]
y = df["tipo_do_caso"]

# 4. Encode da variavel alvo [cite: 1]
label_encoder = LabelEncoder() 
y_encoded = label_encoder.fit_transform(y)

# 5. Pipeline [cite: 1]
categorical_features = ["etnia", "localizacao"] 
numeric_features = ["idade"] 

preprocessor = ColumnTransformer( 
    transformers=[ 
        ("cat", OneHotEncoder(handle_unknown='ignore'), categorical_features), 
        ("num", "passthrough", numeric_features)
    ] 
) 

pipeline = Pipeline([ 
    ("preprocessor", preprocessor), 
    ("classifier", XGBClassifier(use_label_encoder=False, eval_metric='mlogloss'))
]) 

# 6. Treinar [cite: 1]
pipeline.fit(X, y_encoded) 

# 7. Salvar pipeline + label encoder 
with open("model.pkl", "wb") as f: 
    pickle.dump({ 
        "pipeline": pipeline, 
        "label_encoder": label_encoder 
    }, f) 
print("Modelo treinado e salvo em model.pkl") 