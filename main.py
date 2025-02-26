#!/usr/bin/env python3
"""
Application principale pour NetSecure Pro - Analyse de sécurité réseau WiFi
"""
import os
import json
import logging
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify,
    session, abort, current_app
)
from flask_login import (
    LoginManager, current_user, login_user, logout_user, login_required
)
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db, socketio, login_manager
from forms import LoginForm, RegistrationForm, SaveTopologyForm
from models import User, UserReport, SavedTopology
from network_topology import NetworkTopology
from security_scoring import DeviceSecurityScoring
from assistant_securite import AssistantSecurite

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialiser les classes principales
network_topology = NetworkTopology()
security_scoring = DeviceSecurityScoring()
assistant_securite = AssistantSecurite()

# Contexte global pour tous les templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Filtres personnalisés pour les templates
@app.template_filter('datetime')
def format_datetime(value, format='relative'):
    """Format une datetime en une chaîne lisible.
    
    Args:
        value: La datetime à formater (peut être une chaîne ISO ou un objet datetime)
        format: Le format de sortie ('relative' pour "il y a X minutes", ou un format strftime)
    """
    if not value:
        return ""
    
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return value
    
    if format == 'relative':
        now = datetime.now()
        diff = now - value
        
        if diff.days > 365:
            return f"il y a {diff.days // 365} ans"
        if diff.days > 30:
            return f"il y a {diff.days // 30} mois"
        if diff.days > 0:
            return f"il y a {diff.days} jours"
        if diff.seconds > 3600:
            return f"il y a {diff.seconds // 3600} heures"
        if diff.seconds > 60:
            return f"il y a {diff.seconds // 60} minutes"
        return "à l'instant"
    
    return value.strftime(format)

# Routes principales
@app.route('/')
def accueil():
    """Page d'accueil de l'application"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription d'un nouvel utilisateur"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur lors de l'inscription: {e}")
            flash('Une erreur est survenue lors de la création du compte. Veuillez réessayer.', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion d'un utilisateur existant"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Connexion réussie !', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Connexion échouée. Veuillez vérifier votre email et votre mot de passe.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Déconnexion de l'utilisateur"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('accueil'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord de l'utilisateur connecté"""
    # Récupérer les statistiques du réseau
    network_stats = security_scoring.get_network_security_status()
    
    # Récupérer tous les appareils avec leurs scores
    device_scores = security_scoring.get_all_device_scores()
    
    # Trier les appareils par score de sécurité (du plus bas au plus élevé)
    device_scores.sort(key=lambda x: x['security_score'])
    
    return render_template(
        'dashboard.html',
        network_stats=network_stats,
        device_scores=device_scores
    )

@app.route('/network-topology')
@login_required
def network_topology_view():
    """Vue de la topologie du réseau"""
    form = SaveTopologyForm()
    return render_template('network_topology.html', form=form)

