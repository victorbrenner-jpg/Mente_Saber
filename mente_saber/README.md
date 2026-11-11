# Mente Saber — MVP inicial

Plataforma experimental de tutores de aprendizagem com IA. Este projeto é um ponto de partida funcional para desenvolvimento e testes locais; ainda não está pronto para uso comercial público.

## Recursos desta versão

- Cadastro e login com senha armazenada por hash.
- Banco SQLite local.
- Chat por disciplina.
- Histórico de mensagens por usuário e disciplina.
- Limite inicial de 3 perguntas gratuitas por conta.
- Tutores para Português e Gramática, Matemática, Inglês, Programação e Tecnologia, e História.
- Integração opcional com a API da OpenAI.
- Tela de plano de R$ 35/mês com ativação apenas demonstrativa.

## Requisitos

- Windows 10/11
- Python 3.11 ou superior recomendado
- PowerShell

## Instalação pelo PowerShell

Abra o PowerShell e entre na pasta do projeto. Exemplo, se descompactou em Downloads:

```powershell
cd "$HOME\Downloads\mente_saber"
```

Crie um ambiente virtual:

```powershell
py -m venv .venv
```

Ative o ambiente:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute apenas nesta janela:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Crie o arquivo de configuração:

```powershell
Copy-Item .env.example .env
notepad .env
```

Para respostas reais de IA, coloque sua chave no campo `OPENAI_API_KEY` e salve o arquivo. Não compartilhe a chave nem a publique no GitHub. O uso da API pode gerar cobranças independentes da assinatura que você futuramente cobrar dos clientes.

Inicie o aplicativo:

```powershell
streamlit run app.py
```

O Streamlit abrirá o endereço local no navegador, normalmente `http://localhost:8501`.

## Teste sem chave de API

O app pode ser aberto sem chave para testar cadastro, login, navegação e interface. O tutor exibirá uma mensagem de demonstração, pois respostas de IA reais exigem a configuração da API.

## Atenção: antes de lançar publicamente

Esta é uma versão MVP de desenvolvimento. Não cobre nem processa pagamentos reais. O botão de assinatura é apenas demonstrativo e não deve ser tratado como comprovação de pagamento.

Antes de abrir ao público, precisamos:
1. Substituir SQLite local por banco de dados gerenciado, como PostgreSQL.
2. Implementar autenticação e recuperação de senha com fluxos seguros.
3. Integrar um provedor de pagamento recorrente e validar notificações/webhooks no servidor.
4. Fazer controle de uso no backend com transações atômicas, limites contra abuso e monitoramento de custos.
5. Configurar segredos no ambiente de hospedagem, HTTPS, backups, logs e proteção contra abuso.
6. Criar termos de uso, política de privacidade e processo compatível com a LGPD.
7. Avaliar proteção especial caso o serviço seja utilizado por crianças e adolescentes.
8. Testar qualidade das respostas, segurança e acessibilidade.

## Próximas etapas sugeridas

- Fase 2: histórico melhorado, novo chat e interface mais polida.
- Fase 3: base de conhecimento curada e respostas com referências.
- Fase 4: pagamentos recorrentes reais e painel administrativo.
- Fase 5: implantação online, monitoramento e testes com usuários.
