# app/photo_manager.py
import os
import shutil

# Ajuste a assinatura da função se necessário, mas a que você tinha já é boa:
def categorize_photos(destination_base_folder, photo_category_map): # Removi source_folder se não for usado diretamente aqui
    """
    Move fotos para pastas de categoria.
    photo_category_map é um dicionário: {'caminho/foto1.jpg': 'NomeCategoria1', ...}
    """
    if not os.path.isdir(destination_base_folder):
        try:
            os.makedirs(destination_base_folder, exist_ok=True)
            print(f"[Photo Manager] Pasta base de destino criada: {destination_base_folder}")
        except OSError as e:
            print(f"[Photo Manager] Erro ao criar pasta base de destino {destination_base_folder}: {e}")
            return False # Indica falha

    moved_count = 0
    for photo_path, category_name in photo_category_map.items():
        if not category_name.strip(): # Ignora se o nome da categoria estiver vazio
            print(f"[Photo Manager] Nome da categoria vazio para {photo_path}. Pulando.")
            continue

        if not os.path.isfile(photo_path):
            print(f"[Photo Manager] Aviso: Foto {photo_path} não encontrada. Pulando.")
            continue

        # Sanitizar nome da categoria para nome de pasta (opcional, mas bom)
        # category_folder_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in category_name).strip()
        # if not category_folder_name: category_folder_name = "sem_categoria"
        category_folder_name = category_name # Usando o nome direto por enquanto

        category_folder_path = os.path.join(destination_base_folder, category_folder_name)
        
        if not os.path.isdir(category_folder_path):
            try:
                os.makedirs(category_folder_path, exist_ok=True)
                print(f"[Photo Manager] Pasta da categoria '{category_folder_name}' criada em: {category_folder_path}")
            except OSError as e:
                print(f"[Photo Manager] Erro ao criar pasta da categoria {category_folder_name} em {category_folder_path}: {e}")
                continue # Pula para a próxima foto em caso de erro ao criar a pasta
        
        filename = os.path.basename(photo_path)
        destination_path = os.path.join(category_folder_path, filename)
        
        # Evitar sobrescrever por acidente se já existir um arquivo com o mesmo nome
        counter = 1
        temp_destination_path = destination_path
        while os.path.exists(temp_destination_path):
            name, ext = os.path.splitext(filename)
            temp_destination_path = os.path.join(category_folder_path, f"{name}_{counter}{ext}")
            counter += 1
        if temp_destination_path != destination_path:
            print(f"[Photo Manager] Arquivo de destino já existe. Renomeando para: {temp_destination_path}")
            destination_path = temp_destination_path

        try:
            # Mudar para shutil.copy(photo_path, destination_path) se preferir copiar em vez de mover
            shutil.move(photo_path, destination_path)
            print(f"[Photo Manager] Movido: {photo_path} -> {destination_path}")
            moved_count += 1
        except Exception as e:
            print(f"[Photo Manager] Erro ao mover {photo_path} para {destination_path}: {e}")
            # Se falhar ao mover, a foto original permanece. Considere o que fazer aqui.
            # Poderia tentar copiar e depois excluir se a cópia for bem sucedida.
    
    print(f"[Photo Manager] Total de {moved_count} fotos movidas.")
    return True # Indica sucesso geral (mesmo que algumas fotos individuais falhem)


def delete_files_with_permission(file_list_to_delete, user_permission_callback):
    """
    Exclui arquivos APÓS obter permissão para cada um ou para o grupo.
    user_permission_callback é uma função que deve retornar True para excluir.
    """
    deleted_files = []
    failed_deletions = []

    # Exemplo de como obter permissão (a lógica real estará na GUI)
    # if not user_permission_callback(file_list_to_delete):
    #     print("Exclusão cancelada pelo usuário.")
    #     return [], file_list_to_delete

    for filepath in file_list_to_delete:
        if os.path.isfile(filepath):
            # AQUI VOCÊ DEVE INTEGRAR COM A GUI PARA CONFIRMAÇÃO INDIVIDUAL SE NECESSÁRIO
            # Para este exemplo, assumimos que a permissão geral foi dada
            # if user_permission_callback_for_file(filepath): # Função hipotética
            try:
                os.remove(filepath)
                deleted_files.append(filepath)
                print(f"Excluído: {filepath}")
            except OSError as e:
                failed_deletions.append(filepath)
                print(f"Erro ao excluir {filepath}: {e}")
            # else:
            #     print(f"Exclusão de {filepath} negada.")
        else:
            print(f"Aviso: Arquivo {filepath} não encontrado para exclusão.")
            failed_deletions.append(filepath)
            
    return deleted_files, failed_deletions