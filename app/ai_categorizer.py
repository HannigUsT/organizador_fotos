# app/ai_categorizer.py
from imageai.Classification import ImageClassification # Importação atualizada para ImageAI v3+
import os
import threading # Para inicializar o modelo em background no futuro

# Caminho para a pasta de modelos e para o arquivo do modelo específico
# Presume que o script está rodando da raiz do projeto ou que o getcwd() é a raiz.
# Se rodar main.py da raiz, os.getcwd() será a raiz do projeto.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # Vai para a pasta organizador_fotos
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "resnet50_imagenet_tf.2.0.h5")

# Objeto preditor global para carregar o modelo apenas uma vez
image_predictor = None
model_initialized_successfully = False # Flag para status da inicialização

def initialize_ai_model():
    global image_predictor, model_initialized_successfully

    if image_predictor is not None and model_initialized_successfully:
        return True # Já inicializado com sucesso

    if not os.path.exists(MODEL_PATH):
        print(f"ERRO CRÍTICO [AI]: Arquivo do modelo não encontrado em {MODEL_PATH}")
        print("Por favor, baixe o modelo ResNet50 (resnet50_imagenet_tf.2.0.h5) e coloque na pasta 'models'.")
        print("Link: https://github.com/OlafenwaMoses/ImageAI/releases/download/3.0.0-pretrained/resnet50_imagenet_tf.2.0.h5")
        model_initialized_successfully = False
        return False

    try:
        print("INFO [AI]: Inicializando modelo de IA (ResNet50). Isso pode levar alguns instantes...")
        image_predictor = ImageClassification()
        image_predictor.setModelTypeAsResNet50()
        image_predictor.setModelPath(MODEL_PATH)
        image_predictor.loadModel() # Pode adicionar detection_speed="fast" ou "fastest" para menos precisão mas mais rápido
        print("INFO [AI]: Modelo de IA inicializado com sucesso.")
        model_initialized_successfully = True
        return True
    except Exception as e:
        print(f"ERRO CRÍTICO [AI]: Falha ao inicializar o modelo de IA: {e}")
        image_predictor = None # Reseta em caso de falha
        model_initialized_successfully = False
        return False

def predict_image_content(image_path, num_results=5):
    """
    Classifica uma imagem e retorna os N principais resultados.
    Retorna uma lista de dicionários: [{"label": "nome", "probability": 0.xx}] ou None em caso de erro.
    """
    global image_predictor, model_initialized_successfully
    if image_predictor is None or not model_initialized_successfully:
        print("AVISO [AI]: Modelo de IA não inicializado. Tentando inicializar agora...")
        if not initialize_ai_model(): # Tenta inicializar se ainda não foi
            print("ERRO [AI]: Não foi possível inicializar o modelo para predição.")
            return None # Falha ao inicializar modelo

    if not os.path.exists(image_path):
        print(f"ERRO [AI]: Arquivo de imagem não encontrado em {image_path}")
        return None

    try:
        predictions, probabilities = image_predictor.classifyImage(image_path, result_count=num_results)

        results = []
        for i in range(len(predictions)):
            results.append({"label": predictions[i].replace("_", " "), "probability": probabilities[i]}) # Substitui "_" por espaço para melhor leitura
        # print(f"Predições para {os.path.basename(image_path)}: {results}")
        return results
    except Exception as e:
        print(f"ERRO [AI]: Falha ao classificar a imagem {os.path.basename(image_path)}: {e}")
        return None

def map_ai_labels_to_user_category(ai_results, user_categories_map, default_category="outros"):
    """
    Mapeia os rótulos da IA para as categorias definidas pelo usuário.
    user_categories_map: Um dicionário como {'comida': ['food', 'plate', 'meal', 'fruit'], 'amigos': ['person', 'people'], ...}
    """
    if ai_results is None:
        return default_category

    # Ordena os resultados da IA pela maior probabilidade
    sorted_results = sorted(ai_results, key=lambda x: x['probability'], reverse=True)

    for result in sorted_results:
        ai_label = result["label"].lower() # Rótulo da IA em minúsculas
        # print(f"  AI label: {ai_label} (Prob: {result['probability']:.2f})") # Para debug

        for user_cat, keywords in user_categories_map.items():
            for keyword in keywords:
                if keyword.lower() in ai_label: # Verifica se alguma palavra-chave da categoria está no rótulo da IA
                    # print(f"    Mapeado para '{user_cat}' via keyword '{keyword}' em '{ai_label}'")
                    return user_cat # Retorna a primeira categoria de usuário correspondente

    # print(f"  Nenhum mapeamento encontrado, usando default: {default_category}")
    return default_category