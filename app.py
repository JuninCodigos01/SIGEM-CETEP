import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta, time

# CONFIGURAÇÃO DA PÁGINA (STREAMLIT)
st.set_page_config(
    page_title="SIGEM - Gestão Escolar & Mecanografia", 
    page_icon="🏫", 
    layout="wide"
)

# 1. GERENCIAMENTO DO BANCO DE DADOS (SQLite3)
def conectar_bd():
    conn = sqlite3.connect("escola.db", check_same_thread=False)
    return conn

def inicializar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Ativa o suporte a chaves estrangeiras no SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Tabela Curso
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Curso (
        id_curso INTEGER PRIMARY KEY AUTOINCREMENT,
        nome VARCHAR(100),
        descricao VARCHAR(100)
    );
    """)

    # 2. Tabela Turma
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Turma (
        id_turma INTEGER PRIMARY KEY AUTOINCREMENT,
        Curso_id_curso INT,
        nome VARCHAR(100),
        ano INT,
        turno VARCHAR(20),
        FOREIGN KEY (Curso_id_curso) REFERENCES Curso(id_curso)
    );
    """)

    # 3. Tabela Usuario (com campo senha opcional)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Usuario (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nome VARCHAR(30),
        email VARCHAR(100),
        telefone VARCHAR(20),
        tipo_usuario VARCHAR(30),
        senha VARCHAR(100)
    );
    """)

    # Garantir adição da coluna senha caso a tabela já existisse
    try:
        cursor.execute("ALTER TABLE Usuario ADD COLUMN senha VARCHAR(100);")
    except sqlite3.OperationalError:
        pass # Coluna já existe

    # 4. Tabela Arquivo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Arquivo (
        id_arquivo INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_arquivo VARCHAR(255),
        tipo_arquivo VARCHAR(50),
        local_arquivo BLOB,
        data_recebimento DATETIME
    );
    """)

    # 5. Tabela Solicitacao
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Solicitacao (
        id_solicitacao INTEGER PRIMARY KEY AUTOINCREMENT,
        Arquivo_id_arquivo INT,
        Usuario_id_usuario INT,
        tipo_origem VARCHAR(20),
        qtd INT,
        tipo_impressao VARCHAR(30),
        acabamento VARCHAR(100),
        observacao VARCHAR(255),
        data_solicitacao DATETIME,
        status_atual VARCHAR(30),
        FOREIGN KEY (Arquivo_id_arquivo) REFERENCES Arquivo(id_arquivo),
        FOREIGN KEY (Usuario_id_usuario) REFERENCES Usuario(id_usuario)
    );
    """)

    # 6. Tabela Disciplina
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Disciplina (
        id_disciplina INTEGER PRIMARY KEY AUTOINCREMENT,
        Curso_id_curso INT,
        Solicitacao_id_solicitacao INT,
        Solicitacao_Arquivo_id_arquivo INT,
        Solicitacao_Usuario_id_usuario INT,
        nome VARCHAR(100),
        FOREIGN KEY (Curso_id_curso) REFERENCES Curso(id_curso),
        FOREIGN KEY (Solicitacao_id_solicitacao) REFERENCES Solicitacao(id_solicitacao),
        FOREIGN KEY (Solicitacao_Arquivo_id_arquivo) REFERENCES Arquivo(id_arquivo),
        FOREIGN KEY (Solicitacao_Usuario_id_usuario) REFERENCES Usuario(id_usuario)
    );
    """)

    # 7. Tabela email
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email (
        id_email INTEGER PRIMARY KEY AUTOINCREMENT,
        Solicitacao_id_solicitacao INT,
        Solicitacao_Arquivo_id_arquivo INT,
        Solicitacao_Usuario_id_usuario INT,
        email_remetente VARCHAR(150),
        assunto VARCHAR(255),
        data_recebimento DATETIME,
        identificador_email VARCHAR(255),
        FOREIGN KEY (Solicitacao_id_solicitacao) REFERENCES Solicitacao(id_solicitacao),
        FOREIGN KEY (Solicitacao_Arquivo_id_arquivo) REFERENCES Arquivo(id_arquivo),
        FOREIGN KEY (Solicitacao_Usuario_id_usuario) REFERENCES Usuario(id_usuario)
    );
    """)

    # 8. Tabela Historico_Status
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Historico_Status (
        id_historico INTEGER PRIMARY KEY AUTOINCREMENT,
        Solicitacao_id_solicitacao INT,
        Solicitacao_Arquivo_id_arquivo INT,
        Solicitacao_Usuario_id_usuario INT,
        FOREIGN KEY (Solicitacao_id_solicitacao) REFERENCES Solicitacao(id_solicitacao),
        FOREIGN KEY (Solicitacao_Arquivo_id_arquivo) REFERENCES Arquivo(id_arquivo),
        FOREIGN KEY (Solicitacao_Usuario_id_usuario) REFERENCES Usuario(id_usuario)
    );
    """)

    # 9. Tabela Insumo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Insumo (
        id_insumo INTEGER PRIMARY KEY AUTOINCREMENT,
        nome VARCHAR(100),
        tipo VARCHAR(50),
        unidade_media VARCHAR(20),
        qtd_estoque DECIMAL(10,2),
        estoque_minimo DECIMAL(10,2)
    );
    """)

    # 10. Tabela Mov_Estoque
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Mov_Estoque (
        id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
        Usuario_id_usuario INT,
        Insumo_id_insumo INT,
        tipo_movimentacao VARCHAR(10),
        qtd DECIMAL(10,2),
        data_movimentacao DATETIME,
        observacao VARCHAR(255),
        FOREIGN KEY (Usuario_id_usuario) REFERENCES Usuario(id_usuario),
        FOREIGN KEY (Insumo_id_insumo) REFERENCES Insumo(id_insumo)
    );
    """)

    # POPULA DADOS INICIAIS DE FORMA SEGURA
    cursor.execute("SELECT COUNT(*) FROM Usuario")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO Usuario (nome, email, telefone, tipo_usuario, senha) VALUES (?, ?, ?, ?, ?)",
            ("DBA", "", "", "Administrador", "2525")
        )

    cursor.execute("SELECT COUNT(*) FROM Insumo")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO Insumo (nome, tipo, unidade_media, qtd_estoque, estoque_minimo) VALUES (?,?,?,?,?)",
            [
            ]
        )

    conn.commit()
    conn.close()

