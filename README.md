# Cooler Display Monitor

Um serviço em Python para Linux projetado para monitorar a temperatura da CPU ou o consumo de energia (via RAPL) e exibir essas informações em tempo real em um display de Air Cooler via USB.

> ⚠️ **Aviso: use por sua conta e risco.**
> Este projeto foi testado **somente** no ambiente descrito abaixo (esta combinação específica de
> placa-mãe, processador, sistema operacional e display USB). Ele se comunica diretamente com um
> dispositivo USB via chamadas de baixo nível (`ctrl_transfer`), incluindo o desanexamento de
> drivers do kernel — em outro hardware ou modelo de display, o comportamento é desconhecido e
> **não há garantia de compatibilidade ou de que o dispositivo não será afetado de forma
> inesperada**. O software é fornecido "como está", sem garantias de qualquer tipo — veja a
> seção de [Licença](#-licença). Se for testar em um setup diferente do documentado, faça por
> sua conta e risco.
>
> **Na dúvida, não use — procure um profissional de sua confiança antes de rodar isso em
> hardware que você não pode se dar ao luxo de perder.**

## 🧪 Ambiente de Testes
O projeto foi validado e testado com sucesso no seguinte setup:
* **Placa-mãe:** [Asus Sabertooth X79](https://www.asus.com/supportonly/sabertooth_x79/helpdesk_knowledge/)
* **Processador:** [Intel Core i7-3930K (Arquitetura Sandy Bridge-E)](https://www.intel.com.br/content/www/br/pt/products/sku/63697/intel-core-i73930k-processor-12m-cache-up-to-3-80-ghz/specifications.html)
* **Hardware de Exibição:** [Air Cooler Rise Mode Temp 6 Black](https://risemode.com/temp-6-black/)
* **Linux:** Ubuntu [22.04.5 LTS](https://releases.ubuntu.com/jammy/)

## 🚀 Funcionalidades
* Monitoramento de Hardware: Coleta dados de temperatura via psutil ou consumo de energia via intel-rapl.
* Conectividade USB: Gerenciamento automático de dispositivos USB, incluindo o desanexamento de drivers do kernel que podem bloquear a comunicação.
* Resiliência: Reconexão automática em caso de desconexão do dispositivo, e reinício automático do processo via systemd em caso de falha.
* Service-Ready: Projetado para rodar como um serviço em segundo plano (systemd), garantindo um desligamento gracioso (graceful shutdown) ao receber sinais do sistema.
* Baixo impacto: Logging configurado apenas para erros, mantendo o sistema leve e limpo.

## 📋 Pré-requisitos
* Python 3.x
* Pacote `python3-venv` (em sistemas Debian/Ubuntu, geralmente não vem instalado por padrão):
  ```bash
  sudo apt install python3-venv
  ```
* Bibliotecas: pyusb, psutil
* Acesso root (necessário para interagir com o dispositivo USB e/ou ler sensores de energia)

## 📦 Instalação

1. Clone o repositório:
   ```bash
   cd /opt
   sudo git clone https://github.com/celsorv/cooler-display.git
   cd cooler-display
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   /usr/bin/python3 -m venv .venv
   source .venv/bin/activate
   ```

   > ⚠️ **Importante se você usa pyenv, conda, ou qualquer outro gerenciador de versões Python:**
   > Use o caminho completo `/usr/bin/python3` (Python do sistema) em vez de apenas `python3`.
   > Este serviço vai rodar via systemd como root, de forma totalmente isolada do seu shell de
   > usuário — se o venv for criado a partir de um Python gerenciado por pyenv/conda (instalado
   > dentro do seu `$HOME`), ele vai gerar um link simbólico apontando para dentro de `/home/seu-usuario/...`.
   > Isso quebra caso o serviço seja endurecido com `ProtectHome=true` (ver seção de hardening
   > abaixo), e é uma dependência frágil de qualquer forma — o serviço ficaria refém do ambiente
   > pessoal de um usuário específico. Confira com `ls -la .venv/bin/python` se o link não está
   > apontando para dentro de `/home/`.

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   deactivate
   ```

## ⚙️ Configuração como Serviço (Systemd)

Para que o monitoramento inicie automaticamente com o sistema:

1. Crie o arquivo de serviço:
   ```bash
   sudo nano /etc/systemd/system/cooler-display.service
   ```
   (o nome do arquivo aqui — `cooler-display.service`, com hífen — é o que define o nome da
   unidade usado em todos os comandos `systemctl` abaixo; mantenha a consistência.)

2. Cole a configuração abaixo (ajuste os caminhos para o seu diretório):

   ```ini
   [Unit]
   Description=Cooler Display Monitor Service
   After=multi-user.target systemd-udevd.service

   [Service]
   ExecStart=/opt/cooler-display/.venv/bin/python -u /opt/cooler-display/main.py
   WorkingDirectory=/opt/cooler-display

   # Reinicia sempre que o processo terminar (sucesso, erro ou sinal).
   Restart=always

   # Espera entre tentativas de restart, para não martelar o dispositivo USB.
   RestartSec=5

   # Tolerância a múltiplas falhas antes do systemd desistir de vez
   # (sem isso, o padrão é desistir após 5 falhas em 10s).
   StartLimitIntervalSec=300
   StartLimitBurst=20

   # Tempo máximo de espera no shutdown antes de forçar o encerramento.
   TimeoutStopSec=10
   
   # Permite filtrar logs com: journalctl -t cooler-display
   SyslogIdentifier=cooler-display

   User=root

   # Hardening: reduz o que o processo pode fazer, mesmo rodando como root.
   NoNewPrivileges=true
   ProtectSystem=strict
   ProtectHome=true
   PrivateTmp=true
   ReadWritePaths=/opt/cooler-display
   MemoryMax=100M

   [Install]
   WantedBy=multi-user.target
   ```

3. Recarregue a configuração do systemd, habilite e inicie o serviço:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable cooler-display.service
   sudo systemctl start cooler-display.service
   ```

   > ⚠️ **Sempre que editar o arquivo `.service` depois de já tê-lo carregado uma vez**
   > (ex: `enable`/`start` já executados antes), é obrigatório rodar `sudo systemctl daemon-reload`
   > antes de dar `restart` — caso contrário o systemd continua usando a versão antiga em memória.

## 📝 Monitoramento e Logs
Como o serviço roda em segundo plano, você pode verificar o status e ver os logs (caso ocorra algum erro) com o seguinte comando:
```bash
sudo systemctl status cooler-display.service
journalctl -u cooler-display.service -f
```

## 🔧 Troubleshooting

**`status=203/EXEC` ou "Failed to locate executable ... No such file or directory"**
O caminho do Python no `.venv/bin/python` não existe de verdade — geralmente porque o `.venv` foi
apagado/recriado incorretamente, ou (se estiver usando `ProtectHome=true`) o venv foi criado a
partir de um Python instalado dentro de `/home/` (ex: pyenv), que fica invisível para o processo
com esse hardening ativo. Recrie o venv com `/usr/bin/python3` conforme a seção de Instalação.

**Display pisca e volta ocasionalmente**
Normal em baixa frequência — costuma ser uma leitura de sensor momentaneamente indisponível,
que força uma reconexão preventiva. Se acontecer com muita frequência, verifique
`journalctl -u cooler-display.service` por padrões recorrentes.

**Display trava e não volta mais até reiniciar o PC**
Verifique `sudo systemctl status cooler-display.service`:
- Se mostrar `active (running)` mas o log tiver `Failed to send report` repetido sem nunca se
  recuperar: é um travamento real do dispositivo USB (barramento/firmware), que exige replug
  físico ou reboot — nenhum retry de software resolve isso.
- Se mostrar `failed (Result: start-limit-hit)`: o systemd esgotou as tentativas de restart.
  Rode `sudo systemctl reset-failed cooler-display.service` e depois `start` novamente, sem
  precisar reiniciar a máquina inteira.

## ⚠️ Notas de Compatibilidade
* **Processadores Intel:**
    - O monitoramento de energia (RAPL) é suportado nativamente na maioria das arquiteturas Intel desde a microarquitetura Sandy Bridge.
* **Processadores AMD:**
    - O driver intel-rapl não é compatível com processadores AMD. Usuários de sistemas AMD podem utilizar o monitoramento de temperatura normalmente, mas devem manter a configuração 'USE_WATTS = False'.

## 🏗️ Como funciona (Arquitetura)
O código utiliza uma abordagem de loop infinito com tratamento de sinais. Ele captura o sinal SIGTERM do sistema operacional e o converte em uma exceção KeyboardInterrupt, permitindo que o programa feche a porta USB corretamente antes de finalizar, evitando o travamento do hardware. Erros reais de USB durante a execução acionam uma reconexão automática (fechando e reabrindo o dispositivo); outros erros inesperados são registrados em log sem derrubar a conexão USB ativa.

## ™️ Marcas Registradas
Os nomes de produtos, marcas e fabricantes mencionados neste README (Asus, Intel, Rise Mode,
Ubuntu, entre outros) são citados apenas para fins de identificação de compatibilidade de
hardware/software e pertencem aos seus respectivos proprietários. Este é um projeto pessoal e
independente, criado para resolver um problema específico de compatibilidade do autor — não há
qualquer vínculo, patrocínio, autorização ou endosso por parte desses fabricantes.

## 🚫 Nenhuma garantia implícita por documentação, testes ou suporte
O fato deste projeto ter documentação detalhada, testes descritos, uma seção de troubleshooting,
ou de o autor eventualmente responder issues/dúvidas, **não constitui garantia de confiabilidade,
segurança, qualidade ou adequação a qualquer finalidade** — nem para o ambiente testado, nem (com
mais razão ainda) para qualquer outro. Nenhuma comunicação do autor, seja no código, nos
comentários, neste README ou em qualquer resposta a issues/discussões, deve ser interpretada
como uma garantia além do que está explicitamente escrito na [Licença](LICENSE) MIT — que é
fornecida "como está", sem garantias de qualquer tipo.

## 📄 Licença
Este projeto está licenciado sob a licença MIT — veja o arquivo [LICENSE](LICENSE) para detalhes.