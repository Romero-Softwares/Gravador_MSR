import os
import sys


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON_CANDIDATES = (
    os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe"),
    os.path.join(PROJECT_DIR, "venv", "Scripts", "python.exe"),
)


def garantir_ambiente_virtual():
    if getattr(sys, "frozen", False):
        return

    python_atual = os.path.normcase(os.path.abspath(sys.executable))

    for python_venv in VENV_PYTHON_CANDIDATES:
        if os.path.exists(python_venv):
            python_venv_absoluto = os.path.normcase(os.path.abspath(python_venv))
            if python_atual != python_venv_absoluto:
                os.execv(python_venv, [python_venv, *sys.argv])
            return

    usando_venv = (
        hasattr(sys, "real_prefix")
        or getattr(sys, "base_prefix", sys.prefix) != sys.prefix
    )
    if usando_venv and os.path.commonpath([PROJECT_DIR, sys.prefix]) == PROJECT_DIR:
        return

    print("ERRO: ambiente virtual do projeto nao encontrado.")
    print("Crie ou restaure uma pasta .venv ou venv dentro do projeto.")
    sys.exit(1)


garantir_ambiente_virtual()

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox

from modules.app_config import (
    DEFAULT_AUDIO_RATE,
    DEFAULT_TARGET_FPS,
    FFMPEG_PATH,
    get_default_output_dir,
    get_temp_paths,
    resource_path,
)
from modules.recorder_engine import RecorderEngine


os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH


class GravadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Merotec Screen Recorder")
        largura_janela = 540
        altura_janela = min(630, self.winfo_screenheight() - 80)
        self.geometry(f"{largura_janela}x{altura_janela}")
        self.minsize(500, 560)
        self.resizable(False, False)

        self.camera_window = None
        self.camera_label = None
        self.camera_capture = None
        self.camera_photo = None
        self.camera_preview_running = False
        self.camera_overlay_position = None
        self.camera_drag_offset = (0, 0)

        try:
            self.iconbitmap(resource_path("icone.ico"))
        except Exception as error:
            print(f"Erro ao carregar ícone da janela: {error}")

        ctk.set_appearance_mode("dark")

        self.diretorio_destino = get_default_output_dir()
        temp_paths = get_temp_paths()

        self.recorder = RecorderEngine(
            output_dir=self.diretorio_destino,
            video_temp=temp_paths["video"],
            audio_temp=temp_paths["audio"],
            audio_rate=DEFAULT_AUDIO_RATE,
            target_fps=DEFAULT_TARGET_FPS,
            status_callback=self.atualizar_status,
            finished_callback=self.finalizar_interface,
        )

        self.criar_interface()

    def criar_interface(self):
        self.configure(fg_color="#0f172a")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=16)

        self.header_frame = ctk.CTkFrame(
            self.container,
            fg_color="#111827",
            corner_radius=22,
            border_width=1,
            border_color="#1f2937",
        )
        self.header_frame.pack(fill="x", pady=(0, 12))

        self.btn_ajuda = ctk.CTkButton(
            self.header_frame,
            text="?",
            command=self.mostrar_ajuda,
            width=32,
            height=32,
            corner_radius=16,
            fg_color="#334155",
            hover_color="#475569",
            font=("Arial", 16, "bold"),
        )
        self.btn_ajuda.place(relx=1.0, x=-14, y=14, anchor="ne")

        self.label = ctk.CTkLabel(
            self.header_frame,
            text="Merotec Screen Recorder",
            font=("Arial", 23, "bold"),
            text_color="#f8fafc",
        )
        self.label.pack(pady=(16, 2))

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Grave tela, áudio e câmera com controles simples.",
            font=("Arial", 13),
            text_color="#94a3b8",
        )
        self.subtitle_label.pack(pady=(0, 16))

        self.frame_pasta = ctk.CTkFrame(
            self.container,
            fg_color="#111827",
            corner_radius=18,
            border_width=1,
            border_color="#1f2937",
        )
        self.frame_pasta.pack(fill="x", pady=(0, 10))
        self.frame_pasta.grid_columnconfigure(1, weight=1)

        self.pasta_titulo = ctk.CTkLabel(
            self.frame_pasta,
            text="Destino da gravação",
            font=("Arial", 15, "bold"),
            text_color="#e5e7eb",
        )
        self.pasta_titulo.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 4))

        self.btn_pasta = ctk.CTkButton(
            self.frame_pasta,
            text="Escolher pasta",
            command=self.escolher_pasta,
            width=130,
            height=38,
            corner_radius=12,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
        )
        self.btn_pasta.grid(row=1, column=0, padx=(18, 10), pady=(6, 18), sticky="w")

        self.label_caminho = ctk.CTkLabel(
            self.frame_pasta,
            text=self.diretorio_destino,
            font=("Arial", 11),
            text_color="#cbd5e1",
            wraplength=330,
            justify="left",
            anchor="w",
        )
        self.label_caminho.grid(row=1, column=1, padx=(0, 18), pady=(6, 18), sticky="ew")

        self.frame_opcoes = ctk.CTkFrame(
            self.container,
            fg_color="#111827",
            corner_radius=18,
            border_width=1,
            border_color="#1f2937",
        )
        self.frame_opcoes.pack(fill="x", pady=(0, 10))

        self.opcoes_titulo = ctk.CTkLabel(
            self.frame_opcoes,
            text="Modo de captura",
            font=("Arial", 15, "bold"),
            text_color="#e5e7eb",
        )
        self.opcoes_titulo.pack(anchor="w", padx=18, pady=(16, 8))

        self.camera_var = ctk.BooleanVar(value=False)
        self.checkbox_camera = ctk.CTkCheckBox(
            self.frame_opcoes,
            text="Adicionar câmera sobre a gravação da tela",
            variable=self.camera_var,
            command=self.alternar_preview_camera,
            font=("Arial", 13),
            text_color="#d1d5db",
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
        )
        self.checkbox_camera.pack(anchor="w", padx=18, pady=7)

        self.camera_fullscreen_var = ctk.BooleanVar(value=False)
        self.checkbox_camera_fullscreen = ctk.CTkCheckBox(
            self.frame_opcoes,
            text="Gravar somente a câmera em tela cheia",
            variable=self.camera_fullscreen_var,
            command=self.alternar_modo_camera_cheia,
            font=("Arial", 13),
            text_color="#d1d5db",
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6,
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
        )
        self.checkbox_camera_fullscreen.pack(anchor="w", padx=18, pady=(7, 16))

        self.frame_controles = ctk.CTkFrame(
            self.container,
            fg_color="#111827",
            corner_radius=18,
            border_width=1,
            border_color="#1f2937",
        )
        self.frame_controles.pack(fill="x", pady=(0, 10))

        self.controles_titulo = ctk.CTkLabel(
            self.frame_controles,
            text="Controles",
            font=("Arial", 15, "bold"),
            text_color="#e5e7eb",
        )
        self.controles_titulo.pack(anchor="w", padx=18, pady=(16, 8))

        self.btn_alternar_tela = ctk.CTkButton(
            self.frame_controles,
            text="🖥️ Desativar captura da tela",
            command=self.alternar_captura_tela,
            state="disabled",
            height=40,
            corner_radius=12,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
        )
        self.btn_alternar_tela.pack(fill="x", padx=18, pady=(0, 12))

        self.btn_gravar = ctk.CTkButton(
            self.frame_controles,
            text="🔴 Iniciar Gravação",
            fg_color="#16a34a",
            hover_color="#15803d",
            height=48,
            corner_radius=16,
            font=("Arial", 17, "bold"),
            command=self.alternar_gravacao,
        )
        self.btn_gravar.pack(fill="x", padx=18, pady=(0, 18))

        self.status_card = ctk.CTkFrame(
            self.container,
            fg_color="#020617",
            corner_radius=16,
            border_width=1,
            border_color="#1e293b",
        )
        self.status_card.pack(fill="x")
        self.status_card.configure(height=76)
        self.status_card.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="Status: Pronto para gravar",
            text_color="#94a3b8",
            font=("Arial", 13, "bold"),
            wraplength=440,
            anchor="center",
            justify="center",
        )
        self.status_label.pack(fill="both", expand=True, padx=16, pady=12)

    def mostrar_ajuda(self):
        mensagem = (
            "Como usar o Merotec Screen Recorder:\n\n"
            "1. Escolha a pasta onde o vídeo será salvo.\n"
            "2. Marque 'Adicionar câmera' para gravar a tela com a câmera por cima.\n"
            "3. Arraste a janela da câmera para definir a posição dela na gravação.\n"
            "4. Marque 'Gravar somente a câmera' para capturar apenas a câmera em tela cheia.\n"
            "5. Clique em 'Iniciar Gravação' para começar e em 'Parar Gravação' para finalizar.\n"
            "6. Durante a gravação, use o botão de captura da tela para ativar ou desativar a tela.\n\n"
            "Ao finalizar, aguarde o processamento. O arquivo será salvo na pasta escolhida."
        )
        messagebox.showinfo("Ajuda - Merotec Screen Recorder", mensagem)

    def escolher_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.diretorio_destino = pasta
            self.recorder.set_output_dir(pasta)
            self.label_caminho.configure(text=pasta)

    def alternar_gravacao(self):
        if not self.recorder.recording:
            self.iniciar_gravacao()
        else:
            self.parar_gravacao()

    def iniciar_gravacao(self):
        camera_fullscreen = self.camera_fullscreen_var.get()
        camera_enabled = self.camera_var.get() or camera_fullscreen
        capture_screen_enabled = not camera_fullscreen
        camera_position = self.obter_posicao_camera() if camera_enabled and capture_screen_enabled else None

        if camera_enabled:
            self.fechar_preview_camera()

        self.btn_gravar.configure(text="⏹ Parar Gravação", fg_color="#dc2626", hover_color="#b91c1c")
        self.btn_pasta.configure(state="disabled")
        self.checkbox_camera.configure(state="disabled")
        self.checkbox_camera_fullscreen.configure(state="disabled")
        pode_alternar_tela = camera_enabled and capture_screen_enabled
        self.btn_alternar_tela.configure(state="normal" if pode_alternar_tela else "disabled")
        self.atualizar_botao_alternar_tela(capture_screen_enabled)
        self.atualizar_status("GRAVANDO...", "#e74c3c")

        self.recorder.start(
            camera_enabled=camera_enabled,
            camera_overlay_position=camera_position,
            capture_screen_enabled=capture_screen_enabled,
        )

    def parar_gravacao(self):
        self.recorder.stop()
        self.btn_gravar.configure(
            text="Processando...",
            state="disabled",
            fg_color="#475569",
            hover_color="#475569",
        )

    def atualizar_status_selecao(self):
        if self.recorder.recording:
            return

        if self.camera_fullscreen_var.get():
            self.atualizar_status("Status: modo câmera cheia selecionado.", "#c084fc")
        elif self.camera_var.get():
            self.atualizar_status("Status: tela com câmera sobreposta selecionada.", "#60a5fa")
        else:
            self.atualizar_status("Status: pronto para gravar somente a tela.", "#94a3b8")

    def alternar_preview_camera(self):
        if self.camera_var.get():
            self.camera_fullscreen_var.set(False)
            self.abrir_preview_camera()
        else:
            self.fechar_preview_camera()

        self.atualizar_status_selecao()

    def alternar_modo_camera_cheia(self):
        if self.camera_fullscreen_var.get():
            self.camera_var.set(False)
            self.fechar_preview_camera()
        elif self.camera_var.get():
            self.abrir_preview_camera()

        self.atualizar_status_selecao()

    def alternar_captura_tela(self):
        capture_screen_enabled = not self.recorder.is_capture_screen_enabled()
        self.recorder.set_capture_screen_enabled(capture_screen_enabled)
        self.atualizar_botao_alternar_tela(capture_screen_enabled)
        if capture_screen_enabled:
            self.atualizar_status("Status: captura da tela ativada.", "#60a5fa")
        else:
            self.atualizar_status("Status: gravando somente a câmera.", "#c084fc")

    def atualizar_botao_alternar_tela(self, capture_screen_enabled):
        if capture_screen_enabled:
            self.btn_alternar_tela.configure(
                text="🖥️ Desativar captura da tela",
                fg_color="#2563eb",
                hover_color="#1d4ed8",
            )
        else:
            self.btn_alternar_tela.configure(
                text="📷 Gravar também a tela",
                fg_color="#8b5cf6",
                hover_color="#7c3aed",
            )

    def abrir_preview_camera(self):
        if self.camera_window and self.camera_window.winfo_exists():
            self.camera_window.lift()
            return

        self.camera_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.camera_capture.isOpened():
            self.camera_capture.release()
            self.camera_capture = None
            self.camera_var.set(False)
            self.atualizar_status("Câmera não encontrada.", "orange")
            return

        self.camera_window = ctk.CTkToplevel(self)
        self.camera_window.title("Posição da câmera")
        self.camera_window.geometry("320x220+80+80")
        self.camera_window.resizable(width=False, height=False)
        self.camera_window.attributes("-topmost", True)
        self.camera_window.protocol("WM_DELETE_WINDOW", self.fechar_preview_camera)

        instrucao = ctk.CTkLabel(
            self.camera_window,
            text="Arraste esta janela para posicionar a câmera na gravação",
            font=("Arial", 11),
        )
        instrucao.pack(pady=4)

        self.camera_label = ctk.CTkLabel(self.camera_window, text="")
        self.camera_label.pack(padx=8, pady=4)

        for widget in (self.camera_window, instrucao, self.camera_label):
            widget.bind("<ButtonPress-1>", self.iniciar_arraste_camera)
            widget.bind("<B1-Motion>", self.arrastar_camera)

        self.camera_preview_running = True
        self.atualizar_preview_camera()

    def fechar_preview_camera(self):
        self.camera_preview_running = False
        if self.camera_capture:
            self.camera_capture.release()
            self.camera_capture = None
        if self.camera_window and self.camera_window.winfo_exists():
            self.camera_window.destroy()
        self.camera_window = None
        self.camera_label = None

    def iniciar_arraste_camera(self, event):
        self.camera_drag_offset = (event.x_root - self.camera_window.winfo_x(), event.y_root - self.camera_window.winfo_y())

    def arrastar_camera(self, event):
        offset_x, offset_y = self.camera_drag_offset
        self.camera_window.geometry(f"+{event.x_root - offset_x}+{event.y_root - offset_y}")

    def atualizar_preview_camera(self):
        if not self.camera_preview_running or not self.camera_capture or not self.camera_label:
            return

        sucesso, frame = self.camera_capture.read()
        if sucesso:
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (300, 169))
            imagem = Image.fromarray(frame)
            self.camera_photo = ImageTk.PhotoImage(imagem)
            self.camera_label.configure(image=self.camera_photo)

        self.after(33, self.atualizar_preview_camera)

    def obter_posicao_camera(self):
        if not self.camera_window or not self.camera_window.winfo_exists():
            return None

        x = self.camera_window.winfo_x()
        y = self.camera_window.winfo_y()
        return (x, y)

    def atualizar_status(self, texto, cor=None):
        update = {"text": texto}
        if cor:
            update["text_color"] = cor

        self.after(0, lambda: self.status_label.configure(**update))

    def finalizar_interface(self, sucesso, mensagem, cor=None):
        def atualizar():
            self.status_label.configure(text=mensagem, text_color=cor or "gray")
            self.btn_gravar.configure(
                text="🔴 Iniciar Gravação",
                fg_color="#16a34a",
                hover_color="#15803d",
                state="normal",
            )
            self.btn_pasta.configure(state="normal")
            self.checkbox_camera.configure(state="normal")
            self.checkbox_camera_fullscreen.configure(state="normal")
            self.btn_alternar_tela.configure(state="disabled")

            if self.camera_var.get() and not self.camera_fullscreen_var.get():
                self.abrir_preview_camera()

        self.after(0, atualizar)

    def destroy(self):
        self.fechar_preview_camera()
        super().destroy()


if __name__ == "__main__":
    app = GravadorApp()
    app.mainloop()
