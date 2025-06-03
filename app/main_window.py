# app/main_window.py
import customtkinter
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image # , ImageTk # ImageTk pode não ser necessário com CustomTkinter para imagens simples

from .utils import get_image_files
from .duplicate_detector import find_duplicate_files_by_hash
from .photo_manager import categorize_photos, delete_files_with_permission
from app.photo_manager import categorize_photos # Adicione no topo do arquivo se não estiver lá
import os

# Adicione isto no topo do seu arquivo app/main_window.py, abaixo das importações

# Este é o SEU MAPA DE TRADUÇÃO - você precisará ajustá-lo!
# As chaves são as SUAS categorias.
# Os valores são listas de palavras-chave (em inglês, minúsculas) que a IA ResNet50 pode detectar.
USER_CATEGORIES_MAP = {
    'comida': ['food', 'plate', 'meal', 'dish', 'fruit', 'vegetable', 'sushi', 'pizza', 'hamburger', 'banana', 'apple', 'salad', 'sandwich', 'cake', 'ice cream', 'pasta', 'restaurant', 'kitchen', 'dinner', 'lunch', 'breakfast'],
    'amigos': ['person', 'people', 'crowd', 'group', 'smile', 'face', 'portrait', 'man', 'woman', 'child'], # "Amigos" é conceitual. A IA verá "pessoas".
    'academia': ['dumbbell', 'barbell', 'treadmill', 'gym', 'gymnasium', 'fitness', 'sport', 'running shoe', 'yoga mat', 'exercise', 'training'],
    'plantas': ['plant', 'flower', 'tree', 'leaf', 'pot', 'flowerpot', 'garden', 'flora', 'cactus', 'rose', 'forest', 'nature'],
    'memes': ['text', 'screen', 'monitor', 'display', 'comic', 'font', 'screenshot', 'internet meme'], # "Memes" é muito difícil para IA de objetos. Os resultados podem ser limitados.
    'documentos': ['document', 'paper', 'envelope', 'letter', 'book', 'notebook', 'text', 'page', 'menu', 'card'],
    'paisagens': ['sky', 'mountain', 'beach', 'sea', 'ocean', 'landscape', 'field', 'forest', 'nature', 'river', 'lake', 'sunset', 'sunrise', 'cloud'],
    'animais': ['dog', 'cat', 'bird', 'pet', 'animal', 'lion', 'elephant', 'fish', 'insect', 'horse', 'bear', 'wildlife'],
    'veiculos': ['car', 'automobile', 'bicycle', 'motorcycle', 'bus', 'truck', 'train', 'airplane', 'boat', 'ship', 'vehicle'],
    'outros': [] # Deixe vazio. Será a categoria padrão se nenhuma palavra-chave for encontrada.
}
USER_DEFAULT_CATEGORY = 'outros' # Define qual é a sua categoria padrão

# Esta lista será usada para validar as categorias (opcional, mas bom)
USER_DEFINED_CATEGORIES_LIST = list(USER_CATEGORIES_MAP.keys())