@app.route('/topology/save', methods=['POST'])
@login_required
def save_topology():
    """Sauvegarde de la topologie réseau"""
    form = SaveTopologyForm()
    
    if form.validate_on_submit():
        try:
            # Récupérer les données de disposition des appareils
            layout_data = json.loads(request.form.get('layout_data', '{}'))
            
            # Créer une nouvelle topologie sauvegardée
            topology = SavedTopology(
                user_id=current_user.id,
                name=form.name.data,
                layout_data=json.dumps(layout_data)
            )
            
            db.session.add(topology)
            db.session.commit()
            
            flash('Disposition sauvegardée avec succès.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur lors de la sauvegarde de la topologie: {e}")
            flash('Une erreur est survenue lors de la sauvegarde.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('network_topology_view'))

# Routes API
@app.route('/api/topology')
@login_required
def get_topology():
    """API pour récupérer les données de topologie réseau"""
    topology_data = network_topology.get_topology_data()
    return jsonify(topology_data)

@app.route('/api/topology/layout', methods=['POST'])
@login_required
def update_topology_layout():
    """API pour mettre à jour la disposition des appareils"""
    data = request.json
    
    if not data or 'mac_address' not in data or 'x' not in data or 'y' not in data:
        return jsonify({'success': False, 'error': 'Données invalides'})
    
    try:
        network_topology.save_layout(data)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la disposition: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/topology/layout/save', methods=['POST'])
@login_required
def save_topology_layout():
    """API pour sauvegarder une disposition de topologie"""
    data = request.json
    
    if not data or 'name' not in data or 'layout' not in data:
        return jsonify({'success': False, 'error': 'Données invalides'})
    
    try:
        # Créer une nouvelle topologie sauvegardée
        topology = SavedTopology(
            user_id=current_user.id,
            name=data['name'],
            layout_data=json.dumps(data['layout'])
        )
        
        db.session.add(topology)
        db.session.commit()
        
        return jsonify({'success': True, 'id': topology.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la sauvegarde de la disposition: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/device/<mac_address>')
@login_required
def get_device_details(mac_address):
    """API pour récupérer les détails d'un appareil spécifique"""
    device = None
    
    # Rechercher dans les données de topologie
    for d in network_topology.topology_data['devices']:
        if d['mac_address'] == mac_address:
            device = d
            break
    
    if not device:
        return jsonify({'success': False, 'error': 'Appareil non trouvé'})
    
    # Ajouter les données de sécurité
    security_info = security_scoring.get_device(mac_address)
    if security_info:
        device.update({
            'security_issues': security_info.get('security_issues', []),
            'recommendations': security_info.get('recommendations', [])
        })
    
    return jsonify({'success': True, 'device': device})

@app.route('/api/device/<mac_address>/security', methods=['GET'])
@login_required
def update_device_security(mac_address):
    """API pour mettre à jour les informations de sécurité d'un appareil"""
    # Calculer un nouveau score de sécurité pour l'appareil
    new_score = security_scoring.calculate_device_score(mac_address)
    
    if new_score is None:
        return jsonify({'success': False, 'error': 'Appareil non trouvé'})
    
    # Mettre à jour les données de topologie
    device_data = security_scoring.get_device(mac_address)
    if device_data:
        network_topology.update_device_security(mac_address, {
            'security_score': device_data['security_score'],
            'security_issues': device_data.get('security_issues', [])
        })
    
    # Émettre une mise à jour via Socket.IO
    socketio.emit('device_update', {
        'mac_address': mac_address,
        'security_score': new_score,
        'last_updated': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'new_score': new_score})

# Routes pour l'assistant de sécurité
@app.route('/assistant', methods=['GET', 'POST'])
@login_required
def assistant():
    """Page de l'assistant de sécurité"""
    if request.method == 'POST':
        user_input = request.form.get('question', '')
        if user_input:
            # Récupérer les données de topologie pour le contexte
            network_data = network_topology.get_topology_data()
            
            # Générer une réponse
            response = assistant_securite.generate_response(
                user_input, 
                conversation_id=current_user.id,
                network_data=network_data
            )
            
            return jsonify({'success': True, 'response': response})
        else:
            return jsonify({'success': False, 'error': 'Question vide'})
    
    # Récupérer l'historique des conversations
    conversations = assistant_securite.get_conversation_history(current_user.id)
    
    return render_template('assistant.html', conversations=conversations)

@app.route('/vulnerability-analysis')
@login_required
def vulnerability_analysis():
    """Page d'analyse des vulnérabilités"""
    return render_template('vulnerability_analysis.html')

@app.route('/security-report')
@login_required
def security_report():
    """Page de rapport détaillé de sécurité"""
    return render_template('security_report.html')

@app.route('/protocol-analysis')
@login_required
def protocol_analysis():
    """Page d'analyse des protocoles de sécurité WiFi"""
    from protocol_analyzer import ProtocolAnalyzer
    
    # Initialiser l'analyseur de protocoles
    analyzer = ProtocolAnalyzer()
    
    # Récupérer les données d'exemple pour la démonstration
    # Dans une implémentation réelle, ces données viendraient d'une analyse réseau
    test_networks = [
        {
            "ssid": "Réseau_Domicile",
            "bssid": "00:11:22:33:44:55",
            "security": "WPA2",
            "encryption": "AES",
            "authentication": "PSK",
            "strength": -65,
            "frequency": "2.4GHz",
            "channel": 6
        },
        {
            "ssid": "Réseau_Ancien",
            "bssid": "AA:BB:CC:DD:EE:FF",
            "security": "WEP",
            "encryption": None,
            "authentication": None,
            "strength": -70,
            "frequency": "2.4GHz",
            "channel": 11
        },
        {
            "ssid": "Réseau_Invité",
            "bssid": "11:22:33:44:55:66",
            "security": "OPEN",
            "encryption": None,
            "authentication": None,
            "strength": -60,
            "frequency": "2.4GHz",
            "channel": 1
        },
        {
            "ssid": "Réseau_Enterprise",
            "bssid": "22:33:44:55:66:77",
            "security": "WPA2",
            "encryption": "AES",
            "authentication": "ENTERPRISE",
            "strength": -55,
            "frequency": "5GHz",
            "channel": 36
        },
        {
            "ssid": "Réseau_Moderne",
            "bssid": "33:44:55:66:77:88",
            "security": "WPA3",
            "encryption": "GCMP",
            "authentication": "SAE",
            "strength": -50,
            "frequency": "5GHz",
            "channel": 48
        }
    ]
    
    # Analyser les réseaux
    analysis_results = analyzer.analyze_all_networks(test_networks)
    
    # Récupérer le résumé global
    summary = analyzer.get_protocol_analysis_summary()
    
    # Récupérer la comparaison des protocoles
    protocol_comparison = analyzer.get_protocol_comparison()
    
    # Récupérer la chronologie des analyses
    timeline = analyzer.get_protocol_timeline()
    
    return render_template(
        'protocol_analysis.html',
        analysis_results=analysis_results,
        summary=summary,
        protocol_comparison=protocol_comparison,
        timeline=timeline
    )

@app.route('/export-infographic/<report_type>')
@login_required
def export_infographic(report_type):
    """Génère et exporte une infographie basée sur le type de rapport"""
    from infographic_generator import InfographicGenerator
    from protocol_analyzer import ProtocolAnalyzer
    
    # Initialiser le générateur d'infographies
    generator = InfographicGenerator()
    
    # Chemin du fichier infographique généré
    output_path = None
    
    # Selon le type de rapport, générer l'infographie appropriée
    if report_type == 'network_security':
        # Exemple de données de réseau pour la démonstration
        network_data = {
            'overall_score': 72,
            'protocol_distribution': {
                'WPA3': 1,
                'WPA2': 3,
                'WPA': 0,
                'WEP': 1,
                'OPEN': 1
            },
            'security_dimensions': {
                'Authentification': 65,
                'Chiffrement': 70,
                'Mises à jour': 50,
                'Pare-feu': 85,
                'Segmentation': 90,
                'Monitoring': 60
            },
            'devices': [
                {'name': 'Caméra IP', 'security_score': 35},
                {'name': 'Smart TV', 'security_score': 55},
                {'name': 'Smartphone', 'security_score': 65},
                {'name': 'Routeur WiFi', 'security_score': 75},
                {'name': 'Ordinateur portable', 'security_score': 85}
            ],
            'security_trend': [
                {'date': 'Jan', 'score': 54},
                {'date': 'Fév', 'score': 58},
                {'date': 'Mar', 'score': 60},
                {'date': 'Avr', 'score': 65},
                {'date': 'Mai', 'score': 68},
                {'date': 'Juin', 'score': 72}
            ]
        }
        
        # Exemple de données de vulnérabilité
        vulnerability_data = {
            'vulnerability_types': {
                'firmware_outdated': 8,
                'weak_password': 6,
                'open_ports': 5,
                'protocol_weakness': 5,
                'missing_updates': 4,
                'default_credentials': 4
            },
            'recommendations': [
                {
                    'priority': 'critical',
                    'description': 'Mettre à jour le firmware du routeur',
                    'details': 'Votre routeur exécute un firmware obsolète contenant des vulnérabilités connues.'
                },
                {
                    'priority': 'high',
                    'description': 'Changer les mots de passe par défaut',
                    'details': 'Plusieurs appareils IoT utilisent encore leurs mots de passe par défaut.'
                },
                {
                    'priority': 'medium',
                    'description': 'Activer WPA3 sur votre réseau WiFi',
                    'details': 'Passer à WPA3 offre une meilleure protection contre les attaques.'
                }
            ]
        }
        
        # Générer l'infographie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"network_security_{timestamp}.png"
        output_path = generator.generate_network_security_infographic(
            network_data, vulnerability_data, output_filename=filename
        )
    
    elif report_type == 'protocol_analysis':
        # Initialiser l'analyseur de protocoles
        analyzer = ProtocolAnalyzer()
        
        # Récupérer les données d'exemple
        test_networks = [
            {
                "ssid": "Réseau_Domicile",
                "bssid": "00:11:22:33:44:55",
                "security": "WPA2",
                "encryption": "AES",
                "authentication": "PSK",
                "strength": -65,
                "frequency": "2.4GHz",
                "channel": 6
            },
            {
                "ssid": "Réseau_Ancien",
                "bssid": "AA:BB:CC:DD:EE:FF",
                "security": "WEP",
                "encryption": None,
                "authentication": None,
                "strength": -70,
                "frequency": "2.4GHz",
                "channel": 11
            },
            {
                "ssid": "Réseau_Moderne",
                "bssid": "33:44:55:66:77:88",
                "security": "WPA3",
                "encryption": "GCMP",
                "authentication": "SAE",
                "strength": -50,
                "frequency": "5GHz",
                "channel": 48
            }
        ]
        
        # Analyser les réseaux
        analyzer.analyze_all_networks(test_networks)
        
        # Préparer les données pour l'infographie
        protocol_data = {
            'average_score': analyzer.get_protocol_analysis_summary().get('average_score', 0),
            'protocol_distribution': analyzer.get_protocol_analysis_summary().get('protocol_distribution', {}),
            'protocols': analyzer.get_protocol_comparison().get('protocols', []),
            'vulnerability_by_protocol': {
                'WEP': {'critical': 5, 'high': 3, 'medium': 1, 'low': 0},
                'WPA': {'critical': 2, 'high': 4, 'medium': 2, 'low': 1},
                'WPA2': {'critical': 1, 'high': 2, 'medium': 3, 'low': 2},
                'WPA3': {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            },
            'protocol_strengths': {
                'WEP': {'Chiffrement': 10, 'Authentification': 15, 'Intégrité': 20, 'Résistance aux attaques': 5, 'Gestion des clés': 10},
                'WPA': {'Chiffrement': 40, 'Authentification': 45, 'Intégrité': 50, 'Résistance aux attaques': 35, 'Gestion des clés': 40},
                'WPA2': {'Chiffrement': 75, 'Authentification': 70, 'Intégrité': 80, 'Résistance aux attaques': 65, 'Gestion des clés': 70},
                'WPA3': {'Chiffrement': 90, 'Authentification': 95, 'Intégrité': 90, 'Résistance aux attaques': 85, 'Gestion des clés': 90}
            },
            'recommendations': analyzer.get_protocol_analysis_summary().get('recommendations', [])
        }
        
        # Générer l'infographie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"protocol_analysis_{timestamp}.png"
        output_path = generator.generate_protocol_analysis_infographic(
            protocol_data, output_filename=filename
        )
    
    elif report_type == 'vulnerability_report':
        # Exemple de données de vulnérabilité
        vulnerability_data = {
            'summary': {
                'total': 32,
                'critical': 3,
                'high': 8,
                'medium': 15,
                'low': 6,
                'cvss_avg': 7.8,
                'risk_level': 'Élevé'
            },
            'critical_vulnerabilities': [
                {
                    'cve_id': 'CVE-2022-26928',
                    'description': 'Vulnérabilité d\'exécution de code à distance dans le firmware',
                    'severity': 'critical',
                    'cvss_score': 9.8,
                    'affected_device': 'Routeur WiFi Principal',
                    'status': 'Non corrigé'
                },
                {
                    'cve_id': 'CVE-2021-37714',
                    'description': 'Identifiants par défaut exposés permettant un accès non autorisé',
                    'severity': 'critical',
                    'cvss_score': 9.6,
                    'affected_device': 'Caméra IP',
                    'status': 'Non corrigé'
                },
                {
                    'cve_id': 'CVE-2023-12345',
                    'description': 'Vulnérabilité de débordement de tampon dans le traitement des paquets réseau',
                    'severity': 'critical',
                    'cvss_score': 9.1,
                    'affected_device': 'Smart TV',
                    'status': 'Non corrigé'
                }
            ],
            'severity_distribution': {
                'critical': 3,
                'high': 8,
                'medium': 15,
                'low': 6
            },
            'discovery_timeline': [
                {'date': 'Jan', 'total': 2, 'critical': 0},
                {'date': 'Fév', 'total': 5, 'critical': 1},
                {'date': 'Mar', 'total': 3, 'critical': 0},
                {'date': 'Avr', 'total': 8, 'critical': 2},
                {'date': 'Mai', 'total': 6, 'critical': 0},
                {'date': 'Juin', 'total': 8, 'critical': 1}
            ],
            'remediation_plan': [
                {
                    'action': 'Mettre à jour le firmware du routeur',
                    'priority': 'critical',
                    'estimated_time': '30 minutes',
                    'difficulty': 'Facile',
                    'impact': 'Élimine une vulnérabilité critique'
                },
                {
                    'action': 'Changer les mots de passe par défaut',
                    'priority': 'critical',
                    'estimated_time': '20 minutes',
                    'difficulty': 'Facile',
                    'impact': 'Sécurise les appareils IoT vulnérables'
                },
                {
                    'action': 'Activer WPA3',
                    'priority': 'high',
                    'estimated_time': '10 minutes',
                    'difficulty': 'Facile',
                    'impact': 'Renforce la sécurité du WiFi'
                },
                {
                    'action': 'Configurer un réseau invité',
                    'priority': 'medium',
                    'estimated_time': '15 minutes',
                    'difficulty': 'Moyenne',
                    'impact': 'Isole les appareils IoT du réseau principal'
                }
            ]
        }
        
        # Générer l'infographie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vulnerability_report_{timestamp}.png"
        output_path = generator.generate_vulnerability_report_infographic(
            vulnerability_data, output_filename=filename
        )
    
    else:
        # Type de rapport non pris en charge
        flash('Type de rapport non pris en charge', 'danger')
        return redirect(url_for('dashboard'))
    
    # Vérifier si l'infographie a été générée
    if not output_path or not os.path.exists(output_path):
        flash('Erreur lors de la génération de l\'infographie', 'danger')
        return redirect(url_for('dashboard'))
    
    # Retourner le chemin relatif pour servir le fichier
    relative_path = output_path.replace('static/', '')
    
    # Enregistrer le téléchargement dans l'historique de l'utilisateur
    # Cette partie serait implémentée dans une version complète
    
    # Rediriger vers la page de visualisation avec un message de succès
    flash('Infographie générée avec succès', 'success')
    return render_template('export_success.html', image_path=relative_path)


@app.route('/api/export-infographic/<report_type>', methods=['POST'])
@login_required
def api_export_infographic(report_type):
    """API pour générer une infographie et retourner son URL"""
    # Cette route est appelée par AJAX pour générer l'infographie en arrière-plan
    
    try:
        # Rediriger vers la route normale qui génère l'infographie
        response_url = url_for('export_infographic', report_type=report_type)
        
        return jsonify({
            'success': True,
            'message': 'Génération de l\'infographie en cours...',
            'redirect_url': response_url
        })
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'infographie: {e}")
        return jsonify({
            'success': False,
            'message': f"Erreur lors de la génération: {str(e)}"
        }), 500

# Gestionnaires d'événements Socket.IO
@socketio.on('connect')
def handle_connect():
    """Gestion de la connexion WebSocket"""
    logger.info(f"Client connecté: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Gestion de la déconnexion WebSocket"""
    logger.info(f"Client déconnecté: {request.sid}")

@socketio.on('request_topology')
def handle_topology_request():
    """Envoi des données de topologie au client"""
    topology_data = network_topology.get_topology_data()
    emit('topology_data', topology_data)

@socketio.on('update_layout')
def handle_layout_update(data):
    """Mise à jour de la disposition des appareils"""
    if 'mac_address' in data and 'x' in data and 'y' in data:
        try:
            network_topology.save_layout(data)
            # Émettre la mise à jour à tous les clients
            emit('layout_update', {data['mac_address']: {'x': data['x'], 'y': data['y']}}, broadcast=True)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la disposition: {e}")

@socketio.on('update_device_security')
def handle_device_security_update(data):
    """Mise à jour des informations de sécurité d'un appareil"""
    if 'mac_address' in data:
        mac_address = data['mac_address']
        # Calculer un nouveau score de sécurité
        new_score = security_scoring.calculate_device_score(mac_address)
        
        if new_score is not None:
            # Mettre à jour les données de topologie
            device_data = security_scoring.get_device(mac_address)
            if device_data:
                network_topology.update_device_security(mac_address, {
                    'security_score': device_data['security_score'],
                    'security_issues': device_data.get('security_issues', [])
                })
            
            # Émettre la mise à jour à tous les clients
            emit('device_update', {
                'mac_address': mac_address,
                'security_score': new_score,
                'last_updated': datetime.now().isoformat()
            }, broadcast=True)

# Gestionnaires d'erreurs
@app.errorhandler(404)
def page_non_trouvee(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def erreur_serveur(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Point d'entrée principal
if __name__ == '__main__':
    # Démarrer l'application avec Socket.IO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)