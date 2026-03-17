"""Popula dados mock de feedbacks municipais no Supabase"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env from project root (Diretorios antigravit/.env)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Try local .env in prefeitura folder just in case
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL e SUPABASE_KEY são necessários no .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

now = datetime.utcnow()

# Get current max ID to avoid sequence errors
try:
    print("🔍 Buscando último ID...")
    max_id_resp = supabase.table('feedbacks').select('id').order('id', desc=True).limit(1).execute()
    start_id = 1
    if max_id_resp.data:
        start_id = max_id_resp.data[0]['id'] + 1
    print(f"🔢 Iniciando inserção a partir do ID: {start_id}")
except Exception as e:
    print(f"⚠️ Erro ao buscar último ID: {e}")
    start_id = 1

def make_feedback(id_val, sender, name, message, time_offset, category, region, urgency, sentiment, topic, status="aberto", resolved_at=None):
    return {
        "id": id_val,
        "sender": sender,
        "name": name,
        "message": message,
        "timestamp": (now - time_offset).isoformat(),
        "category": category,
        "region": region,
        "urgency": urgency,
        "sentiment": sentiment,
        "topic": topic,
        "status": status,
        "resolved_at": resolved_at
    }

mock_data = [
    make_feedback(start_id + 0, "5511999990001", "Maria Silva", "Tem um buraco enorme na Rua das Flores, zona norte. Já furou 2 pneus!", timedelta(minutes=5), "Infraestrutura & Obras", "Zona Norte", "Urgente", "Negativo", "Buraco Na Via"),
    make_feedback(start_id + 1, "5511999990002", "João Santos", "Parabéns à prefeitura! Arrumaram a praça do centro, ficou linda demais!", timedelta(minutes=12), "Limpeza & Meio Ambiente", "Centro", "Positivo", "Positivo", "Praça Reformada"),
    make_feedback(start_id + 2, "5511999990003", "Ana Oliveira", "Posto de saúde da zona sul tá sem médico há 3 dias! Absurdo! Minha filha tá doente.", timedelta(minutes=20), "Saúde & Atendimento", "Zona Sul", "Urgente", "Negativo", "Saúde"),
    make_feedback(start_id + 3, "5511999990004", "Carlos Ferreira", "Assalto agora na praça central! Tem gente armada! Cadê a guarda municipal?!", timedelta(minutes=2), "Segurança Pública", "Centro", "Critico", "Negativo", "Segurança"),
    make_feedback(start_id + 4, "5511999990005", "Fernanda Lima", "Ônibus da linha 42 atrasado de novo, faz 40 minutos esperando no ponto da zona leste", timedelta(minutes=35), "Transporte & Mobilidade", "Zona Leste", "Urgente", "Negativo", "Ônibus"),
    make_feedback(start_id + 5, "5511999990006", "Roberto Almeida", "Escola municipal do bairro oeste não tem merenda há uma semana. As crianças ficam com fome!", timedelta(minutes=45), "Educação & Escolas", "Zona Oeste", "Urgente", "Negativo", "Escola"),
    make_feedback(start_id + 6, "5511999990007", "Lucia Costa", "Esgoto aberto na rua principal da zona leste, mau cheiro horrível, tem rato saindo", timedelta(minutes=55), "Infraestrutura & Obras", "Zona Leste", "Urgente", "Negativo", "Esgoto"),
    make_feedback(start_id + 7, "5511999990008", "Pedro Mendes", "A nova ciclovia ficou muito boa, parabéns! Top demais, curti muito!", timedelta(minutes=60), "Transporte & Mobilidade", "Centro", "Positivo", "Positivo", "Ciclovia"),
    make_feedback(start_id + 8, "5511999990009", "Beatriz Ramos", "Semáforo quebrado no cruzamento da Av. Brasil com Rua 7, quase causou acidente!", timedelta(hours=1, minutes=15), "Transporte & Mobilidade", "Zona Norte", "Urgente", "Negativo", "Semáforo"),
    make_feedback(start_id + 9, "5511999990010", "Marcos Souza", "Terreno baldio na zona rural cheio de entulho e lixo, tá virando foco de dengue", timedelta(hours=1, minutes=30), "Limpeza & Meio Ambiente", "Zona Rural", "Urgente", "Negativo", "Lixo/Sujeira"),
    make_feedback(start_id + 10, "5511999990011", "Camila Rodrigues", "Calçada toda quebrada na frente da escola, idosos estão caindo! Zona sul", timedelta(hours=2), "Infraestrutura & Obras", "Zona Sul", "Urgente", "Negativo", "Calçada", "em_andamento"),
    make_feedback(start_id + 11, "5511999990012", "Diego Martins", "Obrigado por consertarem a iluminação da minha rua! Agora tá seguro de noite. Show!", timedelta(hours=2, minutes=20), "Infraestrutura & Obras", "Zona Oeste", "Positivo", "Positivo", "Iluminação", "resolvido", (now - timedelta(hours=1)).isoformat()),
    make_feedback(start_id + 12, "5511999990013", "Patrícia Nunes", "Vazamento de água enorme na Rua 15, distrito industrial. A rua tá alagando!", timedelta(hours=2, minutes=45), "Infraestrutura & Obras", "Distrito Industrial", "Critico", "Negativo", "Vazamento"),
    make_feedback(start_id + 13, "5511999990014", "Thiago Barros", "Falta de remédio na UBS central, minha mãe precisa do remédio de pressão e não tem!", timedelta(hours=3), "Saúde & Atendimento", "Centro", "Urgente", "Negativo", "Saúde", "em_andamento"),
    make_feedback(start_id + 14, "5511999990015", "Juliana Pereira", "A coleta de lixo na zona norte não passa há 4 dias, lixo acumulando nas ruas", timedelta(hours=3, minutes=30), "Limpeza & Meio Ambiente", "Zona Norte", "Urgente", "Negativo", "Coleta De Lixo"),
    make_feedback(start_id + 15, "5511999990016", "André Vieira", "Muito bom o novo parque da zona sul, as crianças adoraram! Arrasou prefeitura!", timedelta(hours=4), "Limpeza & Meio Ambiente", "Zona Sul", "Positivo", "Positivo", "Parque"),
    make_feedback(start_id + 16, "5511999990017", "Renata Dias", "Poste de luz caiu na estrada da zona rural, fio solto no chão! Perigo de morte!", timedelta(hours=4, minutes=15), "Infraestrutura & Obras", "Zona Rural", "Critico", "Negativo", "Poste Caiu"),
    make_feedback(start_id + 17, "5511999990018", "Felipe Gomes", "Creche da zona leste tá com vaga sobrando mas não aceita matrícula, que palhaçada!", timedelta(hours=5), "Educação & Escolas", "Zona Leste", "Urgente", "Negativo", "Escola"),
    make_feedback(start_id + 18, "5511999990019", "Isabela Moura", "Pessoa desmaiou no terminal de ônibus da zona norte, precisa de ambulância urgente!", timedelta(minutes=1), "Segurança Pública", "Zona Norte", "Critico", "Negativo", "Emergência Médica"),
    make_feedback(start_id + 19, "5511999990020", "Lucas Cardoso", "Mato alto na praça do bairro oeste, não dá nem pra andar. Precisa de capina urgente", timedelta(hours=5, minutes=30), "Limpeza & Meio Ambiente", "Zona Oeste", "Urgente", "Negativo", "Mato Alto"),
]

# Insert into Supabase
print("🏛️ Inserindo dados mock no Supabase...")
try:
    result = supabase.table('feedbacks').insert(mock_data).execute()
    print(f"✅ {len(mock_data)} feedbacks municipais inseridos com sucesso!")
    print(f"📊 Categorias: Infraestrutura, Saúde, Educação, Segurança, Limpeza, Transporte")
    print(f"📍 Regiões: Centro, ZN, ZS, ZL, ZO, Dist. Industrial, Z. Rural")
    print(f"🔴 4 críticos | 🟡 10 urgentes | 🟢 4 positivos | ⚪ 2 neutros")
except Exception as e:
    print(f"❌ Erro ao inserir: {e}")
