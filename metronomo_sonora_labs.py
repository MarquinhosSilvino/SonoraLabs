import tkinter as tk
from tkinter import ttk
import threading
import time
import winsound


class Metronomo:
    BPM_MIN = 30
    BPM_MAX = 300

    # Estados das batidas: normal -> silêncio -> acentuada -> normal
    ESTADOS = ("normal", "silencio", "acentuada")
    CORES = {
        "normal": "#999999",
        "silencio": "#ffffff",
        "acentuada": "#e53935",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Sonora Labs - Metrônomo")
        self.root.geometry("720x470")
        self.root.minsize(560, 400)

        self.bpm = tk.IntVar(value=120)
        self.quantidade = tk.IntVar(value=4)
        self.estados = ["normal"] * 4

        self.executando = False
        self.proximo_tempo = None
        self.indice_batida = 0
        self.after_id = None
        self.botoes_batida = []

        self._montar_interface()
        self._atualizar_batidas()

        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

    def _montar_interface(self):
        principal = ttk.Frame(self.root, padding=20)
        principal.pack(fill="both", expand=True)

        ttk.Label(
            principal,
            text="METRÔNOMO",
            font=("Arial", 18, "bold")
        ).pack(pady=(0, 18))

        # Área do BPM
        linha_bpm = ttk.Frame(principal)
        linha_bpm.pack(fill="x", pady=5)

        ttk.Button(
            linha_bpm, text="−", width=4, command=lambda: self.alterar_bpm(-1)
        ).pack(side="left")

        self.lbl_bpm = ttk.Label(
            linha_bpm, text="120 BPM", font=("Arial", 25, "bold"), width=12,
            anchor="center"
        )
        self.lbl_bpm.pack(side="left", expand=True)

        ttk.Button(
            linha_bpm, text="+", width=4, command=lambda: self.alterar_bpm(1)
        ).pack(side="right")

        # Controle deslizante
        self.slider = ttk.Scale(
            principal,
            from_=self.BPM_MIN,
            to=self.BPM_MAX,
            orient="horizontal",
            command=self._ao_mover_slider
        )
        self.slider.set(self.bpm.get())
        self.slider.pack(fill="x", pady=(12, 3))

        faixa = ttk.Frame(principal)
        faixa.pack(fill="x")
        ttk.Label(faixa, text="30 BPM").pack(side="left")
        ttk.Label(faixa, text="300 BPM").pack(side="right")

        # Quantidade de batidas
        linha_quantidade = ttk.Frame(principal)
        linha_quantidade.pack(pady=(24, 12))

        ttk.Label(
            linha_quantidade, text="Número de batidas (1 a 16):"
        ).pack(side="left", padx=(0, 10))

        self.spin_batidas = ttk.Spinbox(
            linha_quantidade,
            from_=1,
            to=16,
            width=5,
            textvariable=self.quantidade,
            command=self._alterar_quantidade
        )
        self.spin_batidas.pack(side="left")
        self.spin_batidas.bind("<Return>", self._alterar_quantidade_evento)
        self.spin_batidas.bind("<FocusOut>", self._alterar_quantidade_evento)

        # Grade de batidas
        self.area_batidas = ttk.Frame(principal)
        self.area_batidas.pack(fill="x", pady=12)

        ttk.Label(
            principal,
            text="Clique em cada quadrado para alternar: normal → silêncio → acentuada",
            wraplength=650,
            justify="center"
        ).pack(pady=(4, 14))

        # Play e pause
        controles = ttk.Frame(principal)
        controles.pack(pady=8)

        self.btn_play = ttk.Button(
            controles, text="▶ Play", width=14, command=self.play
        )
        self.btn_play.pack(side="left", padx=8)

        self.btn_pause = ttk.Button(
            controles, text="Ⅱ Pause", width=14, command=self.pause,
            state="disabled"
        )
        self.btn_pause.pack(side="left", padx=8)

        # Legenda
        legenda = ttk.Frame(principal)
        legenda.pack(pady=(22, 0))

        self._item_legenda(legenda, "Silêncio", "#ffffff")
        self._item_legenda(legenda, "Acentuada", "#e53935")
        self._item_legenda(legenda, "Normal", "#999999")

    def _item_legenda(self, parent, texto, cor):
        item = ttk.Frame(parent)
        item.pack(side="left", padx=12)

        amostra = tk.Label(
            item, width=2, height=1, bg=cor,
            relief="solid", borderwidth=1
        )
        amostra.pack(side="left", padx=(0, 5))
        ttk.Label(item, text=texto).pack(side="left")

    def _atualizar_bpm(self):
        valor = max(self.BPM_MIN, min(self.BPM_MAX, int(self.bpm.get())))
        self.bpm.set(valor)
        self.lbl_bpm.config(text=f"{valor} BPM")
        self.slider.set(valor)

    def alterar_bpm(self, passo):
        self.bpm.set(max(self.BPM_MIN, min(self.BPM_MAX, self.bpm.get() + passo)))
        self._atualizar_bpm()

    def _ao_mover_slider(self, valor):
        self.bpm.set(max(self.BPM_MIN, min(self.BPM_MAX, round(float(valor)))))
        self.lbl_bpm.config(text=f"{self.bpm.get()} BPM")

    def _alterar_quantidade_evento(self, _evento=None):
        self._alterar_quantidade()

    def _alterar_quantidade(self):
        try:
            nova_quantidade = int(self.quantidade.get())
        except (ValueError, tk.TclError):
            return

        nova_quantidade = max(1, min(16, nova_quantidade))
        self.quantidade.set(nova_quantidade)

        # Mantém os estados já configurados quando a quantidade muda.
        if nova_quantidade > len(self.estados):
            self.estados.extend(["normal"] * (nova_quantidade - len(self.estados)))
        else:
            self.estados = self.estados[:nova_quantidade]

        self.indice_batida = 0
        self._atualizar_batidas()

    def _atualizar_batidas(self):
        for widget in self.area_batidas.winfo_children():
            widget.destroy()

        self.botoes_batida = []
        quantidade = self.quantidade.get()

        for i in range(quantidade):
            botao = tk.Button(
                self.area_batidas,
                text=str(i + 1),
                width=4,
                height=2,
                bg=self.CORES[self.estados[i]],
                activebackground=self.CORES[self.estados[i]],
                relief="solid",
                borderwidth=1,
                command=lambda indice=i: self.alternar_estado(indice)
            )
            # Distribui os quadrados em duas linhas, como no esboço.
            botao.grid(row=i // 8, column=i % 8, padx=5, pady=7, sticky="nsew")
            self.botoes_batida.append(botao)

        for coluna in range(8):
            self.area_batidas.grid_columnconfigure(coluna, weight=1)

    def alternar_estado(self, indice):
        atual = self.estados[indice]
        proximo = self.ESTADOS[(self.ESTADOS.index(atual) + 1) % len(self.ESTADOS)]
        self.estados[indice] = proximo

        botao = self.botoes_batida[indice]
        botao.config(
            bg=self.CORES[proximo],
            activebackground=self.CORES[proximo]
        )

    def play(self):
        if self.executando:
            return

        self.executando = True
        self.btn_play.config(state="disabled")
        self.btn_pause.config(state="normal")

        # Começa imediatamente pela primeira batida.
        self.indice_batida = 0
        self._marcar_e_tocar()
        self._agendar_proxima()

    def pause(self):
        self.executando = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.btn_play.config(state="normal")
        self.btn_pause.config(state="disabled")
        self._limpar_destaque()

    def _agendar_proxima(self):
        if not self.executando:
            return

        intervalo_ms = int(60000 / self.bpm.get())
        self.after_id = self.root.after(intervalo_ms, self._marcar_e_tocar)

    def _marcar_e_tocar(self):
        if not self.executando:
            return

        self._limpar_destaque()

        estado = self.estados[self.indice_batida]
        botao = self.botoes_batida[self.indice_batida]

        # Destaca temporariamente a batida que está sendo executada.
        botao.config(relief="solid", borderwidth=4)

        if estado == "normal":
            self._tocar_som(660)
        elif estado == "acentuada":
            self._tocar_som(1000)
        # No estado "silencio", não toca som.

        self.indice_batida = (self.indice_batida + 1) % self.quantidade.get()
        self._agendar_proxima()

    def _limpar_destaque(self):
        for botao in self.botoes_batida:
            botao.config(relief="solid", borderwidth=1)

    def _tocar_som(self, frequencia):
        if winsound:
            # Beep curto: frequência maior para a batida acentuada.
            threading.Thread(
                target=winsound.Beep,
                args=(frequencia, 45),
                daemon=True
            ).start()
        else:
            # Alternativa simples em sistemas sem winsound.
            self.root.bell()

    def fechar(self):
        self.pause()
        self.root.destroy()


if __name__ == "__main__":
    janela = tk.Tk()
    app = Metronomo(janela)
    janela.mainloop()
