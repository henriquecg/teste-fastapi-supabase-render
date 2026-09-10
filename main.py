import os
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

# Define o nome do cabeçalho que vamos exigir
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Carrega as variáveis do arquivo .env
load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
# Pega o token secreto que você vai cadastrar no painel da Render
API_TOKEN_SECRETO = os.getenv("API_TOKEN_SECRETO")

async def verificar_token(api_key: str = Depends(api_key_header)):
    if api_key != API_TOKEN_SECRETO:
        raise HTTPException(status_code=403, detail="Acesso negado: Token inválido ou ausente.")
    return api_key

# Inicializa o cliente do Supabase no Python
supabase: Client = create_client(URL, KEY)

app = FastAPI()

# 🌐 Configuração de CORS: Permite que o seu site na Vercel converse com o Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", # Mantém para testes locais
        "https://teste-nextjs-supabase.vercel.app/clientes/lista" # Substitua pela URL real da sua Vercel
    ], # Em produção, substitua pelo link da sua Vercel
    allow_credentials=True,
    allow_methods=["POST"],
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
async def analisar_cliente(request: AnaliseRequest, token: str = Depends(verificar_token)):
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

@app.delete("/clientes/excluir/{cliente_id}")
async def excluir_cliente(cliente_id: str):
    try:
        # O Python usa a service_role e consegue deletar mesmo com o RLS ativado
        resposta = supabase.table("clientes").delete().eq("id", cliente_id).execute()
        
        if not resposta.data:
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
            
        return {"status": "sucesso", "mensagem": "Cliente removido com segurança pelo backend."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))