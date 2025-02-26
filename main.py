from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_socketio import SocketIO, emit
import logging
import json
import os
import subprocess
import asyncio
from network_security import NetworkSecurityAnalyzer
from assistant_securite import AssistantSecurite
from translation import get_user_language, get_translation, get_all_translations, get_direction, AVAILABLE_LANGUAGES
from recommendations import recommendation_system
from network_detector import NetworkDetector
from network_topology import NetworkTopology

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Création de l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Configuration de Socket.IO - 'message_queue' est nécessaire pour Flask run
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialiser l'analyseur de sécurité
security_analyzer = NetworkSecurityAnalyzer()

# Initialiser l'assistant de sécurité
assistant = AssistantSecurite()

# Initialiser le gestionnaire de topologie réseau
topology_manager = NetworkTopology()

# Configuration de l'analyseur WiFi
CONFIG_DIR = os.path.expanduser("~/.network_detect")
WIFI_RESULTS_FILE = os.path.join(CONFIG_DIR, "wifi_results.json")

def load_wifi_data():
    if not os.path.exists(WIFI_RESULTS_FILE):
        logger.warning("Aucun fichier de résultats WiFi trouvé.")
        # Essayer de générer des données de test
        try:
            logger.info("Génération de données de test...")
            subprocess.run(["python", "generate_test_data.py"], check=True)
            if os.path.exists(WIFI_RESULTS_FILE):
                logger.info("Données de test générées avec succès.")
            else:
                logger.warning("Échec de génération des données de test.")
                return []
        except Exception as e:
            logger.error(f"Erreur lors de la génération des données de test: {e}")
            return []

    with open(WIFI_RESULTS_FILE, "r") as file:
        try:
            data = json.load(file)
            return [net for net in data if net.get("ssid")]
        except json.JSONDecodeError:
            logger.error("Fichier JSON invalide.")
            return []

def score_network(network):
    # Score basé sur la puissance du signal et le type de sécurité
    signal_score = max(-network["rssi"], 0)  # Plus le RSSI est proche de 0, meilleur est le signal

    # Bonus pour la sécurité (WPA2/WPA3 est meilleur)
    security = network.get("security", "").upper()
    security_score = 0
    if "WPA3" in security:
        security_score = 30
    elif "WPA2" in security:
        security_score = 20
    elif "WPA" in security:
        security_score = 10

    # Score total (plus petit = meilleur)
    return signal_score - security_score

def get_best_network():
    wifi_data = load_wifi_data()
    if not wifi_data:
        return None
    # Le meilleur réseau a le score le plus bas
    return min(wifi_data, key=score_network)

# Route pour changer la langue
@app.route('/set-language/<language>')
def set_language(language):
    if language in AVAILABLE_LANGUAGES:
        session['language'] = language

    # Rediriger vers la page précédente ou l'accueil
    referer = request.headers.get('Referer')
    if referer:
        return redirect(referer)
    return redirect(url_for('accueil'))

@app.route('/')
def accueil():
    logger.info('Page d\'accueil visitée')
    best_network = get_best_network()
    all_networks = load_wifi_data()

    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)

    # Récupérer le statut des technologies réseau
    network_status = NetworkDetector.get_saved_status()

    return render_template('index.html', 
                           network=best_network, 
                           all_networks=all_networks,
                           network_status=network_status,
                           translations=translations,
                           available_languages=AVAILABLE_LANGUAGES,
                           current_language=lang,
                           text_direction=text_direction)

@app.route('/security-report')
def security_report():
    """Page principale des rapports de sécurité"""
    logger.info('Page des rapports de sécurité visitée')
    all_networks = load_wifi_data()

    # Récupérer les rapports existants
    saved_reports = security_analyzer.get_saved_reports()

    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)

    return render_template(
        'security_report.html', 
        all_networks=all_networks,
        saved_reports=saved_reports,
        translations=translations,
        available_languages=AVAILABLE_LANGUAGES,
        current_language=lang,
        text_direction=text_direction
    )

@app.route('/generate-report', methods=['POST'])
def generate_report():
    """Génère un nouveau rapport de sécurité"""
    report_name = request.form.get('report_name', '')
    all_networks = load_wifi_data()

    if not all_networks:
        return redirect(url_for('security_report'))

    report = security_analyzer.generate_report(all_networks, report_name)

    # Enregistrer l'action pour les recommandations personnalisées
    if report:
        security_levels = {
            level: count 
            for level, count in report['statistics']['security_distribution'].items()
        }
        recommendation_system.add_report_generation(
            report_name=report['report_name'],
            networks_count=report['statistics']['total_networks'],
            security_levels=security_levels
        )

    if report:
        return redirect(url_for('view_report', report_name=report['report_name']))
    else:
        return redirect(url_for('security_report'))

