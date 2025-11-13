# test_client.py
# Käivita see otse terminalist: python test_client.py

import logging
from src.core.configs.config import settings

# MUUDA SEDA IMPORT-RIDA VASTAVALT SELLELE, KUS SU KLIENDIFAL ASUB
# Ma eeldan, et see on 'src/api/clients/' kaustas:
from src.core.integrations.jira_client import JiraClient

# Seadista logimine, et näha, mis toimub
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test():
    logger.info("Initializing JiraClient...")
    try:
        client = JiraClient(settings=settings)
        logger.info("JiraClient initialized.")

        logger.info("Listing attributes for object type ID 13...")
        client.list_object_attributes("13")
        
        return

        logger.info("Testing create_asset...")

        # See on see JSON, mis Postmanis edukalt töötas
        new_asset_data = {
            "objectTypeId": 25,  # See on 'Ubuntu' tüübi ID
            "attributes": [
                {
                    "objectTypeAttributeId": 150,  # See on 'Name' atribuudi ID
                    "objectAttributeValues": [
                        {
                            "value": "Test objekt loodud python skriptist (create toimib)"
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 178,  # Hostname field
                    "objectAttributeValues": [
                        {
                            "value": "test-hostname"
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 177,  # IP Address field
                    "objectAttributeValues": [
                        {
                            "value": "192.168.1.1"
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 179,  # Architecture field
                    "objectAttributeValues": [
                        {
                            "value": "x86_64"
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 180,  # Processor Model field
                    "objectAttributeValues": [
                        {
                            "value": "Intel Xeon"
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 181,  # Physical CPUs field
                    "objectAttributeValues": [
                        {
                            "value": "4"
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 182,  # Virtual CPUs field
                    "objectAttributeValues": [
                        {
                            "value": "8"
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 187,  # OS field
                    "objectAttributeValues": [
                        {
                            "value": "Ubuntu 20.04"
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 175,  # Memory field
                    "objectAttributeValues": [
                        {
                            "value": 16.0  
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 176,  # Disk Usage field
                    "objectAttributeValues": [
                        {
                            "value": 500.0  
                        }
                    ]
                },
                {
                    "objectTypeAttributeId": 173,  # CPU Temperature field
                    "objectAttributeValues": [
                        {
                            "value": 45.0 
                        }
                    ]
                }
            ]
        }

        created_asset = client.create_asset(new_asset_data)
        logger.info(f"SUCCESS! Created new asset: {created_asset.objectKey}")
        new_asset_id = created_asset.id # Võtame ID edasisteks testideks

        # --- Test 2: UPDATE ASSET ---
        logger.info(f"Testing update_asset for new asset ID: {new_asset_id}...")
        update_data = {
            "attributes": [
                {
                    "objectTypeAttributeId": 150, # 'Name' atribuudi ID
                    "objectAttributeValues": [
                        {
                            "value": "UUENDATUD Nimi Pythonist (update toimib)"
                        }
                    ]
                }
            ]
        }
        #updated_asset = client.update_asset(new_asset_id, update_data)
        #logger.info(f"SUCCESS! Updated asset to: {updated_asset.label}")

        # --- Test 3: GET ASSET ---
        #logger.info(f"Testing get_asset_by_id for ID: {new_asset_id}...")
        #fetched_asset = client.get_asset_by_id(new_asset_id)
        #logger.info(f"SUCCESS! Fetched asset: {fetched_asset.label}")

        # --- Test 4: DELETE ASSET ---
        #logger.info(f"Testing delete_asset for ID: {new_asset_id}...")
        #delete_success = client.delete_asset(new_asset_id)
        #logger.info(f"SUCCESS! Asset deleted: {delete_success}")


    except Exception as e:
        logger.error(f"TEST FAILED: {e}", exc_info=True)

if __name__ == "__main__":
    run_test()