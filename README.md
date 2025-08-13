
# Projeto RAG + Chat + WhatsApp (FastAPI + OpenAI + Pinecone)

- Este repositório reúne um backend em FastAPI (Python) para RAG/Chat e um servidor Node para o bot de WhatsApp (via whatsapp-web.js), além de páginas HTML para uso via navegador.
- Permite criar Agente de IA e nutri-lo com informações específicas atravez de arquivos .txt
- Permite usar moldelo de LLM para avaliar as respostas do Agente de IA, usando métricas de precisão, cobertura e Recall@.
- Permite integração com whatsapp.

## Resumo do que você terá localmente
- **API FastAPI** (porta 8000) com endpoints de RAG, chat e avaliação.  
- **UI simples em HTML** (páginas: `/`, `/chatbot`, `/avaliacao-auto`, `/avaliacao-seq`, `/wa`).  
- **Bot de WhatsApp Web** (porta 3001) que conecta no seu WhatsApp e encaminha mensagens para a API do chat.  
- **Integração com OpenAI** (embeddings e chat) e **Pinecone** (vector store).  

---

## 1) Requisitos
- Python 3.11+ (recomendado 3.12)  
- Node.js 18+ (LTS) e npm  
- Conta/credenciais de:
  - OpenAI – chave da API  
  - Pinecone – chave da API e um Index

---

## 2) Estrutura principal
```
PY/
├─ main.py                  # ponto de entrada FastAPI
├─ api/                     # rotas FastAPI
├─ services/                # regras de negócio (RAG, busca, chat, etc.)
├─ html/                    # páginas HTML (index, chat, avaliação, wa_dashboard)
├─ documentos/              # textos exemplo (usados para RAG)
├─ wa-bot/                  # bot WhatsApp (Node + whatsapp-web.js)
└─ requirements.txt         # dependências Python 
└─ transformers/            # scripts .py para limpeza de dados
```

---

## 3) Variáveis de ambiente (.env)
Crie um arquivo `PY/.env` com o conteúdo (**NÃO compartilhe esta chave publicamente**):
```ini
api_key_openIA="SUA_CHAVE_OPENAI_AQUI"
api_key_pinecone="SUA_CHAVE_PINECONE_AQUI"
```

---

## 4) Instalação (Python / FastAPI) e Creiacao de Base Vetorial
Abra um terminal na pasta `PY`.

**Crie e ative um ambiente virtual:**
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

**Instale as dependências:**
```bash
pip install -r requirements.txt
```

