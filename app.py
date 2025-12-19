import streamlit as st
from supabase import create_client
import google.generativeai as genai
import pandas as pd
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Friends Language Center", page_icon="🏫", layout="wide")

# --- BARRA LATERAL (CONFIGURAÇÃO) ---
st.sidebar.title("🏫 Friends School")
st.sidebar.markdown("---")

# Tenta pegar as senhas dos 'Segredos' do Streamlit (para quando você configurar depois)
# Se não achar, pede para você digitar na hora (mais fácil agora)
if 'SUPABASE_URL' in st.secrets:
    SUPABASE_URL = st.secrets['SUPABASE_URL']
    SUPABASE_KEY = st.secrets['SUPABASE_KEY']
    GOOGLE_API_KEY = st.secrets['GOOGLE_API_KEY']
else:
    st.sidebar.warning("🔐 Digite suas chaves para entrar")
    SUPABASE_URL = st.sidebar.text_input("URL Supabase", type="password")
    SUPABASE_KEY = st.sidebar.text_input("Chave Public (Anon)", type="password")
    GOOGLE_API_KEY = st.sidebar.text_input("Chave Google AI", type="password")

# Se faltar alguma chave, para por aqui
if not (SUPABASE_URL and SUPABASE_KEY and GOOGLE_API_KEY):
    st.sidebar.info("Preencha os campos acima para carregar o sistema.")
    st.stop()

# --- CONEXÃO COM O BANCO E A IA ---
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"Erro ao conectar: {e}")
    st.stop()

# --- FUNÇÕES (O TRABALHO PESADO) ---
def buscar_alunos():
    response = supabase.table('alunos').select("*").execute()
    return pd.DataFrame(response.data)

def matricular_aluno(nome, nivel, nascimento):
    dados = {
        "nome": nome,
        "nivel_ingles": nivel,
        "data_nascimento": str(nascimento),
        "ativo": True
    }
    supabase.table('alunos').insert(dados).execute()

def ia_analisar_aluno(nome, nivel):
    prompt = f"""
    Aja como coordenador pedagógico da escola de idiomas Friends.
    O aluno {nome} é do nível {nivel}.
    Escreva um parágrafo curto e motivador parabenizando pelo progresso
    e sugira 2 dicas de estudo específicas para esse nível.
    """
    with st.spinner('O Gemini está pensando...'):
        response = model.generate_content(prompt)
    return response.text

# --- TELA PRINCIPAL ---
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "📝 Nova Matrícula", "🤖 Análise IA"])

if menu == "📊 Dashboard":
    st.header("Visão Geral da Escola")
    try:
        df = buscar_alunos()
        if not df.empty:
            col1, col2 = st.columns(2)
            col1.metric("Total de Alunos", len(df))
            col1.metric("Turmas Ativas", df['nivel_ingles'].nunique())
            st.dataframe(df)
        else:
            st.info("Nenhum aluno cadastrado ainda. Vá em 'Nova Matrícula'.")
    except Exception as e:
        st.error("Erro ao buscar dados. Verifique se a tabela 'alunos' existe no Supabase.")

elif menu == "📝 Nova Matrícula":
    st.header("Matricular Aluno")
    with st.form("form_matricula"):
        nome = st.text_input("Nome Completo")
        nivel = st.selectbox("Nível", ["Kids", "Teens 1", "Teens 2", "Basic", "Intermediate", "Advanced"])
        nasc = st.date_input("Data de Nascimento", min_value=datetime.date(1920, 1, 1))
        
        if st.form_submit_button("Salvar Matrícula"):
            matricular_aluno(nome, nivel, nasc)
            st.success(f"Aluno {nome} salvo com sucesso!")
            st.balloons()

elif menu == "🤖 Análise IA":
    st.header("Consultoria Pedagógica com IA")
    df = buscar_alunos()
    if not df.empty:
        aluno = st.selectbox("Escolha o aluno:", df['nome'])
        dados = df[df['nome'] == aluno].iloc[0]
        
        if st.button("Gerar Relatório"):
            st.write(f"Analisando perfil de **{aluno}** ({dados['nivel_ingles']})...")
            resultado = ia_analisar_aluno(aluno, dados['nivel_ingles'])
            st.markdown("### 📢 Relatório do Coordenador:")
            st.write(resultado)
