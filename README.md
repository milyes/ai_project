# NetSecurePro - Plateforme IA Modulaire

**NetSecurePro** est une plateforme intelligente et modulaire combinant plusieurs outils IA pour lâ€™analyse, la sÃ©curitÃ©, la santÃ©, la connectivitÃ©, et la productivitÃ©. Elle est conÃ§ue pour fonctionner localement (Termux/Linux) ou en cloud (VPS, Docker).

## Principales fonctionnalitÃ©s

- **SÃ©curitÃ©** : chiffrement des donnÃ©es, JWT, protection XSS/SQLi
- **Modules IA intÃ©grÃ©s** :
  - Analyse de santÃ© (Parkinson, DiabÃ¨te)
  - Analyse rÃ©seau (WiFi, Bluetooth)
  - Traitement de langage (analyse de sentiments, rÃ©sumÃ©s)
- **API REST performante (FastAPI / Flask)**
- **Interface web moderne (React / HTML / Tailwind)**
- **DÃ©ploiement possible en local ou cloud**
- **Terminal IA intelligent intÃ©grÃ©**
- **Support mobile (Android avec Termux)**

---

## Architecture des modules

```
NetSecurePro/
â”œâ”€â”€ AIMEDIXAL/               # Analyse Parkinson
â”œâ”€â”€ AIMEDIAB/                # Analyse DiabÃ¨te
â”œâ”€â”€ BluetoothNetworkScanner/ # Scan Bluetooth
â”œâ”€â”€ FlaskServer/             # Serveur principal Flask
â”œâ”€â”€ LanguageLearner/         # Apprentissage linguistique
â”œâ”€â”€ TerminalIA/              # Terminal IA local
â”œâ”€â”€ API_Gateway/             # Routeur API centralisÃ©
â”œâ”€â”€ Dashboard/               # Tableau de bord (Plotly/React)
â””â”€â”€ Mobile/                  # Interface Android (Flutter/ReactNative)
```

---

## Modules inclus

### 1. **AIMEDIXAL** - IA mÃ©dicale Parkinson
- Analyse des tremblements via capteurs
- Upload de fichiers, analyse IA, retour immÃ©diat
- Interface HTML + API FastAPI

### 2. **AIMEDIAB** - IA mÃ©dicale DiabÃ¨te
- Analyse de donnÃ©es glycÃ©miques
- Courbes, alertes, PDF de rÃ©sultats
- ModÃ¨le CNN/Transformers (optionnel)

### 3. **BluetoothNetworkScanner**
- DÃ©tection des appareils Bluetooth environnants
- GÃ©nÃ©ration de rapports JSON/CSV
- Compatible mobile et Raspberry Pi

### 4. **FlaskServer**
- Serveur API sÃ©curisÃ©
- IntÃ©gration avec modules IA
- Authentification, gestion utilisateurs

### 5. **LanguageLearner**
- Suggestions IA de vocabulaire et grammaire
- Analyse des erreurs de l'utilisateur

### 6. **TerminalIA**
- Terminal Linux-like
- Dialogue IA en ligne de commande
- ExÃ©cution de scripts et analyse systÃ¨me

---

## Installation rapide

### 1. Cloner le projet

```bash
git clone https://github.com/milyes/NetSecurePro.git
cd NetSecurePro
```

### 2. Installer les dÃ©pendances (global)

```bash
pip install -r requirements.txt
```

### 3. Lancer un module (ex: AIMEDIXAL)

```bash
cd AIMEDIXAL/api
uvicorn main:app --reload
```

---

## DÃ©ploiement Docker

Un `Dockerfile` est fourni dans chaque module principal. Exemple :

```bash
cd AIMEDIXAL
docker build -t aimedixal .
docker run -p 8000:8000 aimedixal
```

---

## SÃ©curitÃ©

- HTTPS via Cloudflare ou nginx
- Authentification par tokens JWT
- Chiffrement des donnÃ©es sensibles (bcrypt / Fernet)
- Protection contre les injections SQL et attaques XSS
- Headers sÃ©curisÃ©s avec Flask-Talisman

---

## Contribuer

Les contributions sont les bienvenues !  
Merci de crÃ©er un **fork** puis une **pull request** avec une description claire.

---

## Licence

Projet distribuÃ© sous **licence MIT**.

---

## Auteur

DÃ©veloppÃ© par **milyes**  
Site : [https://milyes.github.io/ai_project](https://milyes.github.io/ai_project)  
Email : milyes@wardam.me
