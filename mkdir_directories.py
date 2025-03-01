"""
Script utilitaire pour créer les répertoires nécessaires au bon fonctionnement de l'application
"""
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas déjà"""
    directories = [
        'instance',
        'static',
        'static/css',
        'static/js',
        'static/img',
        'static/img/previews',  # Dossier pour les prévisualisations d'infographies
        'static/img/previews/network',  # Dossier pour les prévisualisations d'infographies réseau 
        'static/img/previews/protocol',  # Dossier pour les prévisualisations d'infographies de protocole
        'static/img/previews/vulnerability',  # Dossier pour les prévisualisations d'infographies de vulnérabilité
        'static/fonts',
        'static/exports',  # Dossier pour les infographies exportées
        'static/exports/network',  # Dossier pour les infographies réseau exportées
        'static/exports/protocol',  # Dossier pour les infographies de protocole exportées
        'static/exports/vulnerability',  # Dossier pour les infographies de vulnérabilité exportées
        'static/templates', # Dossier pour les templates d'infographie
        'templates',
        'templates/admin',  # Dossier pour les templates d'administration

    # Répertoires pour l'analyseur de données echo
    os.makedirs("instance/echo_data", exist_ok=True)
    os.makedirs("instance/echo_reports", exist_ok=True)
    logger.info("Répertoire créé ou déjà existant: instance/echo_data")
    logger.info("Répertoire créé ou déjà existant: instance/echo_reports")

        'config'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Répertoire créé ou déjà existant: {directory}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du répertoire {directory}: {e}")

def initialize_files():
    """Crée des fichiers vides s'ils n'existent pas déjà"""
    files = [
        'config/default.py',
        'config/production.py',
        'config/development.py',
        '.flaskenv'
    ]
    
    for file_path in files:
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    if file_path == '.flaskenv':
                        f.write("FLASK_APP=app.py\nFLASK_ENV=development\n")
                    elif file_path == 'config/default.py':
                        f.write("# Configuration par défaut\n")
                    elif file_path == 'config/production.py':
                        f.write("# Configuration de production\n")
                    elif file_path == 'config/development.py':
                        f.write("# Configuration de développement\n")
                logger.info(f"Fichier créé: {file_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la création du fichier {file_path}: {e}")
        else:
            logger.info(f"Fichier déjà existant: {file_path}")

if __name__ == "__main__":
    logger.info("Création des répertoires et initialisation des fichiers...")
    create_directories()
    initialize_files()
    logger.info("Initialisation terminée avec succès")