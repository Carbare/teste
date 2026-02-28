import os
import time
import subprocess
import sys
import re
import shutil

# --- CONFIGURAÇÕES (EDITE AQUI) ---
URL_DO_REPO = "https://github.com/Carbare/teste.git"  # <--- COLOQUE SUA URL AQUI
intervalo_criar_arquivo_segundos = 5   # Reduzi para teste, pode aumentar
intervalo_git_segundos = 10
nome_pasta = "arquivos"
arquivo_ciclos = "contador_ciclos.txt"
LIMITE_ARQUIVOS = 1000  # Limite para disparar o reset
# ----------------------------------------------------

def rodar_comando_git(argumentos, ignorar_erro=False):
    """Executa comandos git e trata erros."""
    comando = ['git'] + argumentos
    print(f"Executando: {' '.join(comando)}")
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        if not ignorar_erro:
            print(f"Erro no git: {e.stderr}")
        return False

def ler_ciclo():
    """Lê o número do ciclo atual."""
    if not os.path.exists(arquivo_ciclos):
        with open(arquivo_ciclos, "w") as f:
            f.write("0")
        return 0
    try:
        with open(arquivo_ciclos, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def atualizar_ciclo(novo_valor):
    """Salva o novo número de ciclo."""
    with open(arquivo_ciclos, "w") as f:
        f.write(str(novo_valor))

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

def resetar_repositorio(ciclo_atual):
    """
    Função Nuclear:
    1. Apaga os arquivos da pasta 'arquivos'.
    2. Apaga a pasta .git (mata o histórico).
    3. Inicia um repo novo e limpo.
    """
    print("\n" + "="*40)
    print(f"LIMITE DE {LIMITE_ARQUIVOS} ATINGIDO! INICIANDO PROTOCOLO DE RESET.")
    print("="*40 + "\n")

    # 1. Limpar arquivos da pasta
    if os.path.exists(nome_pasta):
        shutil.rmtree(nome_pasta)
        os.makedirs(nome_pasta)
    
    # 2. Atualizar contador de ciclos
    novo_ciclo = ciclo_atual + 1
    atualizar_ciclo(novo_ciclo)
    print(f"Ciclo atualizado para: {novo_ciclo}")

    # 3. Deletar a pasta .git (Isso elimina os 5GB de histórico antigo)
    if os.path.exists(".git"):
        shutil.rmtree(".git")
        print("Histórico git (.git) deletado com sucesso.")

    # 4. Recriar o ambiente Git do zero
    rodar_comando_git(['init'])
    rodar_comando_git(['branch', '-m', 'main'])
    rodar_comando_git(['remote', 'add', 'origin', URL_DO_REPO])
    
    # Cria um arquivo de log do ciclo para ter o que commitar
    with open(f"{nome_pasta}/info_ciclo.txt", "w") as f:
        f.write(f"Repositorio resetado. Estamos no Ciclo {novo_ciclo}.\n")
        f.write(f"Data do reset: {time.ctime()}\n")

    rodar_comando_git(['add', '.'])
    rodar_comando_git(['commit', '-m', f'Reset Completo: Inicio do Ciclo {novo_ciclo}'])
    
    # Force push é obrigatório aqui pois o histórico mudou
    print("Forçando push do novo histórico limpo...")
    rodar_comando_git(['push', '-f', 'origin', 'main'])
    
    return 0 # Retorna o contador de arquivos para 0

def main():
    if not os.path.exists(nome_pasta):
        os.makedirs(nome_pasta)

    contador_arquivos = encontrar_ultimo_numero_arquivo(nome_pasta)
    tempo_ultimo_arquivo = time.time()
    tempo_ultimo_git = time.time()
    commits_pendentes = False

    print(f"--- Script Iniciado ---\nArquivos atuais: {contador_arquivos}\nLimite: {LIMITE_ARQUIVOS}")

    try:
        while True:
            agora = time.time()

            # --- VERIFICAÇÃO DE RESET ---
            if contador_arquivos >= LIMITE_ARQUIVOS:
                ciclo = ler_ciclo()
                # Chama a função que limpa tudo e reseta o git
                contador_arquivos = resetar_repositorio(ciclo)
                # Reseta timers para não bugar
                tempo_ultimo_arquivo = time.time()
                tempo_ultimo_git = time.time()
                commits_pendentes = False
                continue # Pula para o próximo loop

            # --- CRIAÇÃO DE ARQUIVO ---
            if agora - tempo_ultimo_arquivo >= intervalo_criar_arquivo_segundos:
                contador_arquivos += 1
                ciclo_atual = ler_ciclo()
                nome_arquivo = f"{nome_pasta}/arquivo{contador_arquivos}.txt"
                
                with open(nome_arquivo, "w") as f:
                    f.write(f"Ciclo: {ciclo_atual}\n")
                    f.write(f"Arquivo: {contador_arquivos}\n")
                    f.write(f"Data: {time.ctime()}\n")
                
                print(f"[{time.ctime()}] + Criado: {nome_arquivo} (Ciclo {ciclo_atual})")
                tempo_ultimo_arquivo = agora
                commits_pendentes = True

            # --- ENVIO GIT ---
            if agora - tempo_ultimo_git >= intervalo_git_segundos:
                if commits_pendentes:
                    print(f"[{time.ctime()}] Sincronizando com GitHub...")
                    
                    rodar_comando_git(['add', '.'])
                    rodar_comando_git(['commit', '-m', f"Add arquivo {contador_arquivos} (Ciclo {ler_ciclo()})"])
                    
                    # Tenta dar push
                    sucesso = False
                    tentativas = 0
                    while not sucesso and tentativas < 3:
                        # Tenta pull antes (com rebase para não criar merge commits sujos)
                        rodar_comando_git(['pull', 'origin', 'main', '--rebase'], ignorar_erro=True)
                        sucesso = rodar_comando_git(['push', 'origin', 'main'], ignorar_erro=True)
                        
                        if not sucesso:
                            print("Falha no push. Tentando novamente em 5s...")
                            time.sleep(5)
                            tentativas += 1
                    
                    if sucesso:
                        print(">>> Push realizado com sucesso!")
                        commits_pendentes = False
                    else:
                        print(">>> Erro crítico: Não foi possível dar push após 3 tentativas.")

                    tempo_ultimo_git = agora
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nScript finalizado.")

if __name__ == "__main__":
    main()
