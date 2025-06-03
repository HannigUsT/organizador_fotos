# test_heif.py
from PIL import Image, features
print(f"Versão do Pillow: {Image.__version__}")

import pillow_heif
print(f"Versão do pillow_heif: {pillow_heif.__version__}")

# Tenta o registro explícito do abridor HEIF
try:
    pillow_heif.register_heif_opener()
    print("INFO: pillow_heif.register_heif_opener() foi chamado.")
except Exception as e:
    print(f"ERRO ao chamar pillow_heif.register_heif_opener(): {e}")

# Tenta features.check_codec("heif"), mas não deixa o script parar se falhar
try:
    heif_codec_available = features.check_codec("heif")
    print(f"INFO: Pillow features.check_codec('heif') retornou: {heif_codec_available}")
except ValueError as e:
    print(f"AVISO: Erro ao chamar features.check_codec('heif'): {e} (Isso pode ser esperado se o Pillow não tiver um verificador embutido para HEIF)")
except AttributeError as e: # Para o caso de voltar a uma versão antiga do Pillow sem querer
    print(f"AVISO: Erro de atributo ao chamar features.check_codec('heif'): {e} (Versão antiga do Pillow?)")


# --- Teste Principal com uma imagem HEIC ---
# !!! SUBSTITUA ESTE CAMINHO POR UM CAMINHO REAL PARA UMA DE SUAS IMAGENS HEIC !!!
caminho_imagem_heic_teste = "/home/hanni/projetos/organizador_fotos/assets/Cópia de IMG_1069.HEIC" # Use um dos seus arquivos

print(f"\n--- Testando com a imagem: {caminho_imagem_heic_teste} ---")
if pillow_heif.is_supported(caminho_imagem_heic_teste):
    print(f"INFO: pillow_heif.is_supported() retornou True para a imagem.")
    try:
        print(f"INFO: Tentando abrir com Image.open()...")
        img = Image.open(caminho_imagem_heic_teste)
        print(f"SUCESSO! Imagem HEIC aberta com Image.open(): Formato={img.format}, Tamanho={img.size}, Modo={img.mode}")
        img.close()
    except Exception as e:
        print(f"FALHA: Erro ao tentar abrir HEIC com Image.open() diretamente: {e}")
else:
    print(f"INFO: pillow_heif.is_supported() retornou False para a imagem.")


# --- Informações de Plugins do Pillow ---
print("\n--- Informações de Plugins do Pillow ---")
try:
    Image.init() # Garante que todos os plugins sejam carregados
    
    print("\nPlugins de formato registrados (Image.ID):")
    # Image.ID é uma lista dos nomes dos formatos de arquivo que podem ser lidos.
    for plugin_name in Image.ID:
        print(f"- {plugin_name}")

    print("\nExtensões conhecidas pelo Pillow (Image.EXTENSION):")
    # Image.EXTENSION é um dicionário mapeando extensões para nomes de formato.
    # Nem todos os formatos aqui necessariamente têm um abridor funcional.
    for ext, format_name in Image.EXTENSION.items():
        print(f"- Ext: {ext} -> Formato: {format_name}")
    
    # Uma forma mais robusta de verificar se HEIC/HEIF está entre os formatos que Pillow pode abrir
    print("\nVerificando se HEIF/HEIC estão nos formatos de abertura do Pillow:")
    if "HEIF" in Image.OPENERS or "HEIC" in Image.OPENERS:
        print("SUCESSO: 'HEIF' ou 'HEIC' encontrado em Image.OPENERS.")
    else:
        # Image.OPENERS mapeia nomes de formato para classes de plugin.
        # pillow-heif registra 'HEIF'.
        heif_opener_found = False
        for fmt, opener_class in Image.OPENERS.items():
            if fmt.upper() == "HEIF": # pillow-heif registra como "HEIF"
                print(f"SUCESSO: Encontrado abridor para o formato '{fmt}' (classe: {opener_class.__name__ if hasattr(opener_class, '__name__') else opener_class})")
                heif_opener_found = True
                break
        if not heif_opener_found:
            print("AVISO: Nenhum abridor explicitamente nomeado 'HEIF' ou 'HEIC' encontrado em Image.OPENERS.")
            print("Formatos em Image.OPENERS:")
            for fmt in Image.OPENERS:
                print(f"  - {fmt}")


except Exception as e:
    print(f"ERRO ao listar plugins/formatos do Pillow: {e}")

print("\n--- Fim do teste ---")