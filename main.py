# main.py
import customtkinter
from app.main_window import MainWindow
import pillow_heif # Adicione esta importação

# Adicione esta linha para registrar o abridor HEIF globalmente para o Pillow
try:
    pillow_heif.register_heif_opener()
    print("INFO [main.py]: Registrador HEIF do pillow_heif ativado.")
except Exception as e:
    print(f"AVISO [main.py]: Não foi possível registrar o abridor HEIF do pillow_heif: {e}")


if __name__ == "__main__":
    # ... (o resto do seu código main.py continua igual)
    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()