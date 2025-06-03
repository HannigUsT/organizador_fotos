# app/utils.py
import os
import hashlib

def calculate_file_hash(filepath, hash_algo="sha256", block_size=65536):
    """Calcula o hash de um arquivo."""
    hasher = hashlib.new(hash_algo)
    try:
        with open(filepath, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                hasher.update(block)
        return hasher.hexdigest()
    except IOError:
        # Tratar erro de leitura do arquivo
        return None

# def get_image_files(folder_path):
#     """Retorna uma lista de arquivos de imagem em uma pasta."""
#     supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
#     image_files = []
#     if not os.path.isdir(folder_path):
#         return image_files
        
#     for item in os.listdir(folder_path):
#         item_path = os.path.join(folder_path, item)
#         if os.path.isfile(item_path) and item.lower().endswith(supported_extensions):
#             image_files.append(item_path)
#     return image_files

def get_image_files(folder_path):
    """Retorna uma lista de arquivos de imagem em uma pasta."""
    supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heic')
    image_files = []

    print(f"[DEBUG get_image_files] Tentando listar imagens em: {folder_path}") # Adicionado

    if not os.path.isdir(folder_path):
        print(f"[DEBUG get_image_files] O caminho NÃO é um diretório: {folder_path}") # Adicionado
        return image_files
    
    print(f"[DEBUG get_image_files] O caminho É um diretório.") # Adicionado

    try:
        items_in_folder = os.listdir(folder_path)
        print(f"[DEBUG get_image_files] Itens encontrados por os.listdir: {items_in_folder}") # Adicionado
    except Exception as e:
        print(f"[DEBUG get_image_files] Erro ao listar diretório {folder_path}: {e}") # Adicionado
        return [] # Retorna lista vazia em caso de erro

    for item in items_in_folder:
        item_path = os.path.join(folder_path, item)
        print(f"[DEBUG get_image_files] Verificando item: {item}, Caminho completo: {item_path}") # Adicionado
        
        is_file = os.path.isfile(item_path)
        print(f"[DEBUG get_image_files] É arquivo? {is_file}") # Adicionado
        
        if is_file:
            has_supported_extension = item.lower().endswith(supported_extensions)
            print(f"[DEBUG get_image_files] Item: '{item.lower()}', Tem extensão suportada? {has_supported_extension}") # Adicionado
            if has_supported_extension:
                image_files.append(item_path)
                print(f"[DEBUG get_image_files] Adicionada à lista: {item_path}") # Adicionado
        else:
            print(f"[DEBUG get_image_files] Item {item} não é um arquivo.") # Adicionado
            
    print(f"[DEBUG get_image_files] Total de imagens encontradas na função: {len(image_files)}") # Adicionado
    return image_files