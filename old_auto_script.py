import os
import time
import subprocess
import sys
import re

# --- Configurações (você pode mudar estes valores) ---
intervalo_criar_arquivo_segundos = 20 # 1 minuto
intervalo_git_segundos = 20          # 2 minutos
nome_pasta = "arquivos"
# ----------------------------------------------------

def rodar_comando_git(argumentos):
    """Função auxiliar para executar comandos git e verificar o resultado."""
    comando = ['git'] + argumentos
    print(f"\n--- Executando: {' '.join(comando)} ---")
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("Saída do comando:")
        print(resultado.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Ocorreu um erro ao executar o comando 'git {' '.join(argumentos)}'.")
        print("Mensagem de erro:")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Erro: O comando 'git' não foi encontrado. Certifique-se de que o Git está instalado e no seu PATH.")
        sys.exit(1)

def encontrar_ultimo_numero_arquivo(pasta):
    """Encontra o número do último arquivo criado na pasta."""
    maior_numero = 0
    # Expressão regular para encontrar arquivos no formato "arquivo<numero>.txt"
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
    # Garante que a pasta de arquivos existe
    if not os.path.exists(nome_pasta):
        os.makedirs(nome_pasta)
        print(f"Pasta '{nome_pasta}' criada com sucesso.")
    else:
        print(f"Pasta '{nome_pasta}' já existe. Verificando o último arquivo...")

    # Encontra o último arquivo para continuar a partir dele
    contador_arquivos = encontrar_ultimo_numero_arquivo(nome_pasta)
    print(f"Contador de arquivos iniciando em {contador_arquivos + 1}.")

    tempo_ultimo_arquivo = time.time()
    tempo_ultimo_git = time.time()

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

            # Lógica para os comandos Git
            if agora - tempo_ultimo_git >= intervalo_git_segundos:
                print(f"[{time.ctime()}] Iniciando a sequência de comandos Git...")
                
                # 1. git add .
                rodar_comando_git(['add', '.'])
                
                # 2. git commit
                mensagem_commit = f"Arquivo {contador_arquivos} adicionado"
                # O commit agora recebe a mensagem como um único item na lista
                rodar_comando_git(['commit', '-m', mensagem_commit])
                
                # 3. git push
                rodar_comando_git(['push', 'origin', 'main'])
                
                tempo_ultimo_git = agora
            
            # Pausa para evitar que o loop consuma muita CPU
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nScript parado pelo usuário. Adeus!")
        sys.exit(0)

if __name__ == "__main__":
    main()