class MainWindow(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Organizador de Fotos")
        self.geometry("1000x700")

        self.current_folder = ""
        self.image_files = []
        self.duplicate_sets = {}
        self.files_to_delete_selection = {} # {hash_set_id: {filepath: ctk_checkbox_variable}}

        # Layout com Frames
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1) # Para a lista de duplicadas/categorias expandir

        # --- Frame de Seleção de Pasta e Ações ---
        self.control_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.control_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.select_folder_button = customtkinter.CTkButton(self.control_frame, text="Selecionar Pasta de Fotos", command=self.select_folder)
        self.select_folder_button.pack(side="left", padx=5, pady=5)

        self.folder_label = customtkinter.CTkLabel(self.control_frame, text="Nenhuma pasta selecionada", anchor="w")
        self.folder_label.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.scan_duplicates_button = customtkinter.CTkButton(self.control_frame, text="Buscar Duplicatas", command=self.scan_for_duplicates)
        self.scan_duplicates_button.pack(side="left", padx=5, pady=5)
        
        self.delete_selected_button = customtkinter.CTkButton(self.control_frame, text="Excluir Selecionadas", command=self.delete_selected_duplicates, state="disabled")
        self.delete_selected_button.pack(side="right", padx=5, pady=5)


        # --- Frame para exibir miniaturas/lista de fotos (Opcional, pode ser integrado com duplicatas) ---
        # self.photos_list_frame = customtkinter.CTkScrollableFrame(self, label_text="Fotos na Pasta")
        # self.photos_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # --- Frame para exibir resultados (Duplicatas, Categorias) ---
        self.results_frame = customtkinter.CTkScrollableFrame(self, label_text="Resultados")
        self.results_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        # Inicialmente vazio, será populado com os resultados da busca por duplicatas ou interface de categorização

        self.results_frame = customtkinter.CTkScrollableFrame(self, label_text="Resultados Duplicatas") # Renomear para clareza
        self.results_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # --- Novo Frame para Listar Fotos da Pasta e Categorização ---
        self.categorization_main_frame = customtkinter.CTkFrame(self)
        self.categorization_main_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1) # Dar peso para este novo frame

        # Sub-frame para controles de categorização
        self.category_controls_frame = customtkinter.CTkFrame(self.categorization_main_frame)
        self.category_controls_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.category_label = customtkinter.CTkLabel(self.category_controls_frame, text="Nome da Categoria:")
        self.category_label.pack(side="left", padx=5)
        self.category_entry = customtkinter.CTkEntry(self.category_controls_frame, placeholder_text="Ex: Viagem, Família")
        self.category_entry.pack(side="left", padx=5, expand=True, fill="x")

        self.select_destination_button = customtkinter.CTkButton(self.category_controls_frame, text="Pasta de Destino", command=self.select_destination_folder)
        self.select_destination_button.pack(side="left", padx=5)

        self.categorize_button = customtkinter.CTkButton(self.category_controls_frame, text="Organizar Selecionadas", command=self.process_categorization, state="disabled")
        self.categorize_button.pack(side="left", padx=5)


        # Sub-frame para a lista de fotos
        self.folder_photos_list_frame = customtkinter.CTkScrollableFrame(self.categorization_main_frame, label_text="Fotos na Pasta para Organizar")
        self.folder_photos_list_frame.pack(side="bottom", fill="both", expand=True, padx=5, pady=5)

        # Variáveis para categorização
        self.destination_folder = ""
        self.photo_selection_vars = {} # Para armazenar {filepath: tk.BooleanVar()}

    def select_folder(self): # Modificada
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.current_folder = folder_path
            self.folder_label.configure(text=self.current_folder)
            # Limpar resultados anteriores de duplicatas e lista de fotos para categorização
            self.clear_results_frame() # Para duplicatas
            self.clear_folder_photos_list() # Para categorização (vamos criar esta função)

            self.delete_selected_button.configure(state="disabled") # Botão de excluir duplicatas

            self.image_files = get_image_files(self.current_folder) # Busca todos os arquivos de imagem
            print(f"Pasta selecionada: {self.current_folder}, {len(self.image_files)} imagens encontradas (verifique o terminal para debug).")

            # Popular a lista de fotos para categorização
            self.populate_folder_photos_list()
            self.update_categorize_button_state()

        else:
            self.folder_label.configure(text="Nenhuma pasta selecionada")
            self.current_folder = ""
            self.image_files = []
            self.clear_folder_photos_list()
            self.update_categorize_button_state()

    # def list_photos_in_folder(self): # Exemplo de como listar fotos
    #     for widget in self.photos_list_frame.winfo_children():
    #         widget.destroy()
    #     for i, img_path in enumerate(self.image_files):
    #         try:
    #             img = Image.open(img_path)
    #             img.thumbnail((100, 100)) # Criar miniatura
    #             # ct_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(100,100))
    #             # lbl = customtkinter.CTkLabel(self.photos_list_frame, image=ct_img, text=os.path.basename(img_path))
    #             lbl = customtkinter.CTkLabel(self.photos_list_frame, text=os.path.basename(img_path)) # Simplificado
    #             lbl.grid(row=i, column=0, padx=5, pady=2, sticky="w")
    #         except Exception as e:
    #             print(f"Erro ao carregar miniatura {img_path}: {e}")


    def clear_results_frame(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.files_to_delete_selection = {} # Resetar seleções

    def scan_for_duplicates(self):
        if not self.image_files:
            messagebox.showwarning("Aviso", "Nenhuma pasta selecionada ou nenhuma imagem encontrada.")
            return

        self.clear_results_frame()
        self.duplicate_sets = find_duplicate_files_by_hash(self.image_files)

        if not self.duplicate_sets:
            lbl = customtkinter.CTkLabel(self.results_frame, text="Nenhuma foto duplicada encontrada.")
            lbl.pack(pady=10)
            self.delete_selected_button.configure(state="disabled")
            return
        
        self.delete_selected_button.configure(state="normal")
        current_row = 0
        for i, (hash_val, files) in enumerate(self.duplicate_sets.items()):
            set_id = f"set_{i}" # Um ID único para o conjunto de duplicatas
            self.files_to_delete_selection[set_id] = {}

            group_label = customtkinter.CTkLabel(self.results_frame, text=f"Grupo de Duplicatas {i+1} (Hash: {hash_val[:8]}...):", font=customtkinter.CTkFont(weight="bold"))
            group_label.grid(row=current_row, column=0, columnspan=2, padx=5, pady=(10,2), sticky="w")
            current_row += 1

            for file_path in files:
                var = tk.BooleanVar() # Variável para o Checkbutton
                self.files_to_delete_selection[set_id][file_path] = var
                
                # Frame para agrupar checkbox, imagem e caminho
                file_frame = customtkinter.CTkFrame(self.results_frame)
                file_frame.grid(row=current_row, column=0, columnspan=2, padx=10, pady=2, sticky="ew")

                cb = customtkinter.CTkCheckBox(file_frame, text="", variable=var)
                cb.pack(side="left", padx=5)

                try:
                    img = Image.open(file_path)
                    img.thumbnail((80, 80))
                    ct_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(80,80))
                    img_label = customtkinter.CTkLabel(file_frame, image=ct_img, text="")
                    img_label.pack(side="left", padx=5)
                except Exception as e:
                    img_label = customtkinter.CTkLabel(file_frame, text="[Sem Prévia]", width=80, height=80)
                    img_label.pack(side="left", padx=5)
                    print(f"Erro ao carregar prévia de {file_path}: {e}")

                path_label = customtkinter.CTkLabel(file_frame, text=file_path, anchor="w")
                path_label.pack(side="left", padx=5, fill="x", expand=True)
                current_row += 1
        
        # Adicionar aviso sobre manter pelo menos uma cópia
        if self.duplicate_sets:
            warning_label = customtkinter.CTkLabel(self.results_frame, text="Aviso: Recomenda-se manter pelo menos uma cópia de cada grupo.", text_color="orange")
            warning_label.grid(row=current_row, column=0, columnspan=2, padx=5, pady=10, sticky="w")
            current_row += 1

    def select_destination_folder(self):
        folder_path = filedialog.askdirectory(title="Selecione a Pasta Base de Destino para Categorias")
        if folder_path:
            self.destination_folder = folder_path
            # Você pode adicionar um label para mostrar a pasta de destino selecionada
            self.select_destination_button.configure(text=f"Destino: ...{self.destination_folder[-30:]}") # Mostra o final do caminho
            print(f"Pasta de destino para categorias definida como: {self.destination_folder}")
            self.update_categorize_button_state()
        else:
            print("Nenhuma pasta de destino selecionada.")

    def delete_selected_duplicates(self):
        files_to_actually_delete = []
        for set_id, file_vars in self.files_to_delete_selection.items():
            # Validação: não permitir excluir todas as fotos de um grupo
            num_selected_in_group = sum(1 for var in file_vars.values() if var.get())
            num_total_in_group = len(file_vars)

            if num_selected_in_group == num_total_in_group and num_total_in_group > 0:
                messagebox.showerror("Erro", f"Você não pode excluir todas as cópias do Grupo de Duplicatas {set_id.split('_')[1]}. Pelo menos uma deve ser mantida.")
                return

            for file_path, var in file_vars.items():
                if var.get():
                    files_to_actually_delete.append(file_path)

        if not files_to_actually_delete:
            messagebox.showinfo("Informação", "Nenhuma foto selecionada para exclusão.")
            return

        confirm = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir {len(files_to_actually_delete)} foto(s) selecionada(s)?\nEsta ação NÃO PODE ser desfeita.")
        
        if confirm:
            # Aqui, a "permissão" é a confirmação geral.
            # Para uma permissão por arquivo, a lógica seria mais complexa na GUI.
            # Vamos usar a função de exclusão do photo_manager
            def user_permission_granted(files_to_check): # callback simples
                return True # Já foi confirmado pela messagebox

            deleted, failed = delete_files_with_permission(files_to_actually_delete, user_permission_granted)
            
            message_summary = []
            if deleted:
                message_summary.append(f"{len(deleted)} foto(s) excluída(s) com sucesso.")
            if failed:
                message_summary.append(f"{len(failed)} foto(s) falharam ao excluir.")
            
            messagebox.showinfo("Resultado da Exclusão", "\n".join(message_summary))
            
            # Re-escanear ou atualizar a lista após exclusão
            self.image_files = get_image_files(self.current_folder) # Atualizar lista de arquivos
            self.scan_for_duplicates() # Atualizar a exibição de duplicatas
        else:
            messagebox.showinfo("Cancelado", "A exclusão foi cancelada.")

    def clear_folder_photos_list(self):
        for widget in self.folder_photos_list_frame.winfo_children():
            widget.destroy()
        self.photo_selection_vars = {} # Limpa as variáveis dos checkboxes

    def populate_folder_photos_list(self):
        self.clear_folder_photos_list() # Garante que está limpo antes de popular

        if not self.image_files:
            no_files_label = customtkinter.CTkLabel(self.folder_photos_list_frame, text="Nenhuma imagem encontrada nesta pasta.")
            no_files_label.pack(pady=10)
            return

        for i, img_path in enumerate(self.image_files):
            var = tk.BooleanVar()
            self.photo_selection_vars[img_path] = var

            # Frame para cada item da lista (checkbox e nome do arquivo)
            item_frame = customtkinter.CTkFrame(self.folder_photos_list_frame)
            item_frame.pack(fill="x", pady=2, padx=2)

            cb = customtkinter.CTkCheckBox(item_frame, text="", variable=var)
            cb.pack(side="left", padx=5)

            # Adicionar miniatura (opcional, mas melhora a UX)
            try:
                img = Image.open(img_path)
                img.thumbnail((40, 40)) # Tamanho pequeno para a lista
                ct_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(40,40))
                img_label = customtkinter.CTkLabel(item_frame, image=ct_img, text="")
                img_label.pack(side="left", padx=5)
            except Exception as e:
                print(f"Erro ao carregar miniatura para {img_path} na lista: {e}")
                img_label = customtkinter.CTkLabel(item_frame, text="[IMG]", width=40) # Placeholder
                img_label.pack(side="left", padx=5)

            file_label = customtkinter.CTkLabel(item_frame, text=os.path.basename(img_path), anchor="w")
            file_label.pack(side="left", padx=5, fill="x", expand=True)

        self.update_categorize_button_state()

    def update_categorize_button_state(self):
        # Habilita o botão de organizar se houver imagens, uma categoria e uma pasta de destino
        if self.image_files and self.destination_folder and self.category_entry.get():
            # Verifica também se alguma foto foi selecionada
            any_selected = any(var.get() for var in self.photo_selection_vars.values())
            if any_selected:
                self.categorize_button.configure(state="normal")
                return
        self.categorize_button.configure(state="disabled")


    def process_categorization(self):
        selected_category = self.category_entry.get()
        if not selected_category:
            messagebox.showerror("Erro", "Por favor, insira um nome para a categoria.")
            return

        if not self.destination_folder:
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de destino para as categorias.")
            return

        photos_to_categorize_map = {}
        for img_path, var in self.photo_selection_vars.items():
            if var.get(): # Se o checkbox estiver marcado
                photos_to_categorize_map[img_path] = selected_category

        if not photos_to_categorize_map:
            messagebox.showinfo("Informação", "Nenhuma foto selecionada para categorizar.")
            return

        # Confirmação
        confirm_msg = f"Você deseja mover {len(photos_to_categorize_map)} foto(s) para a categoria '{selected_category}' dentro de '{self.destination_folder}'?"
        if messagebox.askyesno("Confirmar Organização", confirm_msg):
            print(f"Iniciando categorização para: {photos_to_categorize_map}")
            # Chamar a função de photo_manager (a ser implementada/ajustada)
            # Supondo que a função em photo_manager é categorize_photos(destination_base_folder, photo_category_map)
            # ou categorize_photos(source_folder, destination_base_folder, photo_category_map)
            # Por enquanto vamos usar uma versão simplificada:
            success = categorize_photos(destination_base_folder=self.destination_folder, 
                                        photo_category_map=photos_to_categorize_map)

            if success:
                messagebox.showinfo("Sucesso", "Fotos categorizadas com sucesso!")
                # Opcional: Limpar seleção, atualizar lista de fotos da pasta de origem, etc.
                self.image_files = get_image_files(self.current_folder) # Re-lê os arquivos da pasta de origem
                self.populate_folder_photos_list() # Repopula a lista (as fotos movidas não estarão mais lá)
            else:
                messagebox.showerror("Erro", "Ocorreu um erro durante a categorização. Verifique o terminal para detalhes.")
        else:
            messagebox.showinfo("Cancelado", "Categorização cancelada.")



    # --- Funcionalidade de Categorização (A ser implementada) ---
    # Você precisará de:
    # 1. UI para o usuário definir o nome da categoria.
    # 2. UI para o usuário selecionar para qual categoria uma ou mais fotos devem ir.
    # 3. Botão para "Aplicar Categorização".
    # 4. Diálogo para selecionar a pasta de destino das categorias.
    # 5. Chamar photo_manager.categorize_photos
    #
    # Exemplo de como poderia ser a interface de categorização:
    # - Um novo frame/tab.
    # - Uma lista de fotos da pasta atual com checkboxes.
    # - Um campo de entrada para o nome da nova categoria ou um dropdown com categorias existentes.
    # - Um botão "Adicionar à Categoria".
    # - Um botão "Processar Categorias" que pede a pasta de destino e move os arquivos.