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

        # Dentro de __init__ da classe MainWindow em app/main_window.py

        # ... (outros botões no self.control_frame) ...
        self.organize_ai_button = customtkinter.CTkButton(self.control_frame, 
                                                        text="Organizar Tudo com IA", 
                                                        command=self.process_ai_organization)
        self.organize_ai_button.pack(side="left", padx=10, pady=5) # Ajuste 'side' e 'padx/pady' conforme necessário

        def process_ai_organization(self):
            if not self.current_folder:
                messagebox.showerror("Erro", "Nenhuma pasta de origem com fotos foi selecionada.")
                return
            if not self.destination_folder:
                messagebox.showerror("Erro", "Nenhuma pasta de destino foi selecionada para salvar as fotos organizadas.")
                return

            if not initialize_ai_model(): # Garante que o modelo de IA esteja pronto
                messagebox.showerror("Erro de IA", "Não foi possível inicializar o modelo de IA. Verifique o terminal para mensagens de ERRO CRÍTICO [AI].")
                return

            # self.image_files é populado por self.select_folder()
            if not self.image_files:
                messagebox.showinfo("Informação", "Nenhuma imagem encontrada na pasta de origem para organizar.")
                return

            # Janela de Progresso Simples
            progress_window = customtkinter.CTkToplevel(self)
            progress_window.title("Processando...")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)
            progress_window.grab_set() # Impede interação com a janela principal
            
            progress_label_title = customtkinter.CTkLabel(progress_window, text="Organização Automática com IA", font=customtkinter.CTkFont(size=16, weight="bold"))
            progress_label_title.pack(pady=(10,5))
            
            progress_status_label = customtkinter.CTkLabel(progress_window, text="Inicializando...")
            progress_status_label.pack(pady=5)
            
            # (Opcional) Barra de progresso - mais complexa para atualizar em tempo real sem threads
            # progress_bar = customtkinter.CTkProgressBar(progress_window, orientation="horizontal", mode="determinate")
            # progress_bar.set(0)
            # progress_bar.pack(pady=10, padx=10, fill="x")
            
            self.update_idletasks() # Atualiza a UI para mostrar a janela de progresso

            photos_to_categorize_map_ai = {}
            total_files = len(self.image_files)
            
            print(f"\nINFO [AI Org]: Iniciando organização com IA para {total_files} imagens...")

            for i, img_path in enumerate(self.image_files):
                status_text = f"Processando imagem {i+1} de {total_files}:\n{os.path.basename(img_path)}"
                print(status_text) # Log no terminal
                progress_status_label.configure(text=status_text) # Atualiza label na UI
                # progress_bar.set(float(i+1)/total_files) # Atualiza barra de progresso
                progress_window.update_idletasks() # Força atualização da UI de progresso

                ai_results = predict_image_content(img_path, num_results=5) # Pega os 5 principais resultados da IA
                
                # USER_CATEGORIES_MAP e USER_DEFAULT_CATEGORY são definidos no escopo da classe ou globalmente neste arquivo
                category = map_ai_labels_to_user_category(ai_results, USER_CATEGORIES_MAP, USER_DEFAULT_CATEGORY)
                photos_to_categorize_map_ai[img_path] = category
                print(f"  -> Categoria IA: {category}")

            progress_status_label.configure(text="Processamento de IA concluído! Movendo arquivos...")
            # progress_bar.set(1)
            progress_window.update_idletasks()
            print("INFO [AI Org]: Processamento de IA concluído.")

            if not photos_to_categorize_map_ai:
                progress_window.destroy()
                messagebox.showinfo("Concluído", "Nenhuma categoria pôde ser atribuída ou não havia fotos para processar.")
                return

            # Mover os arquivos para as pastas de categoria
            print(f"INFO [AI Org]: Movendo {len(photos_to_categorize_map_ai)} fotos para '{self.destination_folder}'...")
            success_moving = categorize_photos(destination_base_folder=self.destination_folder,
                                            photo_category_map=photos_to_categorize_map_ai)

            if not success_moving:
                progress_window.destroy()
                messagebox.showerror("Erro na Organização", "Ocorreu um erro ao mover os arquivos para as pastas de categoria. Verifique o terminal.")
                return
            
            progress_status_label.configure(text="Fotos movidas! Gerando log...")
            progress_window.update_idletasks()
            print("INFO [AI Org]: Fotos movidas com sucesso.")

            # Gerar log de texto
            self.generate_organization_log(photos_to_categorize_map_ai, self.destination_folder, self.current_folder)

            # Criar o arquivo ZIP
            progress_status_label.configure(text="Criando arquivo ZIP...")
            progress_window.update_idletasks()
            print(f"INFO [AI Org]: Criando arquivo ZIP das pastas organizadas em {self.destination_folder}...")
            
            default_zip_name = f"Fotos_Organizadas_IA_{os.path.basename(self.current_folder)}_{datetime.datetime.now().strftime('%Y%m%d')}.zip"
            
            progress_window.grab_release() # Libera a janela principal para o diálogo de salvar
            progress_window.withdraw() # Esconde a janela de progresso temporariamente

            zip_save_path = filedialog.asksaveasfilename(
                master=self, # Garante que o diálogo apareça sobre a janela principal
                title="Salvar ZIP com as Fotos Organizadas",
                defaultextension=".zip",
                initialfile=default_zip_name,
                filetypes=[("Arquivos ZIP", "*.zip")]
            )
            
            progress_window.deiconify() # Mostra novamente
            progress_window.grab_set()

            if zip_save_path:
                progress_status_label.configure(text=f"Salvando ZIP em:\n{os.path.basename(zip_save_path)}...")
                progress_window.update_idletasks()
                zip_success = create_zip_of_organized_folders(self.destination_folder, zip_save_path) # Função de utils.py
                if zip_success:
                    progress_window.destroy() # Fecha a janela de progresso
                    messagebox.showinfo("Sucesso Total!", f"Fotos organizadas, log gerado e arquivo ZIP salvo com sucesso em:\n{zip_save_path}")
                else:
                    progress_window.destroy()
                    messagebox.showerror("Erro ao Criar ZIP", "Não foi possível criar o arquivo ZIP. Verifique o terminal.")
            else:
                progress_window.destroy()
                messagebox.showinfo("Criação de ZIP Cancelada", "A criação do arquivo ZIP foi cancelada. As fotos foram organizadas na pasta de destino e o log foi gerado.")

            # Atualizar lista de arquivos da pasta de origem (se as fotos foram movidas e não copiadas)
            self.image_files = get_image_files(self.current_folder) 
            self.populate_folder_photos_list() # Para atualizar a UI da lista de categorização manual, se visível

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


    def generate_organization_log(self, categorized_map, destination_base, source_folder_path):
            log_filename = f"log_organizacao_ia_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            # Salva o log na pasta de destino junto com as pastas organizadas
            log_filepath = os.path.join(destination_base, log_filename) 

            try:
                with open(log_filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Relatório de Organização de Fotos por IA - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"Pasta de Origem Processada: {source_folder_path}\n")
                    f.write(f"Pasta de Destino (Base para Categorias): {destination_base}\n")
                    f.write("----------------------------------------------------------\n")
                    f.write("Detalhes da Organização:\n")
                    f.write("----------------------------------------------------------\n\n")
                    
                    for original_path, category in categorized_map.items():
                        filename = os.path.basename(original_path)
                        # O caminho final exato pode variar se houver renomeação de duplicatas em categorize_photos
                        final_path_in_category = os.path.join(destination_base, category, filename) 
                        
                        f.write(f"Arquivo Original: {original_path}\n")
                        f.write(f"  -> Categoria Atribuída pela IA: {category}\n")
                        f.write(f"  -> Localização Estimada Pós-Organização: {final_path_in_category}\n\n")
                    
                    f.write("----------------------------------------------------------\n")
                    f.write(f"Total de {len(categorized_map)} fotos processadas neste relatório.\n")
                    f.write("Fim do Relatório.\n")
                print(f"INFO [Log]: Log de organização salvo em: {log_filepath}")
            except Exception as e:
                print(f"ERRO [Log]: Falha ao gerar o log de organização: {e}")
                # Não mostra um messagebox aqui para não interromper o fluxo se o ZIP já foi oferecido.
                # O erro já foi impresso no terminal.
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