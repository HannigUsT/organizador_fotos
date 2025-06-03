# app/ai_categorizer.py
from imageai.Classification import ImageClassification
import os
# import threading # Para inicializar o modelo em background no futuro

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
# Certifique-se que este é o modelo que você baixou e está na pasta models/
# MODEL_PATH = os.path.join(MODEL_DIR, "resnet50_imagenet_tf.2.0.h5")
MODEL_PATH = os.path.join(MODEL_DIR, "resnet50-19c8e357.pth") # NOVA LINHA para o modelo PyTorch

image_predictor = None # CORREÇÃO AQUI - inicializado como None
model_initialized_successfully = False

def initialize_ai_model():
    global image_predictor, model_initialized_successfully

    if image_predictor is not None and model_initialized_successfully:
        return True

    if not os.path.exists(MODEL_PATH):
        print(f"ERRO CRÍTICO [AI]: Arquivo do modelo não encontrado em {MODEL_PATH}")
        # Atualize este link para o da release 2.1.6 se for diferente, ou remova se o usuário já tem o arquivo.
        print("Por favor, baixe o modelo ResNet50 (resnet50_imagenet_tf.2.0.h5) e coloque na pasta 'models'.")
        print("Link de referência (release 2.1.6): https://github.com/OlafenwaMoses/ImageAI/releases/download/2.1.6-pretrained/resnet50_imagenet_tf.2.0.h5")
        model_initialized_successfully = False
        return False

    try:
        print("INFO [AI]: Inicializando modelo de IA (ResNet50) com ImageAI 2.1.6...")
        image_predictor = ImageClassification() 
        image_predictor.setModelTypeAsResNet50() 
        image_predictor.setModelPath(MODEL_PATH)
        image_predictor.loadModel() 
        print("INFO [AI]: Modelo de IA inicializado com sucesso.")
        model_initialized_successfully = True
        return True
    except Exception as e:
        print(f"ERRO CRÍTICO [AI]: Falha ao inicializar o modelo de IA: {e}")
        image_predictor = None 
        model_initialized_successfully = False
        return False

def predict_image_content(image_path, num_results=5):
    global image_predictor, model_initialized_successfully
    if image_predictor is None or not model_initialized_successfully:
        print("AVISO [AI]: Modelo de IA não inicializado. Tentando inicializar agora...")
        if not initialize_ai_model():
            print("ERRO [AI]: Não foi possível inicializar o modelo para predição.")
            return None

    if not os.path.exists(image_path):
        print(f"ERRO [AI]: Arquivo de imagem não encontrado em {image_path}")
        return None

    try:
        # O método classifyImage é adequado para ResNet e retorna predições e probabilidades
        predictions, probabilities = image_predictor.classifyImage(image_path, result_count=num_results)
        results = []
        for i in range(len(predictions)):
            results.append({"label": predictions[i].replace("_", " "), "probability": probabilities[i]})
        return results
    except Exception as e:
        print(f"ERRO [AI]: Falha ao classificar a imagem {os.path.basename(image_path)}: {e}")
        return None

# A função map_ai_labels_to_user_category continua igual
def map_ai_labels_to_user_category(ai_results, user_categories_map, default_category="outros"):
    if ai_results is None:
        return default_category
    sorted_results = sorted(ai_results, key=lambda x: x['probability'], reverse=True)
    for result in sorted_results:
        ai_label = result["label"].lower()
        for user_cat, keywords in user_categories_map.items():
            for keyword in keywords:
                if keyword.lower() in ai_label:
                    return user_cat
    return default_category