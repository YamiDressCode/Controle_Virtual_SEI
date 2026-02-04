#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =======================
# 🔧 CONFIGURAÇÕES INICIAIS
# =======================

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# =======================
# 🔐 CONFIGURAÇÕES FIXAS
# =======================

USUARIO_SEI = "xxxxxx"  # ← ALTERE AQUI SEU USUÁRIO
SENHA_SEI = "xxxxxxx"     # ← ALTERE AQUI SUA SENHA  
NUMERO_MODELO = "17775984"       # Número do modelo fixo

# Configurar logging SEM EMOJIS para Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sei_criar_relatorios.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SEIRelatorioCreator')

# =======================
# 🚀 CLASSE SEI RELATORIO CREATOR
# =======================

class SEIRelatorioCreator:
    def __init__(self):
        self.config = {}
        self.driver = None
        self.wait = None
        logger.info("SEI Relatorio Creator inicializado")

    def configurar_chrome(self):
        """Configura o Chrome para automação"""
        chrome_options = Options()
        
        # Configurações para automação robusta
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("Navegador Chrome configurado")

    def coletar_dados_usuario(self):
        """Coleta apenas o número do processo - credenciais são fixas"""
        print("\n" + "="*70)
        print("SEI - CRIAÇÃO AUTOMÁTICA DE RELATÓRIOS")
        print("="*70)
        
        dados = {}
        
        # Credenciais fixas
        dados['usuario'] = USUARIO_SEI
        dados['senha'] = SENHA_SEI
        
        # Apenas solicita o número do processo
        print("\nCONFIGURAÇÃO DO PROCESSO:")
        dados['numero_processo'] = input("Digite o número do Processo: ").strip()
        
        if not dados['numero_processo']:
            print("Número do processo não pode estar vazio!")
            return None
        
        # Confirmar dados automaticamente
        print("\n" + "="*50)
        print("RESUMO DA CONFIGURACAO:")
        print(f"   Processo: {dados['numero_processo']}")
        print(f"   Usuário: {dados['usuario']}")
        print(f"   Modelo: {NUMERO_MODELO}")
        print("="*50)
        
        print("\nIniciando automação...")
        time.sleep(2)
            
        return dados

    def fazer_login_sei(self, usuario, senha):
        """Faz login no SEI - Multiplos seletores como fallback"""
        try:
            logger.info("Iniciando login no SEI...")
            print("Conectando ao SEI...")
            
            # Acessa página de login
            self.driver.get("https://sei.cidadania.gov.br/sip/login.php?sigla_orgao_sistema=MC&sigla_sistema=SEI")
            time.sleep(3)
            
            # Aguarda página carregar completamente
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Multiplos seletores para usuario
            seletores_usuario = [
                "//input[@id='txtUsuario']",
                "//input[@name='txtUsuario']",
                "//input[@type='text' and contains(@class, 'infraText')]",
                "//input[contains(@placeholder, 'usuario') or contains(@placeholder, 'login')]"
            ]
            
            campo_usuario = None
            seletor_usado = None
            
            for i, seletor in enumerate(seletores_usuario, 1):
                try:
                    logger.info(f"Tentando seletor {i} para usuario: {seletor}")
                    campo_usuario = self.wait.until(EC.presence_of_element_located((By.XPATH, seletor)))
                    seletor_usado = seletor
                    break
                except Exception as e:
                    logger.debug(f"Seletor {i} falhou: {e}")
                    continue
            
            if not campo_usuario:
                logger.error("Nenhum seletor de usuario funcionou")
                print("Nao foi possível encontrar o campo de usuario")
                return False
                
            logger.info(f"Campo usuario encontrado com: {seletor_usado}")
            
            # Preenche usuario
            campo_usuario.clear()
            campo_usuario.send_keys(usuario)
            logger.info("Usuario preenchido")
            
            # Multiplos seletores para senha
            seletores_senha = [
                "//input[@id='pwdSenha']",
                "//input[@name='pwdSenha']", 
                "//input[@type='password']",
                "//input[contains(@class, 'infraText') and @type='password']"
            ]
            
            campo_senha = None
            for seletor in seletores_senha:
                try:
                    campo_senha = self.driver.find_element(By.XPATH, seletor)
                    break
                except:
                    continue
            
            if not campo_senha:
                logger.error("Campo de senha nao encontrado")
                print("Nao foi possível encontrar o campo de senha")
                return False
                
            # Preenche senha
            campo_senha.clear()
            campo_senha.send_keys(senha)
            logger.info("Senha preenchida")
            
            # Encontrar botão de login
            seletores_botao_login = [
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//input[contains(@value, 'Login') or contains(@value, 'Entrar')]",
                "//button[contains(text(), 'Login') or contains(text(), 'Entrar')]"
            ]
            
            botao_login = None
            for seletor in seletores_botao_login:
                try:
                    botao_login = self.driver.find_element(By.XPATH, seletor)
                    break
                except:
                    continue
            
            if not botao_login:
                logger.warning("Botao de login nao encontrado, submetendo pelo campo senha")
                campo_senha.submit()
            else:
                botao_login.click()
                logger.info("Botao de login clicado")
            
            # Aguarda login processar
            logger.info("Aguardando processamento do login...")
            time.sleep(5)
            
            # Verifica se login foi bem-sucedido
            if self._verificar_login_sucesso():
                logger.info("Login realizado com sucesso")
                print("Login realizado com sucesso!")
                return True
            else:
                logger.error("Login falhou - ainda na pagina de login")
                print("Login falhou! Verifique suas credenciais.")
                return False
                
        except Exception as e:
            logger.error(f"Erro critico no login: {e}")
            print(f"Erro durante o login: {e}")
            return False

    def _verificar_login_sucesso(self):
        """Verifica se o login foi bem-sucedido"""
        try:
            # Verifica pela URL ou elementos da página principal
            current_url = self.driver.current_url.lower()
            
            # URLs que indicam sucesso no login
            urls_sucesso = [
                "controlador.php?acao=procedimento_controlar",
                "principal.php",
                "inicio.php"
            ]
            
            # Verifica por URLs de sucesso
            for url_sucesso in urls_sucesso:
                if url_sucesso in current_url:
                    return True
            
            # Fallback: verifica por elementos da página principal
            elementos_sucesso = [
                "//*[contains(text(), 'Processos')]",
                "//*[contains(text(), 'Bem-vindo')]",
                "//*[@id='divArvore']",
                "//*[contains(@id, 'ifrArvore')]",
                "//*[contains(@id, 'ifrVisualizacao')]"
            ]
            
            for elemento in elementos_sucesso:
                try:
                    if self.driver.find_element(By.XPATH, elemento):
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar login: {e}")
            return False

    def buscar_processo(self, numero_processo):
        """Busca processo pela barra de pesquisa rapida"""
        try:
            logger.info(f"Buscando processo: {numero_processo}")
            print(f"Localizando processo {numero_processo}...")
            
            # Multiplos seletores para barra de pesquisa
            seletores_pesquisa = [
                "//input[@id='txtPesquisaRapida']",
                "//input[@name='txtPesquisaRapida']",
                "//input[contains(@placeholder, 'pesquisa') or contains(@placeholder, 'pesquisar')]",
                "//input[@type='text' and contains(@style, 'width:13em')]"
            ]
            
            campo_pesquisa = None
            for seletor in seletores_pesquisa:
                try:
                    campo_pesquisa = self.wait.until(EC.presence_of_element_located((By.XPATH, seletor)))
                    break
                except:
                    continue
            
            if not campo_pesquisa:
                logger.error("Barra de pesquisa nao encontrada")
                print("Nao foi possível encontrar a barra de pesquisa")
                return False
                
            # Limpa e preenche pesquisa
            campo_pesquisa.clear()
            campo_pesquisa.send_keys(numero_processo)
            logger.info("Numero do processo preenchido")
            
            # Submete pesquisa
            campo_pesquisa.submit()
            logger.info("Pesquisa submetida")
            
            # Aguarda resultado
            print("Aguardando carregamento do processo...")
            time.sleep(8)
            
            # VERIFICAÇÃO MELHORADA - Procura por iframes que indicam sucesso
            if self._verificar_processo_aberto():
                logger.info("Processo encontrado e aberto")
                print("Processo encontrado!")
                return True
            else:
                logger.error("Processo nao encontrado")
                print("Processo nao encontrado! Verifique o numero.")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao buscar processo: {e}")
            print(f"Erro ao buscar processo: {e}")
            return False

    def _verificar_processo_aberto(self):
        """Verifica se o processo foi aberto com sucesso"""
        try:
            # Verifica se os iframes principais do SEI estão presentes
            elementos_processo_aberto = [
                "//iframe[contains(@id, 'ifrArvore')]",
                "//iframe[contains(@id, 'ifrVisualizacao')]",
                "//div[@id='divArvore']",
                "//*[contains(text(), 'Arvore do Processo')]",
                "//*[contains(@class, 'infraBarraSistema')]"
            ]
            
            for elemento in elementos_processo_aberto:
                try:
                    if self.driver.find_element(By.XPATH, elemento):
                        logger.info(f"Elemento de processo encontrado: {elemento}")
                        return True
                except:
                    continue
            
            # Verifica se está na URL de visualização de processo
            current_url = self.driver.current_url.lower()
            if "procedimento_visualizar" in current_url or "arvore_visualizar" in current_url:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar processo aberto: {e}")
            return False

    def _mudar_para_iframe_visualizacao(self):
        """Muda para o iframe de visualização onde está o formulário"""
        try:
            logger.info("Mudando para iframe de visualizacao...")
            
            # Tenta diferentes seletores de iframe
            seletores_iframe = [
                "//iframe[@id='ifrVisualizacao']",
                "//iframe[contains(@name, 'ifrVisualizacao')]",
                "//iframe[contains(@src, 'arvore_visualizar')]"
            ]
            
            iframe = None
            for seletor in seletores_iframe:
                try:
                    iframe = self.wait.until(EC.presence_of_element_located((By.XPATH, seletor)))
                    logger.info(f"Iframe encontrado com: {seletor}")
                    break
                except:
                    continue
            
            if not iframe:
                logger.error("Nenhum iframe de visualizacao encontrado")
                return False
            
            # Muda para o iframe
            self.driver.switch_to.frame(iframe)
            logger.info("Mudou para iframe de visualizacao")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao mudar para iframe: {e}")
            return False

    def _voltar_para_contexto_principal(self):
        """Volta para o contexto principal"""
        try:
            self.driver.switch_to.default_content()
            logger.info("Voltou para contexto principal")
            return True
        except Exception as e:
            logger.error(f"Erro ao voltar para contexto principal: {e}")
            return False
    
    def _verificar_pagina_gerar_documento(self):
        try:
            # 1. Muda para o iframe de visualização
            if not self._mudar_para_iframe_visualizacao():
                return False
            
            # Verifica se o formulário de cadastro está presente
            formulario = self.wait.until(EC.presence_of_element_located(
                (By.ID, "frmDocumentoCadastro")
            ))
            
            # Verifica se o botão Confirmar Dados está presente
            botao_confirmar = self.driver.find_element(By.ID, "btnSalvar")
            
            # Volta para contexto principal
            self._voltar_para_contexto_principal()
            
            logger.info("Página 'Gerar Documento' verificada com sucesso dentro do iframe")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar página de gerar documento: {e}")
            self._voltar_para_contexto_principal()
            return False

    def clicar_incluir_documento(self):
        """Clica no botão 'Incluir Documento' e mantém no iframe"""
        try:
            logger.info("Clicando em 'Incluir Documento'...")
            
            # 1. Muda para o iframe de visualização
            if not self._mudar_para_iframe_visualizacao():
                return False
            
            # 2. Procura e clica no botão
            botao_incluir = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@href, 'documento_escolher_tipo')]")
            ))
            botao_incluir.click()
            logger.info("'Incluir Documento' clicado")
            
            # 3. Mantém no iframe - NÃO volta para contexto principal
            logger.info("Aguardando carregamento da página de seleção de documento...")
            time.sleep(5)
            
            # 4. VERIFICA SE CARREGOU CORRETAMENTE DENTRO DO IFRAME
            if not self._verificar_pagina_selecao_documento():
                logger.error("Página de seleção de documento não carregou corretamente")
                self._voltar_para_contexto_principal()
                return False
                
            logger.info("Página de seleção de documento carregada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao clicar em 'Incluir Documento': {e}")
            self._voltar_para_contexto_principal()
            return False

    def _verificar_pagina_selecao_documento(self):
        """Verifica se a página de seleção carregou DENTRO do iframe"""
        try:
            # Verifica se o formulário está presente (dentro do iframe)
            formulario = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//form[@id='frmDocumentoEscolherTipo']")
            ))
            
            # Verifica se a tabela de séries está presente
            tabela_series = self.driver.find_element(By.XPATH, "//table[@id='tblSeries']")
            
            logger.info("Página de seleção de documento verificada com sucesso (dentro do iframe)")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar página de seleção: {e}")
            return False

    def clicar_documento_relatorio(self):
        """CLICA DIRETAMENTE no link Relatório - VERSÃO FINAL"""
        try:
            logger.info("Procurando link direto do Relatório...")
            
            # Estratégia 1: Procura pelo texto "Relatório" exato
            xpaths_relatorio = [
                "//a[@class='ancoraOpcao' and normalize-space(text())='Relatório']",
                "//a[contains(@href, 'id_serie=63') and @class='ancoraOpcao']",
                "//a[contains(@href, 'documento_gerar') and contains(text(), 'Relatório')]",
                "//table[@id='tblSeries']//a[normalize-space(text())='Relatório']"
            ]
            
            link_relatorio = None
            
            for xpath in xpaths_relatorio:
                try:
                    logger.info(f"Tentando XPath: {xpath}")
                    link_relatorio = self.driver.find_element(By.XPATH, xpath)
                    logger.info(f"Relatório encontrado com XPath: {xpath}")
                    break
                except Exception as e:
                    logger.debug(f"XPath falhou: {xpath} - {e}")
                    continue
            
            if not link_relatorio:
                logger.error("Relatório não encontrado")
                return False
            
            # CLICA NO RELATÓRIO
            logger.info("Clicando no Relatório...")
            
            # Rola até o elemento
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_relatorio)
            time.sleep(1)
            
            # Tenta clicar via JavaScript (mais confiável)
            try:
                self.driver.execute_script("arguments[0].click();", link_relatorio)
                logger.info("Clique via JavaScript executado com sucesso")
            except Exception as js_error:
                logger.warning(f"Clique JS falhou, tentando clique normal: {js_error}")
                try:
                    link_relatorio.click()
                    logger.info("Clique normal executado com sucesso")
                except Exception as click_error:
                    logger.error(f"Clique normal também falhou: {click_error}")
                    return False
            
            logger.info("Relatório selecionado com sucesso!")
            print("Relatório selecionado!")
            
            # VOLTA PARA O CONTEXTO PRINCIPAL (já estamos nele, mas por segurança)
            self._voltar_para_contexto_principal()
            
            # Aguarda a página carregar
            time.sleep(5)
            
            return True
                
        except Exception as e:
            logger.error(f"Erro ao clicar no Relatório: {e}")
            self._voltar_para_contexto_principal()
            return False

    def clicar_checklist(self):
        """Clica no link Check-List dentro do iframe"""
        return self._clicar_tipo_documento("Check-List")

    def clicar_ateste_nota_fiscal(self):
        """Clica no link Ateste para Nota Fiscal/Fatura"""
        # O nome pode variar - ajuste conforme necessário
        return self._clicar_tipo_documento("Ateste Para Nota Fiscal/Fatura")

    def clicar_despacho(self):
        """Clica no link Despacho"""
        return self._clicar_tipo_documento("Despacho")

    def _clicar_tipo_documento(self, nome_documento):
        """Função genérica para clicar em qualquer tipo de documento - VERSÃO OTIMIZADA"""
        try:
            logger.info(f"Procurando link: {nome_documento}...")
            
            # MULTIPLAS ESTRATÉGIAS PARA ENCONTRAR O LINK
            xpaths = [
                f"//a[@class='ancoraOpcao' and normalize-space(text())='{nome_documento}']",
                f"//a[contains(@class, 'ancoraOpcao') and normalize-space(text())='{nome_documento}']",
                f"//a[contains(@href, 'documento_gerar') and normalize-space(text())='{nome_documento}']",
                f"//table[@id='tblSeries']//a[normalize-space(text())='{nome_documento}']",
                f"//a[contains(text(), '{nome_documento}')]"
            ]
            
            link = None
            
            for xpath in xpaths:
                try:
                    link = self.driver.find_element(By.XPATH, xpath)
                    logger.info(f"Encontrado com: {xpath}")
                    break
                except:
                    continue
            
            if not link:
                logger.error(f"{nome_documento} não encontrado")
                return False
            
            # CLIQUE VIA JAVASCRIPT (mais confiável)
            self.driver.execute_script("arguments[0].click();", link)
            logger.info(f"{nome_documento} clicado!")
            
            # Volta para contexto principal
            self._voltar_para_contexto_principal()
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao clicar em {nome_documento}: {e}")
            self._voltar_para_contexto_principal()
            return False

    def criar_checklist(self):
        """Cria um Check-List - MESMA LÓGICA DO RELATÓRIO"""
        try:
            logger.info("Iniciando criação de Check-List...")
            print("\nINICIANDO CRIAÇÃO DE CHECK-LIST...")
            
            # 1. Clica em "Incluir Documento"
            if not self.clicar_incluir_documento():
                print("Falha ao clicar em 'Incluir Documento'")
                return False
            
            # 2. Clica no Check-List
            if not self.clicar_checklist():
                print("Falha ao selecionar Check-List")
                return False
            
            # 3. VERIFICA PÁGINA DE GERAR DOCUMENTO
            if not self._verificar_pagina_gerar_documento():
                print("Falha ao carregar página de gerar documento")
                return False
            
            # 4. Configura documento modelo (NOVO NÚMERO)
            if not self.configurar_documento_modelo("17963909"):  # Número do Check-List
                print("Falha ao configurar modelo Check-List")
                return False
            
            # 5. Confirma criação
            if not self.confirmar_criacao_documento():
                print("Falha ao confirmar criação")
                return False
            
            logger.info("Check-List criado com sucesso!")
            print("✅ CHECK-LIST criado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar Check-List: {e}")
            print(f"Erro ao criar Check-List: {e}")
            self._voltar_para_contexto_principal()
            return False

    def criar_ateste_nota_fiscal(self):
        """Cria Ateste para Nota Fiscal/Fatura"""
        try:
            logger.info("Iniciando criação de Ateste para Nota Fiscal/Fatura...")
            print("\nINICIANDO CRIAÇÃO DE ATESTE PARA NOTA FISCAL/FATURA...")
            
            if not self.clicar_incluir_documento():
                return False
            
            if not self.clicar_ateste_nota_fiscal():
                return False
            
            if not self._verificar_pagina_gerar_documento():
                return False
            
            if not self.configurar_documento_modelo("17961283"):  # Número do Ateste
                return False
            
            if not self.confirmar_criacao_documento():
                return False
            
            logger.info("Ateste criado com sucesso!")
            print("✅ ATESTE PARA NOTA FISCAL/FATURA criado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar Ateste: {e}")
            print(f"Erro ao criar Ateste: {e}")
            self._voltar_para_contexto_principal()
            return False

    def criar_despacho(self):
        """Cria Despacho"""
        try:
            logger.info("Iniciando criação de Despacho...")
            print("\nINICIANDO CRIAÇÃO DE DESPACHO...")
            
            if not self.clicar_incluir_documento():
                return False
            
            if not self.clicar_despacho():
                return False
            
            if not self._verificar_pagina_gerar_documento():
                return False
            
            if not self.configurar_documento_modelo("17963908"):  # Número do Despacho
                return False
            
            if not self.confirmar_criacao_documento():
                return False
            
            logger.info("Despacho criado com sucesso!")
            print("✅ DESPACHO criado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar Despacho: {e}")
            print(f"Erro ao criar Despacho: {e}")
            self._voltar_para_contexto_principal()
            return False

    def recarregar_pagina_processo(self):
        """Recarrega a página do processo para voltar ao estado inicial"""
        try:
            logger.info("Recarregando página do processo...")
            print("Recarregando página para próximo documento...")
            
            # Volta para contexto principal (segurança)
            self._voltar_para_contexto_principal()
            
            # Recarrega a página
            self.driver.refresh()
            time.sleep(5)
            
            # Aguarda recarregar os iframes
            if self._verificar_processo_aberto():
                logger.info("Página recarregada com sucesso")
                return True
            else:
                logger.warning("Página não recarregou corretamente")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao recarregar página: {e}")
            return False

    def criar_todos_documentos(self):
        """Cria todos os 4 documentos em sequência"""
        documentos_criados = 0
        documentos_falha = 0
        
        print("\n" + "="*60)
        print("INICIANDO CRIAÇÃO SEQUENCIAL DE TODOS OS DOCUMENTOS")
        print("="*60)
        
        # LISTA DE DOCUMENTOS A CRIAR (nome, função, número modelo)
        documentos = [
            ("RELATÓRIO", self.criar_relatorio),
            ("CHECK-LIST", self.criar_checklist),
            ("ATESTE PARA NOTA FISCAL/FATURA", self.criar_ateste_nota_fiscal),
            ("DESPACHO", self.criar_despacho)
        ]
        
        for nome, funcao in documentos:
            print(f"\n{'='*40}")
            print(f"DOCUMENTO: {nome}")
            print(f"{'='*40}")
            
            if funcao():
                documentos_criados += 1
                print(f"✅ {nome} - CRIADO COM SUCESSO")
            else:
                documentos_falha += 1
                print(f"❌ {nome} - FALHA NA CRIAÇÃO")
            
            # Recarrega a página entre documentos (exceto no último)
            if nome != "DESPACHO":
                if not self.recarregar_pagina_processo():
                    print("⚠️  Problema ao recarregar, continuando...")
        
        return documentos_criados, documentos_falha

    def configurar_documento_modelo(self, numero_modelo):
        """Configura o documento modelo dentro do iframe de visualização - VERSÃO ATUALIZADA"""
        try:
            logger.info(f"Configurando documento modelo: {numero_modelo}")
            
            # 1. Muda para o iframe de visualização
            if not self._mudar_para_iframe_visualizacao():
                return False
            
            # Aguarda página carregar completamente
            time.sleep(3)
            
            # PASSO 1: Clica no radio button "Documento Modelo" - NOVA ABORDAGEM
            logger.info("Clicando em 'Documento Modelo'...")
            try:
                # Estratégia 1: Tenta pelo ID original (funciona no seu caso)
                radio_modelo = self.wait.until(EC.element_to_be_clickable(
                    (By.ID, "optProtocoloDocumentoTextoBase")
                ))
                
                # Estratégia 2: Se não funcionar, tenta pela div pai (fallback)
                if not radio_modelo.is_displayed():
                    div_modelo = self.driver.find_element(By.ID, "divOptProtocoloDocumentoTextoBase")
                    self.driver.execute_script("arguments[0].click();", div_modelo)
                    logger.info("Clicado via div pai")
                else:
                    # Clique direto via JavaScript (mais confiável)
                    self.driver.execute_script("arguments[0].click();", radio_modelo)
                    logger.info("Radio 'Documento Modelo' clicado via JavaScript")
                    
            except Exception as e:
                logger.error(f"Erro ao clicar em 'Documento Modelo': {e}")
                # Tenta alternativa: clicar no label
                try:
                    label_modelo = self.driver.find_element(By.ID, "lblProtocoloDocumentoTextoBase")
                    label_modelo.click()
                    logger.info("Clicado via label")
                except:
                    self._voltar_para_contexto_principal()
                    return False
            
            # Aguarda o campo de texto ficar visível
            logger.info("Aguardando campo de número do modelo...")
            try:
                # Espera até que o campo esteja visível e habilitado
                campo_modelo = WebDriverWait(self.driver, 10).until(
                    lambda d: d.find_element(By.ID, "txtProtocoloDocumentoTextoBase").is_displayed()
                )
                campo_modelo = self.driver.find_element(By.ID, "txtProtocoloDocumentoTextoBase")
            except Exception as e:
                logger.error(f"Campo não ficou visível: {e}")
                self._voltar_para_contexto_principal()
                return False
            
            time.sleep(1)
            
            # PASSO 2: Preenche o número do modelo
            logger.info("Preenchendo número do modelo...")
            try:
                campo_modelo.clear()
                campo_modelo.send_keys(numero_modelo)
                logger.info(f"Número do modelo preenchido: {numero_modelo}")
            except Exception as e:
                logger.error(f"Erro ao preencher número: {e}")
                self._voltar_para_contexto_principal()
                return False
            
            time.sleep(1)
            
            # PASSO 3: Marca como Público - NOVA ABORDAGEM
            logger.info("Marcando como Público...")
            try:
                # Tenta pelo ID original
                radio_publico = self.driver.find_element(By.ID, "optPublico")
                
                # Verifica se já está selecionado
                if not radio_publico.is_selected():
                    # Clique via JavaScript
                    self.driver.execute_script("arguments[0].click();", radio_publico)
                    logger.info("Radio 'Público' clicado via JavaScript")
                else:
                    logger.info("Já estava marcado como público")
            except Exception as e:
                logger.warning(f"Não conseguiu marcar como público: {e}")
                # Tenta alternativa
                try:
                    div_publico = self.driver.find_element(By.ID, "divOptPublico")
                    div_publico.click()
                    logger.info("Público marcado via div")
                except:
                    # Continua mesmo sem marcar como público (não é crítico)
                    pass
            
            time.sleep(1)
            
            # Volta para contexto principal
            self._voltar_para_contexto_principal()
            
            logger.info("Configuração do documento modelo concluída!")
            return True
            
        except Exception as e:
            logger.error(f"Erro geral ao configurar: {e}")
            self._voltar_para_contexto_principal()
            return False
   
    def confirmar_criacao_documento(self):
        """Confirma a criação do documento clicando em 'Confirmar Dados'"""
        try:
            logger.info("Confirmando criação do documento...")
            
            # 1. Muda para o iframe de visualização
            if not self._mudar_para_iframe_visualizacao():
                return False
            
            # Encontra o botão "Confirmar Dados"
            botao_confirmar = self.wait.until(EC.element_to_be_clickable(
                (By.ID, "btnSalvar")
            ))
            
            # Rola até o botão para garantir visibilidade
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_confirmar)
            time.sleep(1)
            
            # Tenta clicar via JavaScript primeiro
            try:
                self.driver.execute_script("arguments[0].click();", botao_confirmar)
                logger.info("Botão 'Confirmar Dados' clicado via JavaScript")
            except Exception as js_error:
                logger.warning(f"Clique JS falhou, tentando clique normal: {js_error}")
                try:
                    botao_confirmar.click()
                    logger.info("Botão 'Confirmar Dados' clicado normalmente")
                except Exception as click_error:
                    logger.error(f"Clique normal também falhou: {click_error}")
                    self._voltar_para_contexto_principal()
                    return False
            
            # Volta para contexto principal
            self._voltar_para_contexto_principal()
            
            # Aguarda a criação do documento
            logger.info("Aguardando criação do documento...")
            time.sleep(5)
            
            return True
                
        except Exception as e:
            logger.error(f"Erro ao confirmar criação: {e}")
            self._voltar_para_contexto_principal()
            return False

    def criar_relatorio(self):
        """Cria um Relatório - VERSÃO AUTOMATIZADA"""
        try:
            logger.info("Iniciando criação de Relatório...")
            print("\nINICIANDO CRIAÇÃO DE RELATÓRIO...")
            
            # 1. Clica em "Incluir Documento" (mantém no iframe)
            if not self.clicar_incluir_documento():
                print("Falha ao clicar em 'Incluir Documento'")
                return False
            
            # 2. CLICA DIRETAMENTE NO RELATÓRIO (dentro do iframe)
            if not self.clicar_documento_relatorio():
                print("Falha ao selecionar Relatório")
                return False
            
            # 3. VERIFICA SE CHEGOU NA PÁGINA DE GERAR DOCUMENTO
            if not self._verificar_pagina_gerar_documento():
                print("Falha ao carregar página de gerar documento")
                return False
            
            # 4. Configura documento modelo (número fixo)
            if not self.configurar_documento_modelo(NUMERO_MODELO):
                print(f"Falha ao configurar modelo {NUMERO_MODELO}")
                return False
            
            # 5. Confirma criação
            if not self.confirmar_criacao_documento():
                print("Falha ao confirmar criação")
                return False
            
            logger.info("Relatório criado com sucesso!")
            print(f"\nRELATÓRIO criado com sucesso com modelo {NUMERO_MODELO}!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar Relatório: {e}")
            print(f"Erro ao criar Relatório: {e}")
            self._voltar_para_contexto_principal()
            return False

    def executar_rotina_relatorios(self):
        
        try:
            print("\n" + "="*70)
            print("SEI - CRIACAO AUTOMÁTICA DE TODOS OS DOCUMENTOS")
            print("="*70)
            
            # 1. COLETAR DADOS BÁSICOS
            self.config = self.coletar_dados_usuario()
            if not self.config:
                return False
            
            # 2. CONFIGURAR NAVEGADOR
            self.configurar_chrome()
            
            # 3. FAZER LOGIN
            if not self.fazer_login_sei(self.config['usuario'], self.config['senha']):
                return False
            
            # 4. BUSCAR PROCESSO
            if not self.buscar_processo(self.config['numero_processo']):
                return False
            
            # 5. CRIA TODOS OS 4 DOCUMENTOS
            sucessos, falhas = self.criar_todos_documentos()
        
            # RESUMO FINAL
            print("\n" + "="*60)
            print("RESUMO FINAL DA EXECUÇÃO")
            print("="*60)
            print(f"✅ Documentos criados com SUCESSO: {sucessos}/4")
            print(f"❌ Documentos com FALHA: {falhas}/4")
            print("="*60)
            
            if sucessos == 4:
                print(f"\n🎉 SUCESSO TOTAL! Todos os 4 documentos criados no processo {self.config['numero_processo']}")
                return True
            elif sucessos > 0:
                print(f"\n⚠️  PARCIAL: {sucessos} de 4 documentos criados com sucesso")
                return True
            else:
                print(f"\n❌ Nenhum documento foi criado com sucesso")
                return False
                
        except Exception as e:
            logger.error(f"Erro na rotina: {e}")
            print(f"Erro crítico: {e}")
            return False
        finally:
            if self.driver:
                time.sleep(2)
                self.driver.quit()
                logger.info("Navegador fechado")
                print("\nNavegador fechado")

# =======================
# EXECUÇÃO PRINCIPAL
# =======================

if __name__ == "__main__":
    print("SEI Relatorio Creator - Versão Automatizada")
    print("⚠️  CONFIGURE SEU USUÁRIO E SENHA NO CÓDIGO ANTES DE USAR!")
    
    # Verifica se as credenciais foram configuradas
    if USUARIO_SEI == "marlon.cxarvalho" or SENHA_SEI == "Y4mipasxsword#":
        print("\n❌ ERRO: Configure seu usuário e senha nas variáveis USUARIO_SEI e SENHA_SEI")
        print("Localize as linhas no início do código e altere com suas credenciais.")
        exit(1)
    
    creator = SEIRelatorioCreator()
    success = creator.executar_rotina_relatorios()
    
    if success:
        print("\n✅ Processo finalizado com sucesso!")
        exit(0)
    else:
        print("\n❌ Ocorreram erros durante o processo.")

        exit(1) 
