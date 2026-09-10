import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as variáveis do arquivo .env
load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

# Inicializa o cliente do Supabase no Python
supabase: Client = create_client(URL, KEY)

app = FastAPI()

# 🌐 Configuração de CORS: Permite que o seu site na Vercel converse com o Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, substitua pelo link da sua Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a estrutura de dados que o Python espera receber
class AnaliseRequest(BaseModel):
    cliente_id: str

@app.get("/")
def rota_inicial():
    return {"status": "API Python do Modelo Híbrido ativa!"}

# Rota complexa que processa dados do cliente e atualiza o Supabase
# LOCALIZE E SUBSTITUA APENAS ESSA ROTA NO SEU MAIN.PY:

@app.post("/clientes/analisar")
async def analisar_cliente(request: AnaliseRequest):
    try:
        # Busca o cliente específico pelo ID vindo do Next.js
        resposta = supabase.table("clientes").select("*").eq("id", request.cliente_id).execute()
        
        # Se o banco não devolver nada ou der erro, avisa
        if not resposta.data:
            print("❌ Erro: Cliente não encontrado no Supabase.")
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
            
        cliente = resposta.data[0] # Pega o primeiro cliente da lista retornada
        
        # 🌟 CORREÇÃO AQUI: Buscando a coluna 'idade' corretamente do banco
        idade_cliente = cliente.get("idade", 0) 
        
        # Aplica a regra de negócio baseada na idade real
        perfil_credito = "Aprovado" if idade_cliente >= 18 else "Bloqueado"
        
        print(f"✅ Análise concluída para {cliente.get('nome')}: {perfil_credito}")
        
        return {
            "cliente_nome": cliente.get("nome"),
            "analise": perfil_credito,
            "mensagem": "Sucesso"
        }
        
    except Exception as e:
        # Isso vai imprimir o erro exato no terminal do seu Python para você ler
        print(f"❌ ERRO INTERNO NO PYTHON: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
