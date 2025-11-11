# Automated CMDB

We are four University of Tartu students, and this repository contains a project for an **Automated Configuration Management Database (CMDB)** for **Eesti Pank (Bank of Estonia)**.

The solution will:
- Collect configuration data from **Accounting, Supporting IT services and Information system services** departments.
- Synchronize data automatically into **Jira Asset Management**

Our goal is to provide Eesti Pank with a single source of truth for IT assets, reduce manual work and improve compliance reporting.

# SETUP

- Offline-masin: paigalda wheelhouse
  ./install.sh ./wheelhouse
  ./start.sh

Oluline: .env ja config.json
- .env: kopeeri vajadusel .env.example → .env ja redigeeri oma keskkonnamuutujad (andmebaasi aadress, Jira token, e-posti kasutaja jms).
  Näited muutujatest, mida kontrollida:
  - DATABASE_URL / database_url
  - JIRA_URL / jira_url
  - JIRA_API_TOKEN / jira_api_token
  - JIRA_USER_EMAIL / jira_user_email
  - CMDB_HOST / cmdb_host
  Muudatused peavad olema .env failis rakendi juurkaustas või keskkonnamuutujates sõltuvalt teie seadistusest.

- config.json (aadressiraamat ja avastamise sätted)
  Faili asukoht: `src/core/configs/config.json`
  Redigeeri:
  - "all": lisage või muutke hostikirjeid (hostname, ip_address, user, type, enabled jne)
  - "discovery_settings": muutke `default_user`, `timeout`, `retry_count`, `parallel_discovery` jms
  Näide: ` "discovery_settings": { "default_user": "chronia", "timeout": 300 }`
  Ansible-plugin eelistab:
  1) otseselt antud kasutajat
  2) per-host `user` välja config.json-st
  3) `discovery_settings.default_user` väärtust

Käivitus / testimine
- Pärast venv aktiveerimist ja sõltuvuste paigaldamist:
  python src/main.py
  või
  ./scripts/start.sh