inicializar_bd()

# Inicialização do Session State
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_id = None
    st.session_state.usuario_atual = None
    st.session_state.nivel_acesso = None
    st.session_state.nome_usuario = None
    st.session_state.email_usuario = None

# 2. FUNÇÕES AUXILIARES
def obter_estoque_equipamentos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, qtd_estoque FROM Insumo WHERE tipo LIKE 'Equipamento%'")
    dados = cursor.fetchall()
    conn.close()
    return {row[0]: int(row[1]) for row in dados}

def verificar_conflito_reserva(recurso, data_str, h_inicio, h_fim):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT observacao, status_atual FROM Solicitacao 
        WHERE acabamento = ? AND data_solicitacao = ? AND status_atual IN ('Aprovada', 'Pendente')
    """, (recurso, data_str))
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
    cursor.execute("""
        SELECT qtd, observacao FROM Solicitacao 
        WHERE acabamento = ? AND data_solicitacao = ? AND status_atual IN ('Aprovada', 'Pendente')
    """, (recurso, data_str))
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

# 3. TELA DE LOGIN
def tela_login():
    st.title("🏫 Sistema Integrado de Gestão e Mecanografia (SIGEM)")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔑 Acesso ao Sistema")
        usuario_input = st.text_input("Nome do Usuário:")
        senha_input = st.text_input("Senha:", type="password")
        
        if st.button("Entrar", use_container_width=True):
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario, tipo_usuario, nome, email, senha FROM Usuario WHERE LOWER(nome) = LOWER(?)", (usuario_input.strip(),))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                id_u, tipo_u, nome_u, email_u, senha_u = user
                if senha_u and senha_u != senha_input:
                    st.error("Senha incorreta.")
                else:
                    st.session_state.logado = True
                    st.session_state.usuario_id = id_u
                    st.session_state.usuario_atual = email_u
                    st.session_state.nivel_acesso = tipo_u
                    st.session_state.nome_usuario = nome_u
                    st.session_state.email_usuario = email_u
                    st.success(f"Bem-vindo(a), {st.session_state.nome_usuario}!")
                    st.rerun()
            else:
                st.error("Usuário não encontrado.")

# 4. SISTEMA PRINCIPAL
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

    # ABA 1: IMPRESSÃO (COM UPLOAD DE ARQUIVOS)
    with guias[0]:
        st.header("🖨️ Solicitação de Impressão (Mecanografia)")
        
        data_minima = date.today() + timedelta(days=2)
        st.info("ℹ️ **Anexe o arquivo que deseja imprimir no campo abaixo e preencha as especificações de impressão.**")
        
        with st.form("form_impressao", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Solicitante Cadastrado:", value=st.session_state.nome_usuario, disabled=True)
                email_prof = st.text_input("E-mail de Contato:", value=st.session_state.email_usuario)
                
                # NOVO: UPLOAD DE QUALQUER TIPO DE ARQUIVO
                arquivo_enviado = st.file_uploader(
                    "Upload do Arquivo para Impressão:", 
                    type=None,  # Permite todos os formatos de arquivo (pdf, docx, xlsx, png, jpg, etc.)
                    help="Suporta PDF, Word, Excel, imagens, textos, etc."
                )
                
            with col2:
                data_necessidade = st.date_input("Para quando precisa do material pronto?", min_value=data_minima, value=data_minima)
                qtd_copias = st.number_input("Quantidade de Cópias:", min_value=1, value=30)
                formato_cor = st.radio("Impressão:", ["Preto e Branco", "Colorida"])

            obs_impressao = st.text_area("Observações para a Mecanografia:", placeholder="Ex: Grampear em duplas, imprimir frente e verso.")
            
            btn_enviar_impressao = st.form_submit_button("Enviar Solicitação de Impressão")

            if btn_enviar_impressao:
                if arquivo_enviado is None:
                    st.error("❌ Por favor, selecione e faça o upload de um arquivo antes de enviar.")
                else:
                    # Ler o conteúdo em bytes para armazenar no BD
                    conteudo_bytes = arquivo_enviado.read()
                    nome_arq = arquivo_enviado.name
                    extensao = nome_arq.split('.')[-1].lower() if '.' in nome_arq else "desconhecido"

                    conn = conectar_bd()
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO Arquivo (nome_arquivo, tipo_arquivo, local_arquivo, data_recebimento)
                        VALUES (?, ?, ?, ?)
                    """, (nome_arq, extensao, conteudo_bytes, datetime.now()))
                    id_arq = cursor.lastrowid

                    cursor.execute("""
                        INSERT INTO Solicitacao (
                            Arquivo_id_arquivo, Usuario_id_usuario, tipo_origem, 
                            qtd, tipo_impressao, acabamento, observacao, data_solicitacao, status_atual
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        id_arq, st.session_state.usuario_id, "Impressão",
                        qtd_copias, formato_cor, "Mecanografia", obs_impressao if obs_impressao else "Sem observações",
                        data_necessidade.strftime("%Y-%m-%d"), "Pendente"
                    ))
                    
                    id_sol = cursor.lastrowid
                    cursor.execute("""
                        INSERT INTO Historico_Status (Solicitacao_id_solicitacao, Solicitacao_Arquivo_id_arquivo, Solicitacao_Usuario_id_usuario) 
                        VALUES (?, ?, ?)
                    """, (id_sol, id_arq, st.session_state.usuario_id))
                    
                    conn.commit()
                    conn.close()

                    st.success(f"✅ Solicitação do arquivo **{nome_arq}** enviada com sucesso!")

    # ABA 2: RESERVAR RECURSOS (COM IDENTIFICAÇÃO DO PROFESSOR)
    with guias[1]:
        st.header("Realizar Reserva de Recursos")
        
        # EXIBIÇÃO DA IDENTIFICAÇÃO DO PROFESSOR RESPONSÁVEL
        st.info(f"👤 **Professor/Responsável pela Reserva:** {st.session_state.nome_usuario} ({st.session_state.email_usuario})")

        tipo_reserva = st.selectbox(
            "O que você deseja reservar?",
            ["Laboratório", "Equipamento Tecnológico", "Equipamento de Educação Física"]
        )

        with st.form("form_reserva", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # IDENTIFICAÇÃO DO SOLICITANTE NO PRÓPRIO FORMULÁRIO
                st.text_input("Professor Solicitante:", value=st.session_state.nome_usuario, disabled=True)
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
                    cursor.execute("SELECT nome FROM Insumo WHERE tipo = ?", (tipo_reserva,))
                    opcoes = [r[0] for r in cursor.fetchall()]
                    conn.close()

                    if not opcoes:
                        st.warning("Nenhum equipamento dessa categoria cadastrado no sistema.")
                    else:
                        recurso_selecionado = st.selectbox("Escolha o Item:", opcoes)
                        
                        estoque_dict = obter_estoque_equipamentos()
                        max_total = estoque_dict.get(recurso_selecionado, 0)
                        
                        ja_reservados = obter_quantidade_reservada(recurso_selecionado, data_reserva.strftime("%Y-%m-%d"), hora_inicio, hora_fim)
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
                    data_formatted = data_reserva.strftime("%Y-%m-%d")
                    horario_str = f"{hora_inicio.strftime('%H:%M')} às {hora_fim.strftime('%H:%M')}"
                    em_uso, hor_conf, status_conf = verificar_conflito_reserva(recurso_selecionado, data_formatted, hora_inicio, hora_fim)
                    
                    if tipo_reserva == "Laboratório" and em_uso:
                        st.error(f"❌ O espaço **{recurso_selecionado}** já possui reserva no horário `{hor_conf}` (Status: {status_conf}). Apenas 1 usuário por horário.")
                    else:
                        conn = conectar_bd()
                        cursor = conn.cursor()
                        
                        # Adiciona o nome do professor no campo observação para facilitar rastreamento rápido
                        obs_com_prof = f"Professor: {st.session_state.nome_usuario} | Horário: {horario_str} | Obs: {observacao if observacao else 'Sem obs'}"
                        
                        cursor.execute("""
                            INSERT INTO Solicitacao (
                                Usuario_id_usuario, tipo_origem, qtd, tipo_impressao, 
                                acabamento, observacao, data_solicitacao, status_atual
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            st.session_state.usuario_id, tipo_reserva, qtd_reservada,
                            "Reserva de Recurso", recurso_selecionado, obs_com_prof,
                            data_formatted, "Pendente"
                        ))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Reserva de **{recurso_selecionado}** realizada em nome do prof. **{st.session_state.nome_usuario}**!")

    # ABA 3: HISTÓRICO DE SOLICITAÇÕES
    with guias[2]:
        st.header("📋 Histórico de Pedidos e Reservas")
        conn = conectar_bd()
        
        st.subheader("🖨️ Solicitações de Impressão Enviadas")
        if st.session_state.nivel_acesso == "Professor":
            query_imp = """
                SELECT S.id_solicitacao AS 'ID', A.nome_arquivo AS 'Arquivo', S.qtd AS 'Cópias', 
                       S.tipo_impressao AS 'Tipo', S.data_solicitacao AS 'Data Necessidade', S.status_atual AS 'Status'
                FROM Solicitacao S
                LEFT JOIN Arquivo A ON S.Arquivo_id_arquivo = A.id_arquivo
                WHERE S.Usuario_id_usuario = ? AND S.tipo_origem = 'Impressão'
            """
            df_imp = pd.read_sql_query(query_imp, conn, params=(st.session_state.usuario_id,))
        else:
            query_imp = """
                SELECT S.id_solicitacao AS 'ID', U.nome AS 'Professor', A.nome_arquivo AS 'Arquivo', 
                       S.qtd AS 'Cópias', S.tipo_impressao AS 'Tipo', S.data_solicitacao AS 'Data', S.status_atual AS 'Status'
                FROM Solicitacao S
                LEFT JOIN Arquivo A ON S.Arquivo_id_arquivo = A.id_arquivo
                LEFT JOIN Usuario U ON S.Usuario_id_usuario = U.id_usuario
                WHERE S.tipo_origem = 'Impressão'
            """
            df_imp = pd.read_sql_query(query_imp, conn)
            
        if not df_imp.empty:
            st.dataframe(df_imp, use_container_width=True)
        else:
            st.info("Nenhuma solicitação de impressão encontrada.")

        st.divider()

        st.subheader("📅 Reservas de Recursos (Laboratórios/Materiais)")
        if st.session_state.nivel_acesso == "Professor":
            query_res = """
                SELECT id_solicitacao AS 'ID', acabamento AS 'Recurso/Espaço', qtd AS 'Qtd', 
                       data_solicitacao AS 'Data Reserva', observacao AS 'Detalhes/Professor', status_atual AS 'Status'
                FROM Solicitacao WHERE Usuario_id_usuario = ? AND tipo_origem != 'Impressão'
            """
            df_res = pd.read_sql_query(query_res, conn, params=(st.session_state.usuario_id,))
        else:
            query_res = """
                SELECT S.id_solicitacao AS 'ID', U.nome AS 'Professor', S.acabamento AS 'Recurso/Espaço', 
                       S.qtd AS 'Qtd', S.data_solicitacao AS 'Data Reserva', S.observacao AS 'Detalhes', S.status_atual AS 'Status'
                FROM Solicitacao S
                LEFT JOIN Usuario U ON S.Usuario_id_usuario = U.id_usuario
                WHERE S.tipo_origem != 'Impressão'
            """
            df_res = pd.read_sql_query(query_res, conn)

        if not df_res.empty:
            st.dataframe(df_res, use_container_width=True)
        else:
            st.info("Nenhuma reserva encontrada.")
        conn.close()

    # ABA 4: GESTÃO
    if st.session_state.nivel_acesso in ["Administrador", "Coordenação"]:
        with guias[3]:
            st.header("⚙️ Controle de Mecanografia e Gestão de Pedidos")
            conn = conectar_bd()
            cursor = conn.cursor()
            
            # GESTÃO DE USUÁRIOS
            st.subheader("👥 Gestão de Usuários e Professores")
            df_usuarios = pd.read_sql_query("SELECT id_usuario AS 'ID', nome AS 'Nome Completo', email AS 'E-mail', telefone AS 'Telefone', tipo_usuario AS 'Nível de Acesso' FROM Usuario", conn)
            st.dataframe(df_usuarios, use_container_width=True)

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                with st.expander("➕ Adicionar Novo Usuário"):
                    with st.form("form_novo_usuario", clear_on_submit=True):
                        nov_nome = st.text_input("Nome Completo:")
                        nov_email = st.text_input("E-mail:")
                        nov_tel = st.text_input("Telefone:")
                        nov_nivel = st.selectbox("Nível de Acesso:", ["Professor", "Coordenação", "Administrador"])
                        nov_senha = st.text_input("Senha (Opcional):", type="password")
                        
                        if st.form_submit_button("Cadastrar Usuário"):
                            if not nov_nome:
                                st.error("❌ Preencha o nome do usuário.")
                            else:
                                cursor.execute(
                                    "INSERT INTO Usuario (nome, email, telefone, tipo_usuario, senha) VALUES (?, ?, ?, ?, ?)", 
                                    (nov_nome, nov_email, nov_tel, nov_nivel, nov_senha if nov_senha else None)
                                )
                                conn.commit()
                                st.success(f"✅ Usuário **{nov_nome}** ({nov_nivel}) cadastrado!")
                                st.rerun()

            with col_u2:
                with st.expander("🗑️ Remover Usuário Cadastrado"):
                    cursor.execute("SELECT id_usuario, nome, email FROM Usuario")
                    todos_usuarios = cursor.fetchall()
                    dict_usuarios = {f"{nome} ({email})": id_u for id_u, nome, email in todos_usuarios}
                    
                    if dict_usuarios:
                        user_sel = st.selectbox("Selecione o Usuário para Excluir:", list(dict_usuarios.keys()))
                        id_excluir = dict_usuarios[user_sel]
                        
                        if st.button("❌ Confirmar Exclusão do Usuário", type="primary"):
                            if id_excluir == st.session_state.usuario_id:
                                st.error("❌ Você não pode excluir o seu próprio usuário enquanto estiver conectado!")
                            else:
                                cursor.execute("DELETE FROM Usuario WHERE id_usuario = ?", (id_excluir,))
                                conn.commit()
                                st.warning("Usuário foi removido do sistema com sucesso.")
                                st.rerun()

            st.divider()

            # ALERTAS DE INSUMOS
            cursor.execute("SELECT nome, qtd_estoque, estoque_minimo, unidade_media FROM Insumo WHERE qtd_estoque <= estoque_minimo")
            for item in cursor.fetchall():
                st.warning(f"⚠️ **Insumo Crítico:** {item[0]} | Atual: {item[1]} {item[3]} (Mínimo: {item[2]} {item[3]})")

            # FILA DE IMPRESSÃO (COM BOTÃO DE DOWNLOAD DO ARQUIVO)
            st.subheader("🖨️ Fila de Impressão Pendente")
            cursor.execute("""
                SELECT S.id_solicitacao, U.nome, S.qtd, S.tipo_impressao, S.data_solicitacao, S.observacao, A.nome_arquivo, A.local_arquivo
                FROM Solicitacao S
                LEFT JOIN Usuario U ON S.Usuario_id_usuario = U.id_usuario
                LEFT JOIN Arquivo A ON S.Arquivo_id_arquivo = A.id_arquivo
                WHERE S.tipo_origem = 'Impressão' AND S.status_atual = 'Pendente'
            """)
            impressoes_pendentes = cursor.fetchall()
            
            if impressoes_pendentes:
                for item in impressoes_pendentes:
                    imp_id, prof_nome, copias, cor, dt_nec, obs, nome_arq, dados_blob = item
                    with st.expander(f"Impressão #{imp_id} - {prof_nome} - Qtd: {copias} ({cor})"):
                        st.write(f"**Arquivo:** {nome_arq}")
                        st.write(f"**Para:** {dt_nec} | **Obs:** {obs}")
                        
                        if dados_blob:
                            st.download_button(
                                label=f"📥 Baixar Arquivo ({nome_arq})",
                                data=dados_blob,
                                file_name=nome_arq,
                                key=f"dl_imp_{imp_id}"
                            )
                        
                        col1, col2 = st.columns(2)
                        if col1.button("✅ Concluir e Dar Baixa", key=f"ap_imp_{imp_id}"):
                            cursor.execute("UPDATE Solicitacao SET status_atual = 'Aprovada / Concluída' WHERE id_solicitacao = ?", (imp_id,))
                            cursor.execute("UPDATE Insumo SET qtd_estoque = MAX(0, qtd_estoque - ?) WHERE nome LIKE '%Papel A4%'", (copias,))
                            conn.commit()
                            st.success("Aprovado e concluído!")
                            st.rerun()
                                
                        if col2.button("❌ Recusar", key=f"rec_imp_{imp_id}"):
                            cursor.execute("UPDATE Solicitacao SET status_atual = 'Recusada' WHERE id_solicitacao = ?", (imp_id,))
                            conn.commit()
                            st.rerun()
            else:
                st.info("Nenhuma solicitação de impressão pendente.")

            st.divider()

            # FILA DE RESERVAS
            st.subheader("📅 Fila de Reservas Pendentes")
            cursor.execute("""
                SELECT S.id_solicitacao, U.nome, S.acabamento, S.qtd, S.data_solicitacao, S.observacao 
                FROM Solicitacao S
                LEFT JOIN Usuario U ON S.Usuario_id_usuario = U.id_usuario
                WHERE S.tipo_origem != 'Impressão' AND S.status_atual = 'Pendente'
            """)
            reservas_pendentes = cursor.fetchall()
            
            if reservas_pendentes:
                for item in reservas_pendentes:
                    res_id, prof_nome, recurso, qtd, dt, hr_obs = item
                    with st.expander(f"Reserva #{res_id} - Professor: {prof_nome} - Recurso: {recurso}"):
                        st.write(f"**Data:** {dt} | **Detalhes:** {hr_obs} | **Qtd:** {qtd}")
                        col_ap, col_rec = st.columns(2)
                        
                        if col_ap.button("✅ Aprovar Reserva", key=f"ap_res_{res_id}"):
                            cursor.execute("UPDATE Solicitacao SET status_atual = 'Aprovada' WHERE id_solicitacao = ?", (res_id,))
                            conn.commit()
                            st.success("Reserva aprovada!")
                            st.rerun()
                            
                        if col_rec.button("❌ Recusar Reserva", key=f"rec_res_{res_id}"):
                            cursor.execute("UPDATE Solicitacao SET status_atual = 'Recusada' WHERE id_solicitacao = ?", (res_id,))
                            conn.commit()
                            st.rerun()
            else:
                st.info("Nenhuma reserva pendente.")

            st.divider()

            # RECURSOS EM USO
            st.subheader("🔄 Recursos/Laboratórios Atualmente em Uso (Aprovados)")
            cursor.execute("""
                SELECT S.id_solicitacao, U.nome, S.acabamento, S.qtd, S.data_solicitacao, S.observacao 
                FROM Solicitacao S
                LEFT JOIN Usuario U ON S.Usuario_id_usuario = U.id_usuario
                WHERE S.status_atual = 'Aprovada' AND S.tipo_origem != 'Impressão'
            """)
            reservas_em_uso = cursor.fetchall()

            if reservas_em_uso:
                for item in reservas_em_uso:
                    res_id, prof_nome, recurso, qtd, dt, hr_obs = item
                    with st.expander(f"🔴 Em Uso #{res_id} - Prof. {prof_nome} ({recurso})"):
                        st.write(f"**Data:** {dt} | **Horário/Obs:** {hr_obs} | **Quantidade:** {qtd}")
                        if st.button("📥 Receber Devolta / Finalizar Uso", key=f"baixa_res_{res_id}"):
                            cursor.execute("UPDATE Solicitacao SET status_atual = 'Devolvido / Finalizado' WHERE id_solicitacao = ?", (res_id,))
                            conn.commit()
                            st.success(f"Uso de **{recurso}** finalizado com sucesso!")
                            st.rerun()
            else:
                st.info("Nenhum recurso ou laboratório está atualmente marcado como 'Aprovado/Em Uso'.")

            st.divider()

            # GESTÃO DE INSUMOS E EQUIPAMENTOS
            st.subheader("📦 Estoque de Insumos e Equipamentos (`Insumo`)")
            df_insumos = pd.read_sql_query("SELECT id_insumo AS 'Código', nome AS 'Item', tipo AS 'Tipo/Categoria', qtd_estoque AS 'Qtd Atual', estoque_minimo AS 'Qtd Mínima', unidade_media AS 'Unidade' FROM Insumo", conn)
            st.dataframe(df_insumos, use_container_width=True)

            col_ins1, col_ins2, col_ins3 = st.columns(3)
            
            with col_ins1:
                with st.expander("➕ Adicionar/Repor Estoque"):
                    cursor.execute("SELECT id_insumo, nome FROM Insumo")
                    lista_ins = cursor.fetchall()
                    if lista_ins:
                        opcoes_ins = {nome: id_i for id_i, nome in lista_ins}
                        item_sel = st.selectbox("Item/Equipamento:", list(opcoes_ins.keys()), key="add_ins_sel")
                        qtd_add = st.number_input("Qtd Recebida:", min_value=1.0, value=1.0, key="add_ins_qtd")
                        
                        if st.button("Confirmar Entrada"):
                            id_sel = opcoes_ins[item_sel]
                            cursor.execute("UPDATE Insumo SET qtd_estoque = qtd_estoque + ? WHERE id_insumo = ?", (qtd_add, id_sel))
                            cursor.execute("INSERT INTO Mov_Estoque (Usuario_id_usuario, Insumo_id_insumo, tipo_movimentacao, qtd, data_movimentacao, observacao) VALUES (?, ?, ?, ?, ?, ?)",
                                           (st.session_state.usuario_id, id_sel, "ENTRADA", qtd_add, datetime.now(), "Entrada de material"))
                            conn.commit()
                            st.success(f"Adicionadas {qtd_add} unidades de {item_sel}!")
                            st.rerun()

                with st.expander("➖ Retirar / Dar Baixa (Danificado/Perdido)"):
                    cursor.execute("SELECT id_insumo, nome, qtd_estoque FROM Insumo")
                    lista_ins_sub = cursor.fetchall()
                    if lista_ins_sub:
                        dict_sub_ins = {f"{nome} (Atual: {int(qtd)})": (id_i, qtd, nome) for id_i, nome, qtd in lista_ins_sub}
                        item_sub_sel = st.selectbox("Selecione o Item:", list(dict_sub_ins.keys()), key="sub_ins_sel")
                        id_ins, max_qtd_ins, desc_ins = dict_sub_ins[item_sub_sel]
                        
                        qtd_sub = st.number_input("Quantidade a Retirar:", min_value=1.0, max_value=max(1.0, float(max_qtd_ins)), value=1.0, key="sub_ins_qtd")
                        motivo_baixa = st.text_input("Motivo da Baixa:")
                        
                        if st.button("Confirmar Retirada"):
                            cursor.execute("UPDATE Insumo SET qtd_estoque = MAX(0, qtd_estoque - ?) WHERE id_insumo = ?", (qtd_sub, id_ins))
                            cursor.execute("INSERT INTO Mov_Estoque (Usuario_id_usuario, Insumo_id_insumo, tipo_movimentacao, qtd, data_movimentacao, observacao) VALUES (?, ?, ?, ?, ?, ?)",
                                           (st.session_state.usuario_id, id_ins, "SAIDA", qtd_sub, datetime.now(), motivo_baixa if motivo_baixa else "Baixa efetuada"))
                            conn.commit()
                            st.warning(f"Retiradas {qtd_sub} unidade(s) de {desc_ins}!")
                            st.rerun()

            with col_ins2:
                with st.expander("🆕 Cadastrar Novo Item/Equipamento"):
                    novo_nome = st.text_input("Nome do Item:")
                    novo_tipo = st.selectbox("Categoria:", ["Papelaria", "Suprimento", "Equipamento Tecnológico", "Equipamento de Educação Física"])
                    nova_qtd = st.number_input("Quantidade Inicial:", min_value=0.0, value=10.0)
                    nova_qtd_min = st.number_input("Mínimo de Alerta:", min_value=1.0, value=2.0)
                    nova_un = st.text_input("Unidade:", value="Unidades")
                    
                    if st.button("Cadastrar Item"):
                        if novo_nome:
                            cursor.execute("INSERT INTO Insumo (nome, tipo, unidade_media, qtd_estoque, estoque_minimo) VALUES (?, ?, ?, ?, ?)", 
                                           (novo_nome, novo_tipo, nova_un, nova_qtd, nova_qtd_min))
                            conn.commit()
                            st.success(f"Item **{novo_nome}** cadastrado!")
                            st.rerun()

            with col_ins3:
                with st.expander("🗑️ Excluir Item Permanentemente"):
                    cursor.execute("SELECT id_insumo, nome FROM Insumo")
                    insumos_para_remover = cursor.fetchall()
                    if insumos_para_remover:
                        dict_rem_ins = {nome: id_i for id_i, nome in insumos_para_remover}
                        item_rem = st.selectbox("Selecione para Remover:", list(dict_rem_ins.keys()), key="del_ins_sel")
                        
                        if st.button("❌ Confirmar Exclusão Definitiva", type="primary"):
                            cursor.execute("DELETE FROM Insumo WHERE id_insumo = ?", (dict_rem_ins[item_rem],))
                            conn.commit()
                            st.warning(f"Item **{item_rem}** removido permanentemente!")
                            st.rerun()

            conn.close()

# 5. PONTO DE ENTRADA
if not st.session_state.logado:
    tela_login()
else:
    sistema_principal()