@app.route('/view-report/<report_name>')
def view_report(report_name):
    """Affiche un rapport spécifique"""
    report = security_analyzer.get_report_by_name(report_name)

    if not report:
        return redirect(url_for('security_report'))

    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)

    return render_template('view_report.html', 
                          report=report,
                          translations=translations,
                          available_languages=AVAILABLE_LANGUAGES,
                          current_language=lang,
                          text_direction=text_direction)

# Route pour les recommandations personnalisées
@app.route('/recommendations')
def personalized_recommendations():
    """Page de recommandations personnalisées"""
    logger.info('Page des recommandations personnalisées visitée')

    # Obtenir les recommandations personnalisées
    recommendations = recommendation_system.get_recommendations()

    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)

    # Formater la date pour l'affichage
    last_updated = recommendations.get('last_updated', '')
    if last_updated:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(last_updated)
            last_updated = dt.strftime('%d/%m/%Y %H:%M')
        except Exception as e:
            logger.error(f"Erreur lors du formatage de la date: {e}")

    return render_template(
        'recommendations.html',
        security_focus=recommendations.get('security_focus', 'general'),
        preferred_security=recommendations.get('network_preferences', {}).get('preferred_security', 'WPA2'),
        frequently_accessed=recommendations.get('network_preferences', {}).get('frequently_accessed', []),
        actions=recommendations.get('recommended_actions', []),
        last_updated=last_updated,
        translations=translations,
        available_languages=AVAILABLE_LANGUAGES,
        current_language=lang,
        text_direction=text_direction
    )

# Routes pour l'assistant de sécurité conversationnel
@app.route('/assistant')
def assistant_page():
    """Page principale de l'assistant de sécurité"""
    logger.info('Page de l\'assistant de sécurité visitée')
    all_networks = load_wifi_data()
    conversation_id = request.args.get('conversation_id')

    # Récupérer l'historique de conversation si un ID est fourni
    conversation_history = []
    if conversation_id:
        conversation_history = assistant.get_conversation_history(conversation_id)

    # Récupérer la liste des conversations
    all_conversations = assistant.get_all_conversations()

    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)

    return render_template(
        'assistant.html', 
        all_networks=all_networks,
        conversation_history=conversation_history,
        conversation_id=conversation_id,
        all_conversations=all_conversations,
        translations=translations,
        available_languages=AVAILABLE_LANGUAGES,
        current_language=lang,
        text_direction=text_direction
    )

@app.route('/api/assistant/message', methods=['POST'])
def assistant_message():
    """API pour interagir avec l'assistant de sécurité"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Données non fournies"}), 400

    user_input = data.get('message', '')
    conversation_id = data.get('conversation_id')
    network_id = data.get('network_id')

    # Récupérer les données du réseau si un ID est fourni
    network_data = None
    if network_id is not None:
        all_networks = load_wifi_data()
        try:
            network_id = int(network_id)
            if 0 <= network_id < len(all_networks):
                network_data = all_networks[network_id]
        except (ValueError, TypeError):
            pass

    # Générer une réponse
    response = assistant.generate_response(user_input, conversation_id, network_data)

    return jsonify(response)

@app.route('/api/assistant/conversations')
def get_conversations():
    """API pour récupérer la liste des conversations"""
    conversations = assistant.get_all_conversations()
    return jsonify(conversations)

@app.route('/network-topology')
def network_topology():
    """Page de visualisation de la topologie du réseau"""
    logger.info('Page de topologie du réseau visitée')
    
    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)
    
    return render_template(
        'network_topology.html',
        translations=translations,
        available_languages=AVAILABLE_LANGUAGES,
        current_language=lang,
        text_direction=text_direction
    )

@app.route('/device-security')
def device_security():
    """Page de sécurité des appareils"""
    logger.info('Page de sécurité des appareils visitée')
    
    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)
    
    # Initialisation du système de notation de sécurité
    from security_scoring import security_scoring
    
    # Récupérer les données des appareils
    devices = security_scoring.get_all_device_scores()
    network_status = security_scoring.get_network_security_status()
    
    return render_template(
        'device_security.html',
        devices=devices,
        network_status=network_status,
        translations=translations,
        available_languages=AVAILABLE_LANGUAGES,
        current_language=lang,
        text_direction=text_direction
    )

@app.route('/api/analyze-network', methods=['POST'])
def api_analyze_network():
    """API pour analyser un réseau spécifique"""
    data = request.get_json()
    network = data.get('network')

    if not network:
        return jsonify({"error": "Réseau non spécifié"}), 400

    result = security_analyzer.analyze_network(network)

    # Enregistrer l'analyse pour les recommandations personnalisées
    if result and 'overall_recommendation' in result:
        recommendation_system.add_network_analysis(
            network_ssid=network.get('ssid', ''),
            security_level=result.get('security_level', ''),
            recommendations=result.get('overall_recommendation', [])
        )

    return jsonify(result)

@socketio.on('request_network_update')
def handle_network_update():
    best_network = get_best_network()
    all_networks = load_wifi_data()
    emit('network_update', {'best': best_network, 'all': all_networks})

@socketio.on('request_technology_status')
async def handle_technology_status():
    status = await NetworkDetector.save_network_status()
    emit('technology_status_update', status)

@socketio.on('analyze_network_security')
def handle_analyze_network(data):
    """Analyser la sécurité d'un réseau spécifique via WebSocket"""
    network_id = data.get('network_id')
    all_networks = load_wifi_data()

    if not all_networks or network_id is None or network_id >= len(all_networks):
        emit('security_analysis_result', {'error': 'Réseau non trouvé'})
        return

    network = all_networks[network_id]
    result = security_analyzer.analyze_network(network)

    # Enregistrer l'analyse pour les recommandations personnalisées
    if result and 'overall_recommendation' in result:
        recommendation_system.add_network_analysis(
            network_ssid=network.get('ssid', ''),
            security_level=result.get('security_level', ''),
            recommendations=result.get('overall_recommendation', [])
        )

    emit('security_analysis_result', result)

