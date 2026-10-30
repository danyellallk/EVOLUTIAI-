# EVOLUTIA AI — versão 0.2

Base experimental em nuvem para pesquisa e propostas de aperfeiçoamento com supervisão humana.

## O que esta versão faz
- API com status e verificação de saúde.
- Registro e consulta de perguntas de pesquisa.
- Registro e consulta de propostas de melhoria.
- Proteção por chave administrativa (Bearer token) nas rotas que alteram dados.
- Aprovação de proposta apenas para revisão controlada; não altera nem publica código automaticamente.

## Implantação no Render
1. Envie o conteúdo desta pasta para a raiz de um repositório GitHub.
2. No Render, escolha **New + → Blueprint** e conecte o repositório.
3. O Render encontrará `render.yaml` e solicitará o valor de `EVOLUTIA_ADMIN_TOKEN`.
4. Crie uma chave longa e aleatória e guarde-a em local privado. Nunca a coloque no GitHub.
5. Após a implantação, teste `/health` e `/docs`.

## Rotas
- `GET /` — status
- `GET /health` — saúde do serviço
- `GET /docs` — documentação interativa
- `GET /research` e `GET /improvements` — consultas
- `POST /research`, `POST /improvements` e `POST /improvements/{id}/approve` — exigem `Authorization: Bearer SUA_CHAVE`

## Limites e segurança
Esta versão ainda não integra um modelo de IA, não faz pesquisa autônoma real e não modifica o próprio código. As rotas de alteração exigem chave administrativa. Proteja essa chave, não a compartilhe e não a envie em conversas. Antes de uso público, acrescente login individual, permissões por usuário, auditoria, limites de requisição e backups. Execução de experiências deve ocorrer em ambiente isolado.
