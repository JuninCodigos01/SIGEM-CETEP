import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta, time

# Configuração Inicial da Página
st.set_page_config(
    page_title="SIGEM - Gestão Escolar & Mecanografia", 
    page_icon="🏫", 
    layout="wide"
)

# -----------------------------------------------------------------------------
# 1. BANCO DE DADOS
# -----------------------------------------------------------------------------

def conectar_bd():
    conn = sqlite3.connect("escola.db", check_same_thread=False)
    return conn

def inicializar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Curso (
            id_curso INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100),
            descricao VARCHAR(100)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Turma (
            id_turma INTEGER PRIMARY KEY AUTOINCREMENT,
            Curso_id_curso INTEGER,
            nome VARCHAR(100),
            ano INTEGER,
            turno VARCHAR(20),
            FOREIGN KEY (Curso_id_curso) REFERENCES Curso(id_curso)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(30),
            email VARCHAR(100),
            telefone VARCHAR(20),
            tipo_usuario VARCHAR(30)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Arquivo (
            id_arquivo INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo VARCHAR(255),
            tipo_arquivo VARCHAR(50),
            local_arquivo BLOB,
            data_recebimento DATETIME
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Solicitacao (
            id_solicitacao INTEGER PRIMARY KEY AUTOINCREMENT,
            Arquivo_id_arquivo INTEGER,
            Usuario_id_usuario INTEGER,
            tipo_origem VARCHAR(20),
            qtd INTEGER,
            tipo_impressao VARCHAR(30),
            acabamento VARCHAR(100),
            observacao INTEGER,
            data_solicitacao DATETIME,
            status_atual VARCHAR(30),
            FOREIGN KEY (Arquivo_id_arquivo) REFERENCES Arquivo(id_arquivo),
            FOREIGN KEY (Usuario_id_usuario) REFERENCES Usuario(id_usuario)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Disciplina (
            id_disciplina INTEGER PRIMARY KEY AUTOINCREMENT,
            Curso_id_curso INTEGER,
            Solicitacao_id_solicitacao INTEGER,
            Solicitacao_Arquivo_id_arquivo INTEGER,
            Solicitacao_Usuario_id_usuario INTEGER,
            nome VARCHAR(100),
            FOREIGN KEY (Curso_id_curso) REFERENCES Curso(id_curso),
            FOREIGN KEY (Solicitacao_id_solicitacao) REFERENCES Solicitacao(id_solicitacao)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email (
            id_email INTEGER PRIMARY KEY AUTOINCREMENT,
            Solicitacao_id_solicitacao INTEGER,
            Solicitacao_Arquivo_id_arquivo INTEGER,
            Solicitacao_Usuario_id_usuario INTEGER,
            email_remetente VARCHAR(150),
            assunto VARCHAR(255),
            data_recebimento DATETIME,
            identificador_email VARCHAR(255),
            FOREIGN KEY (Solicitacao_id_solicitacao) REFERENCES Solicitacao(id_solicitacao)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Historico_Status (
            id_historico INTEGER PRIMARY KEY AUTOINCREMENT,
            Solicitacao_id_solicitacao INTEGER,
            FOREIGN KEY (Solicitacao_id_solicitacao) REFERENCES Solicitacao(id_solicitacao)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumos (
            codigo INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT UNIQUE,
            qtd_estoque INTEGER,
            qtd_minima INTEGER,
            unidade TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Mov_Estoque (
            id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
            Usuario_id_usuario INTEGER,
            Insumo_id_insumo INTEGER,
            qtd DECIMAL(10,2),
            tipo_movimentacao VARCHAR(10),
            data_movimentacao DATETIME,
            observacao VARCHAR(255),
            FOREIGN KEY (Usuario_id_usuario) REFERENCES Usuario(id_usuario),
            FOREIGN KEY (Insumo_id_insumo) REFERENCES insumos(codigo)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            login TEXT PRIMARY KEY,
            senha TEXT,
            nivel TEXT,
            nome TEXT,
            email TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitante TEXT,
            nivel TEXT,
            tipo TEXT,
            recurso TEXT,
            quantidade INTEGER,
            data_reserva TEXT,
            horario TEXT,
            observacao TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS impressoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitante TEXT,
            email TEXT,
            tipo_documento TEXT,
            data_necessidade TEXT,
            copias INTEGER,
            cor TEXT,
            observacao TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            categoria TEXT,
            qtd_total INTEGER
        )
    """)

    # Usuários Padrão
    usuarios_padrao = [
        ("DBA", "2525", "Administrador", "Ryan", "ryan@gmail.com"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?,?)", usuarios_padrao)

    # Insumos Padrão
    insumos_padrao = [
        ("Papel A4 (Folhas)", 5000, 1000, "Unidades"),
        ("Toner HP Preto", 10, 2, "Unidades"),
        ("Toner HP Colorido", 5, 1, "Unidades")
    ]
    cursor.executemany("INSERT OR IGNORE INTO insumos (descricao, qtd_estoque, qtd_minima, unidade) VALUES (?,?,?,?)", insumos_padrao)

    # Equipamentos Padrão
    equipamentos_padrao = [
        ("Datashow", "Equipamento Tecnológico", 5),
        ("Controle da TV", "Equipamento Tecnológico", 4),
        ("Caixa de Som", "Equipamento Tecnológico", 3),
        ("Microfone", "Equipamento Tecnológico", 4),
        ("Bolas de Futebol", "Equipamento de Educação Física", 10),
        ("Bolas de Vôlei", "Equipamento de Educação Física", 8),
        ("Kits de Coletes", "Equipamento de Educação Física", 5),
        ("Cones de Treinamento", "Equipamento de Educação Física", 15)
    ]
    cursor.executemany("INSERT OR IGNORE INTO equipamentos (nome, categoria, qtd_total) VALUES (?,?,?)", equipamentos_padrao)

    conn.commit()
    conn.close()

inicializar_bd()

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_atual = None
    st.session_state.nivel_acesso = None
    st.session_state.nome_usuario = None
    st.session_state.email_usuario = None

# -----------------------------------------------------------------------------
# FUNÇÕES DE VALIDAÇÃO DE CONFLITO E SALDO DE MATERIAIS
# -----------------------------------------------------------------------------

def obter_estoque_equipamentos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, qtd_total FROM equipamentos")
    dados = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in dados}

def verificar_conflito_reserva(recurso, data_str, h_inicio, h_fim):
    """Bloqueia o laboratório caso exista QUALQUER reserva em aberto ou aprovada no mesmo horário."""
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT horario, status FROM reservas WHERE recurso = ? AND data_reserva = ? AND status IN ('Aprovada', 'Pendente')", (recurso, data_str))
    reservas = cursor.fetchall()
    conn.close()

    for horario_str, status in reservas:
        try:
            partes = horario_str.split(" às ")
            inicio_ex = datetime.strptime(partes[0].strip(), "%H:%M").time()
            fim_ex = datetime.strptime(partes[1].strip(), "%H:%M").time()

            if max(h_inicio, inicio_ex) < min(h_fim, fim_ex):
                return True, horario_str, status
        except Exception:
            continue
    return False, "", ""

def obter_quantidade_reservada(recurso, data_str, h_inicio, h_fim):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade, horario FROM reservas WHERE recurso = ? AND data_reserva = ? AND status IN ('Aprovada', 'Pendente')", (recurso, data_str))
    reservas = cursor.fetchall()
    conn.close()

    total = 0
    for qtd, horario_str in reservas:
        try:
            partes = horario_str.split(" às ")
            inicio_ex = datetime.strptime(partes[0].strip(), "%H:%M").time()
            fim_ex = datetime.strptime(partes[1].strip(), "%H:%M").time()

            if max(h_inicio, inicio_ex) < min(h_fim, fim_ex):
                total += qtd
        except Exception:
            continue
    return total

# -----------------------------------------------------------------------------
# 2. TELA DE LOGIN
# -----------------------------------------------------------------------------

def tela_login():
    st.title("🏫 Sistema Integrado de Gestão e Mecanografia (SIGEM)")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔑 Acesso ao Sistema")
        usuario_input = st.text_input("Usuário:")
        senha_input = st.text_input("Senha:", type="password")
        
        if st.button("Entrar", use_container_width=True):
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT senha, nivel, nome, email FROM usuarios WHERE login = ?", (usuario_input,))
            user = cursor.fetchone()
            conn.close()
            
            if user and user[0] == senha_input:
                st.session_state.logado = True
                st.session_state.usuario_atual = usuario_input
                st.session_state.nivel_acesso = user[1]
                st.session_state.nome_usuario = user[2]
                st.session_state.email_usuario = user[3]
                st.success(f"Bem-vindo(a), {st.session_state.nome_usuario}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# -----------------------------------------------------------------------------
# 3. SISTEMA PRINCIPAL
# -----------------------------------------------------------------------------

def sistema_principal():
    st.sidebar.title("👤 Perfil do Usuário")
    st.sidebar.write(f"**Nome:** {st.session_state.nome_usuario}")
    st.sidebar.write(f"**E-mail:** {st.session_state.email_usuario}")
    st.sidebar.write(f"**Nível:** `{st.session_state.nivel_acesso}`")
    
    if st.sidebar.button("Sair (Logout)"):
        st.session_state.logado = False
        st.rerun()

    st.title("📌 Painel de Gestão e Pedidos")

    abas = ["🖨️ Solicitar Impressão", "📅 Reservar Recursos", "📋 Painel de Solicitações"]
    if st.session_state.nivel_acesso in ["Administrador", "Coordenação"]:
        abas.append("📊 Gestão da Coordenação")
        
    guias = st.tabs(abas)

    # ABA 1: SOLICITAR IMPRESSÃO
    with guias[0]:
        st.header("🖨️ Solicitação de Impressão (Mecanografia)")
        
        data_minima = date.today() + timedelta(days=2)
        st.info("ℹ **Antes de fazer sua solicitação, envie o arquivo no e-mail. Essas informações serão necessárias apenas para confirmar sua identidade.**")
        
        with st.form("form_impressao", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Solicitante Cadastrado:", value=st.session_state.nome_usuario, disabled=True)
                email_prof = st.text_input("E-mail de Contato:", value=st.session_state.email_usuario)
                tipo_documento = st.selectbox(
                    "Tipo de Documento:", 
                    [".pdf", ".png", ".jpg", ".txt(Texto)", ".docx(Word)", ".pptx(PowerPoint)", ".xlsx(Excel)", "Outro"],
                    index=None,
                    placeholder="Selecione um formato..."
                )
                
            with col2:
                data_necessidade = st.date_input("Para quando precisa do material pronto?", min_value=data_minima, value=data_minima)
                qtd_copias = st.number_input("Quantidade de Cópias:", min_value=1, value=30)
                formato_cor = st.radio("Impressão:", ["Preto e Branco", "Colorida"])

            obs_impressao = st.text_area("Observações para a Mecanografia:", placeholder="Ex: Grampear em duplas, imprimir frente e verso.")
            
            btn_enviar_impressao = st.form_submit_button("Enviar Solicitação de Impressão")

            if btn_enviar_impressao:
                if not tipo_documento:
                    st.error("❌ Por favor, selecione o tipo de documento antes de enviar.")
                else:
                    conn = conectar_bd()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO impressoes (solicitante, email, tipo_documento, data_necessidade, copias, cor, observacao, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        st.session_state.nome_usuario, email_prof, tipo_documento, 
                        data_necessidade.strftime("%d/%m/%Y"), qtd_copias, formato_cor, 
                        obs_impressao if obs_impressao else "Sem observações", "Pendente"
                    ))
                    conn.commit()
                    conn.close()

                    st.success("✅ Solicitação gravada no banco de dados com sucesso!")

    # ABA 2: RESERVAR RECURSOS
    with guias[1]:
        st.header("Realizar Reserva de Recursos")
        
        tipo_reserva = st.selectbox(
            "O que você deseja reservar?",
            ["Laboratório", "Equipamento Tecnológico", "Equipamento de Educação Física"]
        )

        with st.form("form_reserva", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                data_reserva = st.date_input("Data da Reserva:", min_value=date.today())
                hora_inicio = st.time_input("Horário de Início:", value=time(7, 30))
                hora_fim = st.time_input("Horário de Término:", value=time(8, 20))

            with col2:
                recurso_selecionado = ""
                qtd_reservada = 1

                if tipo_reserva == "Laboratório":
                    recurso_selecionado = st.selectbox("Escolha o Laboratório:", [
                        "Laboratório de Informática 1",
                        "Laboratório de Informática 2",
                        "Laboratório de Ciências / Biologia",
                        "Laboratório de Química / Física"
                    ])
                    qtd_reservada = 1
                    
                elif tipo_reserva in ["Equipamento Tecnológico", "Equipamento de Educação Física"]:
                    conn = conectar_bd()
                    cursor = conn.cursor()
                    cursor.execute("SELECT nome FROM equipamentos WHERE categoria = ?", (tipo_reserva,))
                    opcoes = [r[0] for r in cursor.fetchall()]
                    conn.close()

                    if not opcoes:
                        st.warning("Nenhum equipamento dessa categoria cadastrado no sistema.")
                    else:
                        recurso_selecionado = st.selectbox("Escolha o Item:", opcoes)
                        
                        estoque_dict = obter_estoque_equipamentos()
                        max_total = estoque_dict.get(recurso_selecionado, 0)
                        
                        ja_reservados = obter_quantidade_reservada(recurso_selecionado, data_reserva.strftime("%d/%m/%Y"), hora_inicio, hora_fim)
                        disp_real = max(0, max_total - ja_reservados)
                        
                        if disp_real > 0:
                            qtd_reservada = st.number_input(f"Quantidade Disponível ({disp_real} livre(s)):", min_value=1, max_value=disp_real, value=1)
                        else:
                            st.error(f"❌ Nenhuma unidade disponível de {recurso_selecionado} para este horário.")
                            qtd_reservada = 0

            observacao = st.text_area("Observações / Finalidade Pedagógica:")
            btn_submeter = st.form_submit_button("Confirmar Reserva")

            if btn_submeter:
                if hora_inicio >= hora_fim:
                    st.error("❌ O horário de término deve ser posterior ao de início.")
                elif qtd_reservada <= 0:
                    st.error("❌ Quantidade indisponível para reserva.")
                else:
                    data_formatted = data_reserva.strftime("%d/%m/%Y")
                    em_uso, hor_conf, status_conf = verificar_conflito_reserva(recurso_selecionado, data_formatted, hora_inicio, hora_fim)
                    
                    if tipo_reserva == "Laboratório" and em_uso:
                        st.error(f"❌ O espaço **{recurso_selecionado}** já possui reserva no horário `{hor_conf}` (Status: {status_conf}). Apenas 1 usuário por horário.")
                    else:
                        conn = conectar_bd()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO reservas (solicitante, nivel, tipo, recurso, quantidade, data_reserva, horario, observacao, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            st.session_state.nome_usuario, st.session_state.nivel_acesso,
                            tipo_reserva, recurso_selecionado, qtd_reservada,
                            data_formatted, f"{hora_inicio.strftime('%H:%M')} às {hora_fim.strftime('%H:%M')}",
                            observacao if observacao else "Nenhuma", "Pendente"
                        ))
                        conn.commit()
                        conn.close()
                        st.success("✅ Reserva gravada com sucesso!")

    # ABA 3: PAINEL DE SOLICITAÇÕES
    with guias[2]:
        st.header("📋 Histórico de Pedidos e Reservas")
        conn = conectar_bd()
        
        st.subheader("🖨️ Solicitações de Impressão Enviadas")
        if st.session_state.nivel_acesso == "Professor":
            query_imp = "SELECT * FROM impressoes WHERE LOWER(email) = LOWER(?) OR LOWER(solicitante) = LOWER(?)"
            df_imp = pd.read_sql_query(query_imp, conn, params=(st.session_state.email_usuario, st.session_state.nome_usuario))
        else:
            df_imp = pd.read_sql_query("SELECT * FROM impressoes", conn)
            
        if not df_imp.empty:
            st.dataframe(df_imp, use_container_width=True)
        else:
            st.info("Nenhuma solicitação encontrada.")

        st.divider()

        st.subheader("📅 Reservas de Recursos (Laboratórios/Materiais)")
        if st.session_state.nivel_acesso == "Professor":
            query_res = "SELECT * FROM reservas WHERE LOWER(solicitante) = LOWER(?)"
            df_res = pd.read_sql_query(query_res, conn, params=(st.session_state.nome_usuario,))
        else:
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)

        if not df_res.empty:
            st.dataframe(df_res, use_container_width=True)
        else:
            st.info("Nenhuma reserva encontrada.")
        conn.close()

    # ABA 4: PAINEL DA COORDENAÇÃO / MECANOGRAFIA
    if st.session_state.nivel_acesso in ["Administrador", "Coordenação"]:
        with guias[3]:
            st.header("⚙️ Controle de Mecanografia e Gestão de Pedidos")
            conn = conectar_bd()
            cursor = conn.cursor()
            
            # GESTÃO DE USUÁRIOS (CADASTRO E REMOÇÃO COM CONFIRMAÇÃO DE SENHA PARA ADMIN)
            st.subheader("👥 Gestão de Usuários e Professores")
            
            df_usuarios = pd.read_sql_query("SELECT login AS 'Login', nome AS 'Nome Completo', email AS 'E-mail', nivel AS 'Nível de Acesso' FROM usuarios", conn)
            st.dataframe(df_usuarios, use_container_width=True)

            col_u1, col_u2 = st.columns(2)
            
            with col_u1:
                with st.expander("➕ Adicionar Novo Usuário"):
                    with st.form("form_novo_usuario", clear_on_submit=True):
                        nov_login = st.text_input("Login:")
                        nov_nome = st.text_input("Nome Completo:")
                        nov_email = st.text_input("E-mail:")
                        nov_senha = st.text_input("Senha Inicial:", type="password")
                        nov_nivel = st.selectbox("Nível de Acesso:", ["Professor", "Coordenação", "Administrador"])
                        
                        if st.form_submit_button("Cadastrar Usuário"):
                            if not nov_login or not nov_senha or not nov_nome:
                                st.error("❌ Preencha todos os campos obrigatórios.")
                            else:
                                try:
                                    cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?, ?)", (nov_login, nov_senha, nov_nivel, nov_nome, nov_email))
                                    conn.commit()
                                    st.success(f"✅ Usuário **{nov_nome}** ({nov_nivel}) cadastrado!")
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("❌ Login já cadastrado.")

            with col_u2:
                with st.expander("🗑️ Remover Usuário Cadastrado"):
                    cursor.execute("SELECT login, nome, nivel, senha FROM usuarios")
                    todos_usuarios = cursor.fetchall()
                    
                    dict_usuarios = {f"{nome} ({login} - {nivel})": (login, nivel, senha) for login, nome, nivel, senha in todos_usuarios}
                    
                    if dict_usuarios:
                        user_sel = st.selectbox("Selecione o Usuário para Excluir:", list(dict_usuarios.keys()))
                        login_excluir, nivel_excluir, senha_excluir = dict_usuarios[user_sel]
                        
                        senha_confirmacao = ""
                        if nivel_excluir == "Administrador":
                            st.warning("⚠️ **Atenção:** Este usuário é um **Administrador**. Insira a senha dele para confirmar a exclusão.")
                            senha_confirmacao = st.text_input("Senha do Administrador a ser removido:", type="password", key="pwd_confirm_del")

                        if st.button("❌ Confirmar Exclusão do Usuário", type="primary"):
                            if login_excluir == st.session_state.usuario_atual:
                                st.error("❌ Você não pode excluir o seu próprio usuário enquanto estiver conectado!")
                            elif nivel_excluir == "Administrador" and senha_confirmacao != senha_excluir:
                                st.error("❌ Senha incorreta! A exclusão do Administrador foi cancelada.")
                            else:
                                cursor.execute("DELETE FROM usuarios WHERE login = ?", (login_excluir,))
                                conn.commit()
                                st.warning(f"Usuário **{login_excluir}** foi removido do sistema com sucesso.")
                                st.rerun()

            st.divider()

            # ALERTAS DE ESTOQUE DE INSUMOS
            cursor.execute("SELECT descricao, qtd_estoque, qtd_minima, unidade FROM insumos WHERE qtd_estoque <= qtd_minima")
            for item in cursor.fetchall():
                st.warning(f"⚠️ **Insumo Crítico:** {item[0]} | Atual: {item[1]} {item[3]} (Mínimo: {item[2]} {item[3]})")

            # FILA DE IMPRESSÃO
            st.subheader("🖨️ Fila de Impressão Pendente")
            cursor.execute("SELECT * FROM impressoes WHERE status = 'Pendente'")
            impressoes_pendentes = cursor.fetchall()
            
            if impressoes_pendentes:
                for item in impressoes_pendentes:
                    imp_id, solicitante, email, tipo_doc, dt_necessidade, copias, cor, obs, status = item
                    with st.expander(f"Impressão #{imp_id} - {solicitante} ({tipo_doc})"):
                        st.write(f"**Para:** {dt_necessidade} | **Cópias:** {copias} ({cor})")
                        col1, col2 = st.columns(2)
                        
                        if col1.button("✅ Concluir e Dar Baixa", key=f"ap_imp_{imp_id}"):
                            cursor.execute("SELECT qtd_estoque FROM insumos WHERE descricao LIKE '%Papel A4%'")
                            res_papel = cursor.fetchone()
                            estoque_papel = res_papel[0] if res_papel else 0

                            if estoque_papel < copias:
                                st.error(f"❌ Estoque insuficiente de Papel A4! Necessário: {copias} | Atual: {estoque_papel}")
                            else:
                                cursor.execute("UPDATE insumos SET qtd_estoque = MAX(0, qtd_estoque - ?) WHERE descricao LIKE '%Papel A4%'", (copias,))
                                cursor.execute("UPDATE impressoes SET status = 'Aprovada / Concluída' WHERE id = ?", (imp_id,))
                                conn.commit()
                                st.success(f"Aprovado! Baixa de {copias} folhas realizada.")
                                st.rerun()
                                
                        if col2.button("❌ Recusar", key=f"rec_imp_{imp_id}"):
                            cursor.execute("UPDATE impressoes SET status = 'Recusada' WHERE id = ?", (imp_id,))
                            conn.commit()
                            st.rerun()
            else:
                st.info("Nenhuma solicitação de impressão pendente.")

            st.divider()

            # FILA DE RESERVAS PENDENTES
            st.subheader("📅 Fila de Reservas Pendentes")
            cursor.execute("SELECT * FROM reservas WHERE status = 'Pendente'")
            reservas_pendentes = cursor.fetchall()
            
            if reservas_pendentes:
                for item in reservas_pendentes:
                    res_id, solicitante, nivel, tipo_reserva_item, recurso, qtd, dt, hr, obs, status = item
                    with st.expander(f"Reserva #{res_id} - {solicitante} ({recurso})"):
                        st.write(f"**Data:** {dt} | **Horário:** {hr} | **Qtd:** {qtd}")
                        col_ap, col_rec = st.columns(2)
                        
                        if col_ap.button("✅ Aprovar Reserva", key=f"ap_res_{res_id}"):
                            cursor.execute("UPDATE reservas SET status = 'Aprovada' WHERE id = ?", (res_id,))
                            conn.commit()
                            st.success("Reserva aprovada!")
                            st.rerun()
                            
                        if col_rec.button("❌ Recusar Reserva", key=f"rec_res_{res_id}"):
                            cursor.execute("UPDATE reservas SET status = 'Recusada' WHERE id = ?", (res_id,))
                            conn.commit()
                            st.rerun()
            else:
                st.info("Nenhuma reserva pendente.")

            st.divider()

            # PAINEL DE DEVOLUÇÃO / BAIXA DE RECURSOS EM USO
            st.subheader("🔄 Recursos/Laboratórios Atualmente em Uso (Aprovados)")
            cursor.execute("SELECT * FROM reservas WHERE status = 'Aprovada'")
            reservas_em_uso = cursor.fetchall()

            if reservas_em_uso:
                for item in reservas_em_uso:
                    res_id, solicitante, nivel, tipo_reserva_item, recurso, qtd, dt, hr, obs, status = item
                    with st.expander(f"🔴 Em Uso #{res_id} - {recurso} (Reservado por: {solicitante})"):
                        st.write(f"**Data:** {dt} | **Horário:** {hr} | **Quantidade:** {qtd}")
                        st.write(f"**Obs:** {obs}")
                        if st.button("📥 Receber Devolta / Finalizar Uso", key=f"baixa_res_{res_id}"):
                            cursor.execute("UPDATE reservas SET status = 'Devolvido / Finalizado' WHERE id = ?", (res_id,))
                            conn.commit()
                            st.success(f"Uso do recurso **{recurso}** finalizado e liberado com sucesso!")
                            st.rerun()
            else:
                st.info("Nenhum recurso ou laboratório está atualmente marcado como 'Aprovado/Em Uso'.")

            st.divider()

            # REPOSIÇÃO, CADASTRO E REMOÇÃO DE ESTOQUE (MECANOGRAFIA)
            st.subheader("📦 Estoque de Insumos da Mecanografia")
            df_insumos = pd.read_sql_query("SELECT codigo AS 'Código', descricao AS 'Item', qtd_estoque AS 'Qtd Atual', qtd_minima AS 'Qtd Mínima', unidade AS 'Unidade' FROM insumos", conn)
            st.dataframe(df_insumos, use_container_width=True)

            col_ins1, col_ins2, col_ins3 = st.columns(3)
            with col_ins1:
                with st.expander("➕ Adicionar/Repor Estoque"):
                    cursor.execute("SELECT codigo, descricao FROM insumos")
                    lista_ins = cursor.fetchall()
                    if lista_ins:
                        opcoes_ins = {desc: cod for cod, desc in lista_ins}
                        item_sel = st.selectbox("Insumo:", list(opcoes_ins.keys()))
                        qtd_add = st.number_input("Qtd Recebida:", min_value=1, value=500)
                        
                        if st.button("Confirmar Entrada de Insumo"):
                            cursor.execute("UPDATE insumos SET qtd_estoque = qtd_estoque + ? WHERE codigo = ?", (qtd_add, opcoes_ins[item_sel]))
                            conn.commit()
                            st.success(f"Adicionadas {qtd_add} unidades de {item_sel}!")
                            st.rerun()

            with col_ins2:
                with st.expander("🆕 Cadastrar Novo Insumo"):
                    novo_nome = st.text_input("Nome do Produto:")
                    nova_qtd = st.number_input("Quantidade Inicial:", min_value=0, value=100)
                    nova_qtd_min = st.number_input("Mínimo de Alerta:", min_value=1, value=20)
                    nova_un = st.text_input("Unidade:", value="Unidades")
                    
                    if st.button("Cadastrar Insumo"):
                        if novo_nome:
                            try:
                                cursor.execute("INSERT INTO insumos (descricao, qtd_estoque, qtd_minima, unidade) VALUES (?, ?, ?, ?)", (novo_nome, nova_qtd, nova_qtd_min, nova_un))
                                conn.commit()
                                st.success(f"Insumo **{novo_nome}** cadastrado!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Produto já existente.")

            with col_ins3:
                with st.expander("🗑️ Remover Insumo"):
                    cursor.execute("SELECT codigo, descricao FROM insumos")
                    insumos_para_remover = cursor.fetchall()
                    if insumos_para_remover:
                        dict_rem_ins = {desc: cod for cod, desc in insumos_para_remover}
                        item_rem = st.selectbox("Selecione para Remover:", list(dict_rem_ins.keys()))
                        
                        if st.button("❌ Confirmar Exclusão do Insumo", type="primary"):
                            cursor.execute("DELETE FROM insumos WHERE codigo = ?", (dict_rem_ins[item_rem],))
                            conn.commit()
                            st.warning(f"Insumo **{item_rem}** foi removido permanentemente!")
                            st.rerun()

            st.divider()

            # GESTÃO INTERATIVA DE EQUIPAMENTOS E MATERIAIS ESPORTIVOS
            st.subheader("⚽ Gestão Interativa de Equipamentos (Tecnológicos & Educação Física)")
            
            df_eq = pd.read_sql_query("SELECT id AS 'ID', nome AS 'Equipamento', categoria AS 'Categoria', qtd_total AS 'Quantidade Disponível' FROM equipamentos", conn)
            st.dataframe(df_eq, use_container_width=True)

            col_eq1, col_eq2, col_eq3 = st.columns(3)
            
            with col_eq1:
                with st.expander("➕ Repor / Comprar Equipamento"):
                    cursor.execute("SELECT id, nome FROM equipamentos")
                    eqs = cursor.fetchall()
                    if eqs:
                        dict_eqs = {nome: eq_id for eq_id, nome in eqs}
                        eq_sel = st.selectbox("Selecione o Item para Adicionar:", list(dict_eqs.keys()))
                        qtd_add_eq = st.number_input("Quantidade Adicionada:", min_value=1, value=1)
                        if st.button("Confirmar Reposição"):
                            cursor.execute("UPDATE equipamentos SET qtd_total = qtd_total + ? WHERE id = ?", (qtd_add_eq, dict_eqs[eq_sel]))
                            conn.commit()
                            st.success(f"Adicionadas {qtd_add_eq} unidade(s) a {eq_sel}!")
                            st.rerun()

            with col_eq2:
                with st.expander("🗑️ Dar Baixa (Danificado / Perdido)"):
                    cursor.execute("SELECT id, nome, qtd_total FROM equipamentos")
                    eqs_baixa = cursor.fetchall()
                    if eqs_baixa:
                        dict_eqs_baixa = {f"{nome} (Disp: {qtd})": (eq_id, qtd, nome) for eq_id, nome, qtd in eqs_baixa}
                        eq_sel_baixa = st.selectbox("Selecione o Item para Baixa:", list(dict_eqs_baixa.keys()))
                        eq_id, max_disp, nome_item = dict_eqs_baixa[eq_sel_baixa]
                        
                        qtd_sub_eq = st.number_input("Qtd Danificada/Perdida:", min_value=1, max_value=max(1, max_disp), value=1)
                        motivo_baixa = st.text_input("Motivo (Ex: Bola furou, Cone quebrou, etc.):")
                        
                        if st.button("Confirmar Baixa/Descarte"):
                            if max_disp < qtd_sub_eq:
                                st.error("❌ Não é possível retirar mais do que a quantidade disponível.")
                            else:
                                cursor.execute("UPDATE equipamentos SET qtd_total = MAX(0, qtd_total - ?) WHERE id = ?", (qtd_sub_eq, eq_id))
                                conn.commit()
                                st.warning(f"Baixa registrada: -{qtd_sub_eq} unidade(s) de {nome_item}. Motivo: {motivo_baixa}")
                                st.rerun()

            with col_eq3:
                with st.expander("🆕 Cadastrar Novo Equipamento"):
                    novo_eq_nome = st.text_input("Nome do Equipamento:")
                    novo_eq_cat = st.selectbox("Categoria:", ["Equipamento Tecnológico", "Equipamento de Educação Física"])
                    novo_eq_qtd = st.number_input("Quantidade Inicial:", min_value=1, value=5)
                    
                    if st.button("Cadastrar Equipamento"):
                        if novo_eq_nome:
                            try:
                                cursor.execute("INSERT INTO equipamentos (nome, categoria, qtd_total) VALUES (?, ?, ?)", (novo_eq_nome, novo_eq_cat, novo_eq_qtd))
                                conn.commit()
                                st.success(f"Equipamento **{novo_eq_nome}** cadastrado!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Equipamento já cadastrado.")

            conn.close()

# 4. EXECUÇÃO DO FLUXO
if not st.session_state.logado:
    tela_login()
else:
    sistema_principal()