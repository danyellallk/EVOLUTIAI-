# EVOLUTIA AI — versão 0.3

API experimental para registrar perguntas de pesquisa e propostas de melhoria, com supervisão humana.

## Recursos
- API FastAPI com documentação interativa em `/docs`.
- Verificação de saúde em `/health`, incluindo teste de conexão com o banco.
- Cadastro e consulta de perguntas de pesquisa.
- Cadastro e consulta de propostas de melhoria.
- Aprovação administrativa de propostas, sem alteração automática de código.
- Análise textual opcional com modelo OpenAI pela rota `POST /ai/analyze`, sem execução de código.
- Autenticação Bearer nas rotas que alteram dados.
- Banco PostgreSQL no Render e SQLite para desenvolvimento local.

## Implantação no Render
1. No Render, escolha **New + → Blueprint**.
2. Conecte o repositório `danyellallk/EVOLUTIAI-`.
3. O Render lerá `render.yaml` e solicitará `EVOLUTIA_ADMIN_TOKEN`.
4. Gere uma chave longa e aleatória no próprio Render e guarde-a em local privado. Nunca coloque a chave no GitHub nem a envie em conversas.
5. Para ativar a análise com IA, configure `OPENAI_API_KEY` nas variáveis de ambiente do serviço Render. Opcionalmente, configure `OPENAI_MODEL` (padrão `gpt-5.5`). A chave é fornecida pelo painel da plataforma OpenAI; nunca a coloque no GitHub nem a envie em conversas. O uso da API pode gerar cobranças separadas.
6. Após a implantação, teste `/`, `/health` e `/docs`.

## Rotas
- `GET /` — status e versão.
- `GET /health` — saúde da API e do banco.
- `GET /docs` — documentação interativa.
- `GET /dashboard` — painel web inicial.
- `GET /research` — consulta de pesquisas.
- `POST /research` — cria pesquisa (Bearer obrigatório).
- `GET /improvements` — consulta propostas.
- `POST /improvements` — cria proposta (Bearer obrigatório).
- `POST /improvements/{id}/approve` — aprova proposta para revisão controlada (Bearer obrigatório).
- `POST /ai/analyze` — gera análise com IA (Bearer obrigatório e `OPENAI_API_KEY` configurada).

## Desenvolvimento local
```bash
python -m venv .venv
# Ative o ambiente virtual e instale as dependências:
pip install -r requirements.txt
# Configure EVOLUTIA_ADMIN_TOKEN e, opcionalmente, DATABASE_URL.
uvicorn app.main:app --reload
```

## Limites e segurança
A integração de IA é opcional e só funciona após configurar uma chave de API válida; não realiza pesquisa autônoma na internet. A aprovação apenas marca uma proposta como aprovada; não executa nem publica código. Antes de uso público, implemente login individual, permissões por usuário, auditoria, limites de requisição, backups e testes automatizados. A análise não executa código, não altera arquivos e não aprova propostas. Qualquer execução experimental deve ocorrer em ambiente isolado. Proteja a chave administrativa e nunca a compartilhe.
