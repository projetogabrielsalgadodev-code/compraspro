# Passo a Passo: Setup Final do Frontend (Autenticação e Admin)

Este é o guia completo das **ações manuais obrigatóricas** que você (Administrador) precisa executar no seu projeto e no painel do Supabase para que os módulos de Autenticação, Proteção de Rotas e Telas Administrativas fiquem 100% funcionais.

---

## 1. Aplicar Scripts no Banco de Dados (Supabase)
Todo o frontend agora depende de tabelas como `perfis`, `empresas` e `configuracoes_empresa`. 

1. Acesse o **[Painel do Supabase](https://supabase.com/dashboard)**.
2. Vá até o menu lateral **SQL Editor**.
3. Abra um **New Query** (Nova Consulta).
4. Copie o conteúdo completo do arquivo `python-api/migrations/001_criar_tabelas_analises.sql`.
5. Cole no editor do Supabase e clique em **Run** (Executar).
   - *Isso criará todas as tabelas administrativas, as políticas de segurança (RLS) e a Trigger padrão para auto-cadastrar o perfil ao registrar um log-in no Supabase.*

---

## 2. Configurar os Redirecionamentos de Autenticação (PKCE)
O nosso sistema de "Esqueci a Senha" e "Convites" depende que o Supabase saiba qual é a URL do seu frontend para mandar o usuário de volta com segurança.

1. No Supabase, vá até menu **Authentication** -> **URL Configuration**.
2. Na seção **Site URL**, garanta que o valor preenchido seja: `http://localhost:3000` (ou sua URL de produção caso em deploy).
3. Na seção **Redirect URLs**, adicione a seguinte URL exata:
   - `http://localhost:3000/auth/callback`
   - *Nota: Caso falte isso, os botões sentados no email de recuperação ou convite darão tela preta (redirecionamento inválido).*

---

## 3. Criar o SEU Perfil de Super Admin (O Primeiro Usuário)
A rota `/admin` e todos as páginas de gerenciamento criadas no Next.js estão restritas e verificam se o `papel` do usuário logado é igual a `admin`. Você precisa de uma primeira chave-mestra.

1. **Registre-se:**
   - Rode o projeto: `cd apps/web && npx next dev`
   - Vá até `http://localhost:3000/auth/login`. Como ainda não temos página de registro, crie um usuário inserindo seu email através do menu do Supabase:
     - Acesse **Authentication** -> **Users** no Supabase.
     - Clique em **Add User** -> **Create New User**.
     - Coloque seu email (ex: `admin@compraspro.com.br`) e defina uma senha.
2. **Atribua a Permissão:**
   - Com o usuário criado no item anterior, vá até o menu lateral **Table Editor**.
   - Abra a tabela `perfis` (`public.perfis`). Você verá lá o registro do seu email/conta recém criado.
   - Dê um duplo-clique na coluna `papel` da sua linha e escreva `admin`.
   - Modifique também a coluna `nome` e digite seu nome verdadeiro se desejar.

---

## 4. Testando o Acesso
1. Vá até `http://localhost:3000/auth/login`.
2. Faça login informando o email/senha criados na etapa 3.
3. Se tudo deu certo, o sistema deverá redirecioná-lo para a Dashboard interna em `http://localhost:3000/admin/empresas`.

---

## 5. Setup Inicial das Empresas e Parâmetros
O nosso backend/IA funciona na premissa de processar o CNPJ e os parâmetros do algoritmo configurados por base.

1. **Criar a Primeira Empresa:**
   - Estando logado via navegador em `/admin/empresas`, clique em **Cadastrar Empresa**.
   - Coloque o CNPJ e Empresa padrão da sua rede de farmácias.
2. **Definir as Configurações da IA:**
   - Pelo menu esquerdo, vá para a tela **Parâmetros** (`/admin/parametros`).
   - Selecione a empresa recém-criada no Input.
   - Ajuste e grave a **Margem de Lucro Padrão**, **Dias de Histórico Visíveis** e o **Alerta de Variações**.
   - Clique em **Salvar**. A partir de agora o robô no backend possui a inteligência mapeada!

---

## 6. Fluxo de Equipe (Módulo de Usuários e Convites)
1. Pelo menu esquerdo, vá para a tela **Usuários** (`/admin/usuarios`).
2. Clique no botão de enviar um novo convite mágico e convide outro email corporativo.
3. O console enviará via "Supabase Auth Admin", o que disparará um link seguro no e-mail dessa nova pessoa informando para ela definir uma senha de entrada.

---

### Resumo do Check de 100% ✅
- [ ] Banco Atualizado (`001_criar_tabelas_analises.sql` rodado).
- [ ] Supabase com `Site URL` habilitando o `http://localhost:3000`.
- [ ] `perfil` atualizado manualmente como `admin` no Painel Supabase.
- [ ] Pelo menos `1` Empresa Cadastrada pelo dashboard Next.js.
- [ ] Pelo menos `1` Configuração Global Inserida vinculada à Empresa (Aba Parâmetros).

Você concluiu o Setup de Ambiente FrontEnd+Auth do ComprasPRO!
