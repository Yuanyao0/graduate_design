from pymongo import MongoClient
from config import MONGO_URI

collection_map = {
    ('simulation', 'hydrology'): 'simulated_hydrdata',
    ('simulation', 'biomass'): 'simulated_biodata',
    ('simulation', 'environment'): 'simulated_envidata',
    ('observation', 'hydrology'): 'observed_hydrdata',
    ('observation', 'biomass'): 'observed_biodata',
    ('observation', 'environment'): 'observed_envidata',
}

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client['MarineData']
# mongo_db.create_collection("simulated_hydrdata")
# mongo_db.create_collection("simulated_biodata")
# mongo_db.create_collection("simulated_envidata")
# mongo_db.create_collection("observed_hydrdata")
# mongo_db.create_collection("observed_biodata")
# mongo_db.create_collection("observed_envidata")

