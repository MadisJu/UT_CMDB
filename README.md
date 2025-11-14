# Automated CMDB

We are four University of Tartu students, and this repository contains a project for an **Automated Configuration Management Database (CMDB)** for **Eesti Pank (Bank of Estonia)**.

The solution will:
- Collect configuration data from **Accounting, Supporting IT services and Information system services** departments.
- Synchronize data automatically into **Jira Asset Management**

Our goal is to provide Eesti Pank with a single source of truth for IT assets, reduce manual work and improve compliance reporting.

--------------------------

# Setup for Bank of Estonia

- Juhised installimiseks ja käivitamiseks.
1. Runi ```./build.sh``` online masinas, millel peab olema sama tüüp OS, kus seda käivitatakse.
2. Peale build.sh runimist tuleb kopeerida tekkinud /wheelhouse kaust offline masina root kausa. Seejärel tuleb käivitada käsk ```./install.sh ./wheelhouse``` offline masinas.
3. Configureeri failid (Mida on vaja muuta on näha allpool.)
4. Et käivitada, tuleb jooksutada käsklus ```./start.sh```.

## Oluline: 
**.env**
- .env: kopeeri vajadusel .env.example (Github Wikis olemas) → .env ja redigeeri oma keskkonnamuutujad (andmebaasi aadress, Jira token, e-posti kasutaja jms). .env fail peab olema /src/core/configs/ kaustas. Samuti on vaja lisada .env faili Ansible inventory path.
  Näited muutujatest, mida kontrollida:
  - DATABASE_URL / database_url
  - JIRA_URL / jira_url
  - JIRA_API_TOKEN / jira_api_token
  - JIRA_USER_EMAIL / jira_user_email
  - CMDB_HOST / cmdb_host
  - JIRA_ASSET_WORKSPACE_ID
  - JIRA_CLOUD_ID
  - ANSIBLE_INVENTORY_PATH

Praegu on scheduler seadisatud jooksutama ja syncima iga 30-ne minuti tagant. Seda veel envis muuta ei saa, kuid saab src/scheduler/celery_app.py.

Selles kaustas on ka jira_field_map.json, mille kaudu saab Jira asseti atribuute ühendada. Jira objektide id-d saab kätte minnes Jira Asset Manageri veebilehele. Seejärel tuleb valida schemade alt serverid vms, siis üks serveritest, atribuudid (üleval paremal) ja siis on juba võimalik kopeerida sealt vastavate atribuutide id-d.

Vaja on ka muuta failis /src/core/services/jira_field_mapper_service.py os_object_type_ids id-d. Ehk siis tuleb seal muuta ära vastavate OS-de id-d.

  ### Algselt oleks soovitatav testida järgmiselt:
* Esiteks tuleks teha src\core\configs\inventory.ini failist koopia, kus on esialgu ainult Linuxi masinad.
* Kui Linuxi masinatega töötab probleemideta, siis saab edasi liikuda Windowsi masinate juurde (ei ole garanteeritud et windowsi masinad tootavad)

