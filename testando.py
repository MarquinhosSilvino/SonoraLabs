import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import soundfile as sf
import sounddevice as sd

from scipy.signal import resample
import librosa

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SonicLab:

    def __init__(self, root):
        self.root = root
        self.root.title("SonoraLABS | Audio Experimentation")
        self.root.geometry("1100x700")
        self.root.minsize(850, 550)

        # Áudio
        self.audio_original = None
        self.audio_processado = None
        self.taxa = None
        self.caminho = None

        # Gravação
        self.gravando = False
        self.audio_gravado = []
        self.stream = None
        self.taxa_gravacao = 44100

        # Parâmetros dos efeitos
        self.intensidade = tk.DoubleVar(value=5)
        self.pitch = tk.DoubleVar(value=0.7)
        self.niveis = tk.IntVar(value=16)

        # Parâmetros do Delay
        self.delay_tempo = tk.DoubleVar(value=300)
        self.delay_feedback = tk.DoubleVar(value=0.35)
        self.delay_mix = tk.DoubleVar(value=0.35)

        # Parâmetros do oitavador
        self.oitava = tk.StringVar(value="Oitava acima (+12)")
        self.oitava_mix = tk.DoubleVar(value=0.50)

        self.configurar_estilo()
        self.criar_interface()
        self.criar_grafico()

        self.root.protocol("WM_DELETE_WINDOW", self.fechar_aplicacao)

    # =====================================
    # INTERFACE
    # =====================================

    def configurar_estilo(self):
        self.root.configure(bg="#17191f")

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TFrame",
            background="#17191f"
        )

        style.configure(
            "TLabel",
            background="#17191f",
            foreground="#eeeeee",
            font=("Arial", 9)
        )

        style.configure(
            "Title.TLabel",
            font=("Arial", 18, "bold"),
            foreground="#55dfad"
        )

        style.configure(
            "TButton",
            font=("Arial", 8, "bold"),
            padding=(4, 3)
        )

        style.configure(
            "TScale",
            background="#17191f",
            troughcolor="#343943"
        )

    def criar_interface(self):

        # CABEÇALHO
        header = ttk.Frame(self.root, padding=8)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="SONIC LAB",
            style="Title.TLabel"
        ).pack(side="left")

        ttk.Label(
            header,
            text="DIGITAL AUDIO PROCESSOR"
        ).pack(side="right")

        # ARQUIVOS E REPRODUÇÃO
        arquivo_frame = ttk.Frame(self.root, padding=(8, 3))
        arquivo_frame.pack(fill="x")

        ttk.Button(
            arquivo_frame,
            text="CARREGAR SAMPLE",
            command=self.carregar_audio
        ).pack(side="left", padx=2)

        ttk.Button(
            arquivo_frame,
            text="TOCAR ORIGINAL",
            command=lambda: self.tocar("original")
        ).pack(side="left", padx=2)

        ttk.Button(
            arquivo_frame,
            text="TOCAR PROCESSADO",
            command=lambda: self.tocar("processado")
        ).pack(side="left", padx=2)

        ttk.Button(
            arquivo_frame,
            text="LOOP ORIGINAL",
            command=lambda: self.tocar_loop("original")
        ).pack(side="left", padx=2)

        ttk.Button(
            arquivo_frame,
            text="LOOP PROCESSADO",
            command=lambda: self.tocar_loop("processado")
        ).pack(side="left", padx=2)

        ttk.Button(
            arquivo_frame,
            text="PARAR",
            command=self.parar
        ).pack(side="left", padx=2)

        ttk.Button(
            arquivo_frame,
            text="RESETAR",
            command=self.resetar
        ).pack(side="left", padx=2)

        # GRAVAÇÃO
        gravacao_frame = ttk.LabelFrame(
            self.root,
            text="GRAVAÇÃO DE ÁUDIO",
            padding=6
        )
        gravacao_frame.pack(fill="x", padx=8, pady=3)

        ttk.Button(
            gravacao_frame,
            text="GRAVAR MICROFONE",
            command=self.iniciar_gravacao
        ).pack(side="left", padx=2)

        ttk.Button(
            gravacao_frame,
            text="PARAR GRAVAÇÃO",
            command=self.parar_gravacao
        ).pack(side="left", padx=2)

        ttk.Button(
            gravacao_frame,
            text="SALVAR GRAVAÇÃO",
            command=self.salvar_gravacao
        ).pack(side="left", padx=2)

        self.nome_arquivo = ttk.Label(
            self.root,
            text="Nenhum sample carregado",
            padding=5
        )
        self.nome_arquivo.pack(anchor="w", padx=15)

        # GRÁFICOS
        grafico_frame = ttk.Frame(
            self.root,
            padding=5
        )
        grafico_frame.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=3
        )

        self.grafico_frame = grafico_frame

        # EFEITOS
        efeitos = ttk.LabelFrame(
            self.root,
            text="PROCESSAMENTO DE ÁUDIO",
            padding=8
        )
        efeitos.pack(
            fill="x",
            padx=8,
            pady=5
        )

        # DISTORTION
        coluna1 = ttk.Frame(efeitos)
        coluna1.pack(
            side="left",
            expand=True,
            fill="x",
            padx=5
        )

        ttk.Label(
            coluna1,
            text="DISTORTION"
        ).pack()

        ttk.Scale(
            coluna1,
            from_=1,
            to=20,
            variable=self.intensidade,
            orient="horizontal"
        ).pack(fill="x")

        ttk.Label(
            coluna1,
            textvariable=self.intensidade
        ).pack()

        ttk.Button(
            coluna1,
            text="APLICAR",
            command=self.aplicar_distorcao
        ).pack(pady=2)

        # PITCH
        coluna2 = ttk.Frame(efeitos)
        coluna2.pack(
            side="left",
            expand=True,
            fill="x",
            padx=5
        )

        ttk.Label(
            coluna2,
            text="PITCH DOWN / UP"
        ).pack()

        ttk.Scale(
            coluna2,
            from_=0.3,
            to=1.5,
            variable=self.pitch,
            orient="horizontal"
        ).pack(fill="x")

        ttk.Label(
            coluna2,
            textvariable=self.pitch
        ).pack()

        ttk.Button(
            coluna2,
            text="APLICAR",
            command=self.aplicar_pitch
        ).pack(pady=2)

        # BITCRUSHER
        coluna3 = ttk.Frame(efeitos)
        coluna3.pack(
            side="left",
            expand=True,
            fill="x",
            padx=5
        )

        ttk.Label(
            coluna3,
            text="BITCRUSHER"
        ).pack()

        ttk.Scale(
            coluna3,
            from_=2,
            to=64,
            variable=self.niveis,
            orient="horizontal"
        ).pack(fill="x")

        ttk.Label(
            coluna3,
            textvariable=self.niveis
        ).pack()

        ttk.Button(
            coluna3,
            text="APLICAR",
            command=self.aplicar_bitcrusher
        ).pack(pady=2)

        # EFEITOS ADICIONAIS
        adicionais = ttk.Frame(efeitos)
        adicionais.pack(fill="x", pady=4)

        ttk.Button(
            adicionais,
            text="REVERSE",
            command=self.aplicar_reverse
        ).pack(side="left", padx=2)

        ttk.Button(
            adicionais,
            text="EXPORTAR WAV",
            command=self.exportar
        ).pack(side="right", padx=5)

        # NOVOS EFEITOS: DELAY E OITAVADOR
        novos_efeitos = ttk.Frame(efeitos)
        novos_efeitos.pack(fill="x", pady=5)

        # DELAY
        delay_frame = ttk.LabelFrame(
            novos_efeitos,
            text="DELAY",
            padding=6
        )
        delay_frame.pack(
            side="left",
            expand=True,
            fill="both",
            padx=4
        )

        ttk.Label(delay_frame, text="Tempo (ms)").pack()
        ttk.Scale(
            delay_frame,
            from_=50,
            to=1000,
            variable=self.delay_tempo,
            orient="horizontal"
        ).pack(fill="x")
        ttk.Label(
            delay_frame,
            textvariable=self.delay_tempo
        ).pack()

        ttk.Label(delay_frame, text="Feedback / repetições").pack()
        ttk.Scale(
            delay_frame,
            from_=0,
            to=0.90,
            variable=self.delay_feedback,
            orient="horizontal"
        ).pack(fill="x")
        ttk.Label(
            delay_frame,
            textvariable=self.delay_feedback
        ).pack()

        ttk.Label(delay_frame, text="Mix (áudio original / eco)").pack()
        ttk.Scale(
            delay_frame,
            from_=0,
            to=1,
            variable=self.delay_mix,
            orient="horizontal"
        ).pack(fill="x")
        ttk.Label(
            delay_frame,
            textvariable=self.delay_mix
        ).pack()

        ttk.Button(
            delay_frame,
            text="APLICAR DELAY",
            command=self.aplicar_delay
        ).pack(pady=3)

        # OITAVADOR
        oitava_frame = ttk.LabelFrame(
            novos_efeitos,
            text="OITAVADOR",
            padding=6
        )
        oitava_frame.pack(
            side="left",
            expand=True,
            fill="both",
            padx=4
        )

        ttk.Label(
            oitava_frame,
            text="Tom da camada adicional"
        ).pack()

        ttk.Combobox(
            oitava_frame,
            textvariable=self.oitava,
            values=[
                "Oitava abaixo (-12)",
                "Oitava acima (+12)",
                "Duas oitavas abaixo (-24)",
                "Duas oitavas acima (+24)"
            ],
            state="readonly"
        ).pack(fill="x", pady=3)

        ttk.Label(
            oitava_frame,
            text="Mix da oitava"
        ).pack()

        ttk.Scale(
            oitava_frame,
            from_=0,
            to=1,
            variable=self.oitava_mix,
            orient="horizontal"
        ).pack(fill="x")

        ttk.Label(
            oitava_frame,
            textvariable=self.oitava_mix
        ).pack()

        ttk.Button(
            oitava_frame,
            text="APLICAR OITAVADOR",
            command=self.aplicar_oitavador
        ).pack(pady=3)

        # STATUS
        self.status = ttk.Label(
            self.root,
            text="Aguardando sample...",
            padding=5
        )
        self.status.pack(fill="x")

    # =====================================
    # GRÁFICOS
    # =====================================

    def criar_grafico(self):

        self.figura = Figure(
            figsize=(10, 4),
            dpi=100,
            facecolor="#17191f"
        )

        self.ax_original = self.figura.add_subplot(211)
        self.ax_processado = self.figura.add_subplot(212)

        self.configurar_eixos()

        self.figura.tight_layout(pad=1)

        self.canvas = FigureCanvasTkAgg(
            self.figura,
            master=self.grafico_frame
        )

        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        self.canvas.draw()

    def configurar_eixos(self):

        for ax, titulo in [
            (self.ax_original, "ÁUDIO ORIGINAL"),
            (self.ax_processado, "ÁUDIO PROCESSADO")
        ]:

            ax.set_facecolor("#222630")

            ax.set_title(
                titulo,
                color="#55dfad",
                fontsize=9
            )

            ax.set_xlabel(
                "Tempo (segundos)",
                color="white"
            )

            ax.set_ylabel(
                "Amplitude",
                color="white"
            )

            ax.tick_params(colors="white")
            ax.grid(True, alpha=0.15)

            for spine in ax.spines.values():
                spine.set_color("#444b58")

    def atualizar_grafico(self):

        self.ax_original.clear()
        self.ax_processado.clear()

        self.configurar_eixos()

        if self.audio_original is not None:
            self.desenhar_audio(
                self.ax_original,
                self.audio_original
            )

        if self.audio_processado is not None:
            self.desenhar_audio(
                self.ax_processado,
                self.audio_processado
            )

        self.figura.tight_layout(pad=1)
        self.canvas.draw_idle()

    def desenhar_audio(self, eixo, audio):

        sinal = (
            audio.mean(axis=1)
            if audio.ndim == 2
            else audio
        )

        passo = max(1, len(sinal) // 30000)
        sinal = sinal[::passo]

        tempo = np.arange(len(sinal)) * passo / self.taxa

        eixo.plot(
            tempo,
            sinal,
            color="#55dfad",
            linewidth=0.6
        )

    # =====================================
    # CARREGAMENTO DE ÁUDIO
    # =====================================

    def carregar_audio(self):

        caminho = filedialog.askopenfilename(
            title="Selecione um sample",
            filetypes=[
                ("Arquivos de áudio", "*.wav *.flac *.ogg *.aiff"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if not caminho:
            return

        try:
            self.parar()

            self.status.config(text="Carregando áudio...")
            self.root.update_idletasks()

            audio, taxa = sf.read(
                caminho,
                dtype="float32"
            )

            if audio.size == 0:
                raise ValueError("O arquivo está vazio.")

            self.audio_original = audio
            self.audio_processado = audio.copy()
            self.taxa = taxa
            self.caminho = caminho

            duracao = len(audio) / taxa

            self.nome_arquivo.config(
                text=caminho.split("/")[-1].split("\\")[-1]
            )

            canais = 1 if audio.ndim == 1 else audio.shape[1]

            self.status.config(
                text=f"Duração: {duracao:.2f}s | "
                     f"Sample Rate: {taxa} Hz | "
                     f"Canais: {canais}"
            )

            self.atualizar_grafico()

        except Exception as erro:

            messagebox.showerror(
                "Erro ao carregar",
                str(erro)
            )

    # =====================================
    # GRAVAÇÃO PELO MICROFONE
    # =====================================

    def iniciar_gravacao(self):

        if self.gravando:
            return

        try:
            self.parar()

            self.audio_gravado = []
            self.gravando = True

            def callback(indata, frames, time, status):

                if status:
                    print(status)

                if self.gravando:
                    self.audio_gravado.append(
                        indata.copy()
                    )

            self.stream = sd.InputStream(
                samplerate=self.taxa_gravacao,
                channels=1,
                dtype="float32",
                callback=callback
            )

            self.stream.start()

            self.status.config(
                text="GRAVANDO MICROFONE..."
            )

        except Exception as erro:

            self.gravando = False

            if self.stream is not None:
                self.stream.close()
                self.stream = None

            messagebox.showerror(
                "Erro na gravação",
                str(erro)
            )

    def parar_gravacao(self):

        if not self.gravando:
            return

        self.gravando = False

        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            if not self.audio_gravado:
                self.status.config(
                    text="Nenhum áudio foi capturado."
                )
                return

            # Junta todos os blocos capturados
            audio = np.concatenate(
                self.audio_gravado,
                axis=0
            )

            self.audio_gravado = audio

            # A gravação passa a ser o áudio principal
            self.audio_original = audio
            self.audio_processado = audio.copy()
            self.taxa = self.taxa_gravacao
            self.caminho = None

            duracao = len(audio) / self.taxa

            self.nome_arquivo.config(
                text="Gravação realizada pelo microfone"
            )

            self.atualizar_grafico()

            self.status.config(
                text=f"Gravação finalizada | Duração: {duracao:.2f}s"
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro ao finalizar gravação",
                str(erro)
            )

    def salvar_gravacao(self):

        if isinstance(self.audio_gravado, list) or self.audio_gravado is None:
            messagebox.showwarning(
                "Atenção",
                "Faça uma gravação primeiro."
            )
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("Arquivo WAV", "*.wav")],
            title="Salvar gravação"
        )

        if not caminho:
            return

        try:
            sf.write(
                caminho,
                self.audio_gravado,
                self.taxa_gravacao,
                subtype="PCM_16"
            )

            messagebox.showinfo(
                "Sucesso",
                f"Gravação salva em:\n{caminho}"
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro ao salvar",
                str(erro)
            )

    # =====================================
    # REPRODUÇÃO E LOOP
    # =====================================

    def tocar(self, tipo):

        audio = (
            self.audio_original
            if tipo == "original"
            else self.audio_processado
        )

        if audio is None:
            messagebox.showwarning(
                "Atenção",
                "Carregue ou grave um áudio primeiro."
            )
            return

        try:
            self.parar()

            sd.play(
                audio,
                self.taxa
            )

            self.status.config(
                text=f"Reproduzindo: {tipo}"
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro de reprodução",
                str(erro)
            )

    def tocar_loop(self, tipo):

        audio = (
            self.audio_original
            if tipo == "original"
            else self.audio_processado
        )

        if audio is None:
            messagebox.showwarning(
                "Atenção",
                "Carregue ou grave um áudio primeiro."
            )
            return

        try:
            self.parar()

            sd.play(
                audio,
                self.taxa,
                loop=True
            )

            self.status.config(
                text=f"LOOP ATIVO: {tipo}"
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro no loop",
                str(erro)
            )

    def parar(self):

        sd.stop()

        if not self.gravando:
            self.status.config(
                text="Reprodução interrompida."
            )

    # =====================================
    # PROCESSAMENTO
    # =====================================

    def verificar_audio(self):

        if self.audio_processado is None:
            messagebox.showwarning(
                "Atenção",
                "Carregue ou grave um áudio primeiro."
            )
            return False

        return True

    def atualizar_resultado(self, resultado, nome):

        self.audio_processado = resultado.astype(
            np.float32
        )

        self.atualizar_grafico()

        self.status.config(
            text=f"Efeito aplicado: {nome}"
        )

    # DISTORÇÃO
    def aplicar_distorcao(self):

        if not self.verificar_audio():
            return

        intensidade = self.intensidade.get()
        audio = self.audio_processado

        resultado = np.tanh(
            audio * intensidade
        )

        pico = np.max(np.abs(resultado))

        if pico > 0:
            resultado = resultado / pico * 0.95

        self.atualizar_resultado(
            resultado,
            "Distorção"
        )

    # REVERSE
    def aplicar_reverse(self):

        if not self.verificar_audio():
            return

        resultado = self.audio_processado[::-1].copy()

        self.atualizar_resultado(
            resultado,
            "Reverse"
        )

    # PITCH
    def aplicar_pitch(self):

        if not self.verificar_audio():
            return

        fator = self.pitch.get()
        audio = self.audio_processado

        novo_tamanho = max(
            1,
            int(len(audio) / fator)
        )

        resultado = resample(
            audio,
            novo_tamanho,
            axis=0
        )

        self.atualizar_resultado(
            resultado,
            "Pitch"
        )

    # BITCRUSHER
    def aplicar_bitcrusher(self):

        if not self.verificar_audio():
            return

        niveis = int(self.niveis.get())

        audio = np.clip(
            self.audio_processado,
            -1,
            1
        )

        resultado = (
            np.round(audio * niveis) / niveis
        )

        self.atualizar_resultado(
            resultado,
            "Bitcrusher"
        )

    # =====================================
    # DELAY
    # =====================================

    def aplicar_delay(self):

        if not self.verificar_audio():
            return

        audio = self.audio_processado.astype(np.float32)

        tempo_ms = self.delay_tempo.get()
        feedback = self.delay_feedback.get()
        mix = self.delay_mix.get()

        atraso = int(self.taxa * tempo_ms / 1000)

        if atraso <= 0 or atraso >= len(audio):
            messagebox.showwarning(
                "Delay",
                "O tempo do delay é maior que a duração do áudio."
            )
            return

        # Mantém o tamanho original do áudio.
        # Cada repetição é mais baixa conforme o feedback.
        resultado = audio.copy()
        eco = audio.copy()

        for _ in range(8):
            eco = eco * feedback

            if audio.ndim == 1:
                resultado[atraso:] += eco[:-atraso] * mix
            else:
                resultado[atraso:, :] += eco[:-atraso, :] * mix

            # Desloca o eco para a próxima repetição
            eco = np.concatenate(
                [np.zeros_like(eco[:atraso]), eco[:-atraso]],
                axis=0
            )

        pico = np.max(np.abs(resultado))
        if pico > 1:
            resultado = resultado / pico * 0.98

        self.atualizar_resultado(
            resultado,
            f"Delay ({tempo_ms:.0f} ms)"
        )

    # =====================================
    # OITAVADOR
    # =====================================

    def aplicar_oitavador(self):

        if not self.verificar_audio():
            return

        audio = self.audio_processado.astype(np.float32)

        opcoes = {
            "Oitava abaixo (-12)": -12,
            "Oitava acima (+12)": 12,
            "Duas oitavas abaixo (-24)": -24,
            "Duas oitavas acima (+24)": 24
        }

        semitons = opcoes.get(self.oitava.get(), 12)
        mix = self.oitava_mix.get()

        try:
            # Pitch shift mantém a duração aproximada do áudio.
            if audio.ndim == 1:
                camada_oitava = librosa.effects.pitch_shift(
                    y=audio,
                    sr=int(self.taxa),
                    n_steps=semitons
                )
            else:
                canais = []
                for canal in range(audio.shape[1]):
                    canais.append(
                        librosa.effects.pitch_shift(
                            y=audio[:, canal],
                            sr=int(self.taxa),
                            n_steps=semitons
                        )
                    )
                camada_oitava = np.column_stack(canais)

            # Mistura o som original com a camada em outra oitava.
            resultado = (
                audio * (1 - mix) +
                camada_oitava * mix
            )

            pico = np.max(np.abs(resultado))
            if pico > 1:
                resultado = resultado / pico * 0.98

            self.atualizar_resultado(
                resultado,
                f"Oitavador ({semitons:+d} semitons)"
            )

        except Exception as erro:
            messagebox.showerror(
                "Erro no oitavador",
                f"Não foi possível aplicar o efeito.\n{erro}"
            )

    # =====================================
    # RESET E EXPORTAÇÃO
    # =====================================

    def resetar(self):

        if self.audio_original is None:
            return

        self.parar()

        self.audio_processado = self.audio_original.copy()

        self.atualizar_grafico()

        self.status.config(
            text="Áudio restaurado ao original."
        )

    def exportar(self):

        if not self.verificar_audio():
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV", "*.wav")],
            title="Exportar áudio processado"
        )

        if not caminho:
            return

        try:
            sf.write(
                caminho,
                self.audio_processado,
                self.taxa,
                subtype="PCM_16"
            )

            messagebox.showinfo(
                "Exportação concluída",
                f"Arquivo salvo em:\n{caminho}"
            )

            self.status.config(
                text="Áudio exportado com sucesso."
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro na exportação",
                str(erro)
            )

    # =====================================
    # ENCERRAMENTO
    # =====================================

    def fechar_aplicacao(self):

        self.gravando = False

        try:
            sd.stop()

            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
                self.stream = None

        except Exception:
            pass

        self.root.destroy()


# =====================================
# INICIALIZAÇÃO
# =====================================

if __name__ == "__main__":

    root = tk.Tk()

    app = SonicLab(root)

    root.mainloop()