# Routes API et WebSocket pour la topologie réseau
@app.route('/api/topology', methods=['GET'])
def get_topology():
    """API pour récupérer les données de topologie réseau"""
    topology_data = topology_manager.get_topology_data()
    return jsonify(topology_data)

@app.route('/api/topology/layout', methods=['POST'])
def update_topology_layout():
    """API pour mettre à jour la disposition des appareils"""
    layout_data = request.json
    if not layout_data:
        return jsonify({"error": "Données de disposition non fournies"}), 400
    
    try:
        topology_manager.save_layout(layout_data)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la disposition: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/device/<mac_address>', methods=['GET'])
def get_device_details(mac_address):
    """API pour récupérer les détails d'un appareil spécifique"""
    for device in topology_manager.devices:
        if device['mac_address'] == mac_address:
            return jsonify(device)
    return jsonify({"error": "Appareil non trouvé"}), 404

@app.route('/api/device/<mac_address>', methods=['PUT'])
def update_device_security(mac_address):
    """API pour mettre à jour les informations de sécurité d'un appareil"""
    security_data = request.json
    if not security_data:
        return jsonify({"error": "Données de sécurité non fournies"}), 400
    
    success = topology_manager.update_device_security(mac_address, security_data)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "Appareil non trouvé"}), 404

@socketio.on('request_topology_data')
def handle_topology_request():
    """Gestionnaire de demande de données de topologie via WebSocket"""
    topology_data = topology_manager.get_topology_data()
    emit('topology_update', topology_data)

@socketio.on('update_topology_layout')
def handle_layout_update(data):
    """Gestionnaire de mise à jour de la disposition via WebSocket"""
    try:
        topology_manager.save_layout(data)
        emit('layout_saved', {"success": True})
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la disposition via WebSocket: {e}")
        emit('layout_saved', {"success": False, "error": str(e)})

@app.errorhandler(404)
def page_non_trouvee(error):
    logger.error(f'Page non trouvée: {error}')

    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)

    return render_template('index.html', 
                          error=get_translation("error_not_found", lang),
                          translations=translations,
                          available_languages=AVAILABLE_LANGUAGES,
                          current_language=lang,
                          text_direction=text_direction), 404

@app.errorhandler(500)
def erreur_serveur(error):
    logger.error(f'Erreur serveur: {error}')

    # Récupérer les traductions et la direction du texte
    lang = get_user_language()
    translations = get_all_translations(lang)
    text_direction = get_direction(lang)

    return render_template('index.html', 
                          error=get_translation("error_server", lang),
                          translations=translations,
                          available_languages=AVAILABLE_LANGUAGES,
                          current_language=lang,
                          text_direction=text_direction), 500

# Ajouter les traductions et la direction du texte à tous les templates
@app.context_processor
def inject_translations():
    lang = get_user_language()
    return {
        't': lambda key: get_translation(key, lang),
        'translations': get_all_translations(lang),
        'available_languages': AVAILABLE_LANGUAGES,
        'current_language': lang,
        'text_direction': get_direction(lang)
    }

# S'assurer que le répertoire de configuration existe
os.makedirs(CONFIG_DIR, exist_ok=True)

# Cette ligne permet à flask run de fonctionner avec socketio
socketio.init_app(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)