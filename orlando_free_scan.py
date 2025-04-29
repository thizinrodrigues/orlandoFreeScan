import tkinter as tk
from tkinter import scrolledtext, filedialog
import threading
import subprocess
import platform
import time
from datetime import datetime, timedelta
import socket

# Variáveis dinâmicas
ips = []
intervalo_entre_testes = 5

# Função de ping
def verificar_ping(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    comando = ["ping", param, "1", ip]
    try:
        resultado = subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
        return resultado.returncode == 0
    except subprocess.TimeoutExpired:
        return None

# Função para obter nome do host
def obter_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "desconhecido"

# Função principal de monitoramento
def monitorar_ips(text_widget, parar_evento, status_label, tempo_label, tempo_execucao_label, nome_relatorio, botao_iniciar, botao_abrir):
    rodada = 1
    total_online = 0
    total_offline = 0
    inicio_monitoramento = time.time()
    nome_arquivo = f"{nome_relatorio}.txt"

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE MONITORAMENTO DE IPs\n")
        f.write(f"Relatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("IPs Monitorados:\n")
        for ip in ips:
            f.write(f"- {ip}\n")
        f.write("\nRESULTADOS:\n\n")

    while not parar_evento.is_set():
        inicio_rodada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_text = f"\n🔁 Rodada {rodada} iniciada - {inicio_rodada}\n"
        status_text += "-" * 60 + "\n"

        online_count = 0
        offline_count = 0
        resultados_rodada = ""

        for ip in ips:
            status_ping = verificar_ping(ip)
            host = obter_hostname(ip)

            if status_ping is None:
                linha = f"⚠️ {ip} ({host}) não respondeu (timeout)"
                offline_count += 1
                total_offline += 1
            elif status_ping:
                linha = f"✅ {ip} ({host}) está ONLINE"
                online_count += 1
                total_online += 1
            else:
                linha = f"❌ {ip} ({host}) está OFFLINE"
                offline_count += 1
                total_offline += 1

            status_text += linha + "\n"
            resultados_rodada += linha + "\n"

        fim_rodada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_text += "-" * 60 + f"\n🔁 Rodada {rodada} finalizada - {fim_rodada}\n"
        status_text += f"📊 Rodada: {online_count} ONLINE | {offline_count} OFFLINE\n"
        status_text += f"📈 Acumulado: {total_online} ONLINE | {total_offline} OFFLINE\n"

        with open(nome_arquivo, "a", encoding="utf-8") as f:
            f.write(f"🕒 Rodada {rodada} - {inicio_rodada}\n{resultados_rodada}\n")

        text_widget.config(state='normal')
        text_widget.insert(tk.END, status_text + "\n")
        text_widget.see(tk.END)
        text_widget.config(state='disabled')

        status_label.config(bg="green" if online_count == len(ips) and len(ips) > 0 else "red")

        tempo_execucao = time.time() - inicio_monitoramento
        tempo_total_formatado = str(timedelta(seconds=int(tempo_execucao)))
        tempo_execucao_label.config(text=f"Tempo total de execução: {tempo_total_formatado}")

        tempo_restante = intervalo_entre_testes - (tempo_execucao % intervalo_entre_testes)
        tempo_restante_formatado = str(timedelta(seconds=int(tempo_restante)))
        tempo_label.config(text=f"Tempo restante para próxima rodada: {tempo_restante_formatado}")

        rodada += 1
        time.sleep(intervalo_entre_testes)

    botao_abrir.config(state=tk.NORMAL)
    botao_iniciar.config(state=tk.NORMAL)


# Interface principal
def iniciar_interface():
    root = tk.Tk()
    root.title("Orlando Free Scan")

    # IPs
    frame_ip = tk.Frame(root)
    frame_ip.pack(pady=5)
    entry_ip = tk.Entry(frame_ip, width=20)
    entry_ip.pack(side=tk.LEFT)

    listbox_ips = tk.Listbox(root, width=30, height=5)
    listbox_ips.pack(pady=5)

    def adicionar_ip():
        ip = entry_ip.get()
        if ip and ip not in ips:
            ips.append(ip)
            listbox_ips.insert(tk.END, ip)
            entry_ip.delete(0, tk.END)

    def remover_ip():
        selecionado = listbox_ips.curselection()
        if selecionado:
            ip_remover = listbox_ips.get(selecionado)
            ips.remove(ip_remover)
            listbox_ips.delete(selecionado)

    tk.Button(frame_ip, text="Adicionar IP", command=adicionar_ip).pack(side=tk.LEFT, padx=2)
    tk.Button(frame_ip, text="Remover IP", command=remover_ip).pack(side=tk.LEFT)

    # Intervalo
    frame_intervalo = tk.Frame(root)
    frame_intervalo.pack()
    tk.Label(frame_intervalo, text="Intervalo entre testes (s):").pack(side=tk.LEFT)
    entry_intervalo = tk.Entry(frame_intervalo, width=5)
    entry_intervalo.insert(0, "5")
    entry_intervalo.pack(side=tk.LEFT)

    # Área de texto
    text_area = scrolledtext.ScrolledText(root, width=80, height=15, state='disabled', font=("Courier", 10))
    text_area.pack(padx=10, pady=10)

    # LED
    status_label = tk.Label(root, text="Status Geral", bg="gray", width=20, height=2)
    status_label.pack(pady=5)

    # Tempo
    tempo_label = tk.Label(root, text="Tempo restante: 00:00:00", font=("Courier", 10))
    tempo_label.pack()
    tempo_execucao_label = tk.Label(root, text="Tempo total: 00:00:00", font=("Courier", 10))
    tempo_execucao_label.pack()

    # Parar
    parar_evento = threading.Event()

    # Nome do relatório
    frame_relatorio = tk.Frame(root)
    frame_relatorio.pack(pady=5)
    tk.Label(frame_relatorio, text="Nome do relatório:").pack(side=tk.LEFT)
    entry_nome_relatorio = tk.Entry(frame_relatorio, width=30)
    entry_nome_relatorio.pack(side=tk.LEFT)

    # Botões que precisam ser acessados por outras funções
    botao_iniciar = tk.Button(root, text="Iniciar Monitoramento")
    botao_iniciar.pack(pady=(5, 2))

    botao_abrir = tk.Button(root, text="Abrir Relatório", state=tk.DISABLED)
    botao_abrir.pack(pady=(2, 5))

    def iniciar_monitoramento():
        nome_relatorio = entry_nome_relatorio.get().strip()
        if not nome_relatorio:
            tk.messagebox.showwarning("Aviso", "Informe um nome para o relatório.")
            return

        parar_evento.clear()
        botao_iniciar.config(state=tk.DISABLED)
        botao_abrir.config(state=tk.DISABLED)

        try:
            intervalo = int(entry_intervalo.get())
        except:
            intervalo = 5

        global intervalo_entre_testes
        intervalo_entre_testes = intervalo

        thread = threading.Thread(
            target=monitorar_ips,
            args=(text_area, parar_evento, status_label, tempo_label, tempo_execucao_label, nome_relatorio, botao_iniciar, botao_abrir),
            daemon=True
        )
        thread.start()

    botao_iniciar.config(command=iniciar_monitoramento)

    def parar_monitoramento():
        parar_evento.set()

    def sair():
        parar_evento.set()
        root.quit()

    def limpar_logs():
        text_area.config(state='normal')
        text_area.delete(1.0, tk.END)
        text_area.config(state='disabled')

    def abrir_relatorio():
        nome = entry_nome_relatorio.get().strip()
        if nome:
            caminho = f"{nome}.txt"
            try:
                subprocess.Popen(["notepad.exe", caminho])
            except:
                tk.messagebox.showerror("Erro", "Não foi possível abrir o relatório.")

    botao_abrir.config(command=abrir_relatorio)

    # Botões adicionais
    tk.Button(root, text="Parar Monitoramento", command=parar_monitoramento).pack(pady=(5, 2))
    tk.Button(root, text="Limpar Logs", command=limpar_logs).pack(pady=(5, 2))
    tk.Button(root, text="Sair", command=sair).pack()

    root.mainloop()


# Executar
if __name__ == "__main__":
    iniciar_interface()