**Rode a API:**
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Acesse:  
- Home: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
- Chat: [http://127.0.0.1:8000/chatbot](http://127.0.0.1:8000/chatbot)  
- Avaliação (auto): [http://127.0.0.1:8000/avaliacao-auto](http://127.0.0.1:8000/avaliacao-auto)  
- Avaliação (sequencial): [http://127.0.0.1:8000/avaliacao-seq](http://127.0.0.1:8000/avaliacao-seq)  
- Dashboard WhatsApp: [http://127.0.0.1:8000/wa](http://127.0.0.1:8000/wa)  

**Criar o index no pinecone**
- Acesse o Swagger(/docs) e utilize a rota /api/index/create
- Nos script .py dentro da pasta transformers, atrele o nome do index criado a varial INDEX_NAME

- Execute o orquestrador de scripts:
- 0_orquestrador.py

## 5) Instalação do bot WhatsApp (Node)
```bash
cd PY/wa-bot
npm install
npm start
```
---

## 6) Pinecone e embeddings
- **Modelo embeddings**: `text-embedding-3-small` (1536 dimensões)  
- **Index Pinecone**: `INDEX_NAME = "testeanalistasr"`  
- **Métrica**: `cosine`  

---

## 7) Endpoints principais
- `POST /api/chat/message` – envia mensagem e recebe resposta do RAG.  
- `POST /api/chat/reset` – limpa memória da sessão.  
- `POST /api/index/create` – cria index Pinecone.  
- `GET /api/index/list` – lista indexes.  

---

## 8) URLs úteis
- `/` – Home  
- `/chatbot` – Chat  
- `/avaliacao-auto` – Avaliação automática  
- `/avaliacao-seq` – Avaliação sequencial  
- `/wa` – Dashboard WhatsApp  

---

## 9) Dicas e Problemas Comuns
- QR não aparece? Verifique se o bot está ativo e acessível na porta 3001.  
- Index não encontrado? Crie manualmente no Pinecone ou via API.  

---

## 10) Scripts de desenvolvimento
- API:  
```bash
uvicorn main:app --reload --port 8000
```
- Bot:  
```bash
cd wa-bot && npm start
```
---

## 11) Roadmap
- Script de ingestão para Pinecone  
- Index name configurável via `.env`  
- Memória de chat persistente  
- Docker Compose para API e Bot  

---

## 13) Decisões Técnicas

### 13.1 Modelo de Embeddings – `text-embedding-3-small`
**Escolhido por:**
- Dimensão padrão (1536) suportada pelo Pinecone.  
- Custo baixo e boa precisão para buscas semânticas.  
- Velocidade para processar grandes lotes de texto.  

### 13.2 Métrica – `cosine`
**Escolhida por:**
- Comparar ângulo entre vetores, ideal para embeddings normalizados.  
- Ignorar magnitude, focando apenas no significado.  
- Suporte nativo no Pinecone.  

### 13.3 Modelo de Resposta – `gpt-3.5-turbo`
**Escolhido por:**
- Equilíbrio entre custo e qualidade.  
- Velocidade ideal para uso interativo.  
- Bom para consultas simples e médias.  

### 13.4 Avaliação – `gpt-5`
**Escolhido por:**
- Maior capacidade de raciocínio e contexto.  
- Melhor identificação de nuances semânticas.  
- Usado apenas para avaliação, mantendo custo sob controle.  

---


## 14) Instruções de Uso

### 1. Swagger (API)
📍 **Finalidade:**
- Exibir a documentação interativa da API do sistema.
- Permitir testar os endpoints diretamente pelo navegador.

🛠 **Como usar:**
1. Clique no botão **Swagger (API)**.
2. Navegue pela lista de endpoints disponíveis.
3. Clique em um endpoint para expandir suas opções.
4. Use o botão **Try it out** para executar chamadas diretamente, informando parâmetros e corpo de requisição.
5. Veja a resposta retornada pela API em tempo real.

### 2. Chatbot
📍 **Finalidade:**
- Interface para interação com o assistente virtual.
- Permite fazer perguntas e receber respostas em linguagem natural.

🛠 **Como usar:**
1. Clique no botão **Chatbot**.
2. Digite sua pergunta no campo de entrada.
3. Pressione **Enter** ou clique no botão de envio.
4. Aguarde a resposta do assistente.

### 3. Avaliação Automática
📍 **Finalidade:**
- Realizar avaliação de respostas utilizando critérios automáticos.
- Útil para análise rápida e padronizada de conteúdo.

🛠 **Como usar:**
1. Clique no botão **Avaliação Automática**.
2. Insira ou selecione a resposta a ser avaliada.
3. O sistema aplicará as métricas configuradas (ex.: precisão, cobertura semântica, recall).
4. Veja os resultados exibidos na tela.

### 4. Avaliação Sequencial
📍 **Finalidade:**
- Avaliar respostas de forma ordenada, seguindo um fluxo pré-definido.
- Ideal para revisões manuais ou testes de múltiplos exemplos.

🛠 **Como usar:**
1. Clique no botão **Avaliação Sequencial**.
2. Navegue pelas perguntas e respostas apresentadas pelo sistema.
3. Avance até completar todas as avaliações.

### 5. WhatsApp Bot
📍 **Finalidade:**
- Gerenciar e monitorar o bot de integração com o WhatsApp.
- Permite escanear o QR Code para autenticação e acompanhar mensagens.

🛠 **Como usar:**
1. Clique no botão **WhatsApp Bot**.
2. Escaneie o QR Code exibido usando o aplicativo do WhatsApp no celular.
3. Acesse: *WhatsApp > Menu > Aparelhos Conectados > Conectar Dispositivo*.
4. Após a autenticação, o status mudará para **Conectado**.
5. Visualize e envie mensagens diretamente pelo painel.


## 15) Avaliações e Insights

### 1. Tipos de perguntas que funcionam melhor
- Perguntas diretas e factuais, buscando listas de requisitos ou procedimentos (ex.: *Quais são as exigências para clientes negativados?*, *Quais produtos a empresa oferece?*, *Quais práticas de compliance são adotadas?*).  
- Nessas perguntas, o modelo obteve Precisão, Cobertura e Recall altos (>= 9.5).  
- Respostas estruturadas que cobrem praticamente todo o conteúdo dos chunks relevantes.  
- Perguntas sobre políticas bem documentadas, especialmente quando os chunks contêm listas claras ou frases objetivas.  
- Perguntas com termos específicos (*cartão consignado*, *FGTS*, *comitê de crédito*) que ajudam no match exato no RAG.  

### 2. Lacunas na base de conhecimento
- Alguns temas aparecem fragmentados ou em documentos não diretamente relacionados, confundindo o modelo.  
- Ex.: Pergunta sobre liberação de e-mail corporativo respondeu com dados de segurança da informação, sem conectar ao onboarding (causa real).  
- Informações complementares relevantes não aparecem no mesmo chunk.  
- Pouco contexto narrativo ou exemplos de aplicação; conteúdo muito normativo/listado.  

### 3. Tipos de erros cometidos pelo modelo
- **Cobertura incompleta**: ignorou pontos relevantes nos chunks (ex.: LGPD sem citar criptografia, antivírus, monitoramento, incidentes).  
- **Uso de adjetivos genéricos não suportados**: termos como “rigorosas” e “outras normas” sem respaldo textual.  
- **Confusão de contexto**: misturou segurança de TI com causas administrativas.  
- **Falta de priorização**: listou pontos menos relevantes antes dos centrais.  

### 4. Recomendações técnicas
- **Otimização do chunking**: manter informações correlatas no mesmo chunk, aumentar tamanho quando o tema for interligado.  
- **Enriquecimento de metadados**: taggear documentos por tópico principal (Onboarding, Segurança, Produtos, Compliance).  
- **Aprimorar re-ranking**: priorizar chunks com match semântico e de entidade chave.  
- **Modelo**: GPT-5 teve bom desempenho nas factuais, mas pode ser ajustado para recall completo.  
- **Pós-processamento**: passo de verificação de cobertura total antes de exibir resposta.  


