import os
import time
import subprocess
import sys
import re

# --- Configurações (você pode mudar estes valores) ---
intervalo_criar_arquivo_segundos = 11
intervalo_git_segundos = 11
nome_pasta = "arquivos"
# ----------------------------------------------------

def rodar_comando_git(argumentos, ignorar_erro=False):
    """
    Função para executar comandos git.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    comando = ['git'] + argumentos
    print(f"\n--- Executando: {' '.join(comando)} ---")
    try:
        # A opção 'check=True' irá lançar uma exceção se o comando falhar
        # Usamos try/except para capturar essa exceção e gerenciar o fluxo
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("Saída do comando:")
        print(resultado.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ocorreu um erro ao executar o comando 'git {' '.join(argumentos)}'.")
        print("Mensagem de erro:")
        print(e.stderr)
        if not ignorar_erro:
            # Encerra o script apenas se não for para ignorar o erro
            sys.exit(1)
        return False
    except FileNotFoundError:
        print("Erro: O comando 'git' não foi encontrado. Certifique-se de que o Git está instalado.")
        sys.exit(1)

def encontrar_ultimo_numero_arquivo(pasta):
    """Encontra o número do último arquivo criado na pasta."""
    maior_numero = 0
    padrao = re.compile(r"arquivo(\d+)\.txt")

    if os.path.exists(pasta) and os.path.isdir(pasta):
        for nome_arquivo in os.listdir(pasta):
            correspondencia = padrao.match(nome_arquivo)
            if correspondencia:
                numero = int(correspondencia.group(1))
                if numero > maior_numero:
                    maior_numero = numero
    return maior_numero

def main():
    """Função principal que executa o loop de automação."""
    if not os.path.exists(nome_pasta):
        os.makedirs(nome_pasta)
        print(f"Pasta '{nome_pasta}' criada com sucesso.")
    else:
        print(f"Pasta '{nome_pasta}' já existe. Verificando o último arquivo...")

    contador_arquivos = encontrar_ultimo_numero_arquivo(nome_pasta)
    print(f"Contador de arquivos iniciando em {contador_arquivos + 1}.")

    tempo_ultimo_arquivo = time.time()
    tempo_ultimo_git = time.time()
    
    # Variável para controlar os commits pendentes de push
    commits_pendentes = False

    print("Script de automação iniciado. Pressione Ctrl+C para parar.")

    try:
        while True:
            agora = time.time()

            # Lógica para criar um novo arquivo
            if agora - tempo_ultimo_arquivo >= intervalo_criar_arquivo_segundos:
                contador_arquivos += 1
                nome_arquivo = f"{nome_pasta}/arquivo{contador_arquivos}.txt"
                with open(nome_arquivo, "w") as f:
                    f.write(f"Este é o arquivo número {contador_arquivos}, criado em {time.ctime()}\n")
                print(f"[{time.ctime()}] Arquivo '{nome_arquivo}' criado.")
                tempo_ultimo_arquivo = agora
                commits_pendentes = True # Marca que há novos arquivos para commit

            # Lógica para os comandos Git
            if agora - tempo_ultimo_git >= intervalo_git_segundos:
                if commits_pendentes:
                    print(f"[{time.ctime()}] Iniciando a sequência de comandos Git...")
                    
                    # 1. git add .
                    rodar_comando_git(['add', '.'])
                    
                    # 2. git commit
                    mensagem_commit = f"Arquivo {contador_arquivos} adicionado"
                    if rodar_comando_git(['commit', '-m', mensagem_commit]) == True:
                        commits_pendentes = False
                
                # Loop para tentar o push até que funcione
                while True:
                    # 1. Tenta fazer um 'pull' para evitar divergência de histórico
                    pull_ok = rodar_comando_git(['pull', 'origin', 'main'], ignorar_erro=True)

                    if not pull_ok:
                        print("Erro no 'git pull'. Tentando novamente em 10 segundos...")
                        time.sleep(10)
                        continue # Pula para a próxima tentativa no loop
                    
                    # 2. Tenta fazer o 'push'
                    push_ok = rodar_comando_git(['push', 'origin', 'main'], ignorar_erro=True)
                    
                    if not push_ok:
                        print("Erro no 'git push'. Tentando novamente em 10 segundos...")
                        time.sleep(10)
                        continue # Pula para a próxima tentativa no loop
                    
                    print("Git push realizado com sucesso!")
                    break # Sai do loop de push quando dá certo

                tempo_ultimo_git = agora
            
            # Pausa para evitar que o loop consuma muita CPU
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nScript parado pelo usuário. Adeus!")
        sys.exit(0)

if __name__ == "__main__":
    main()
