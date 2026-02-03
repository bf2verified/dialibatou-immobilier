from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import os
import base64
from datetime import datetime, timezone

app = FastAPI(title="DIALIBATOU BTP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "dialibatou")
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
properties_col = db["properties"]
lots_col = db["lots"]

# Pydantic Models
class Agent(BaseModel):
    na: str = "Mame Cheikh Ndiaye"
    ph: str = "+221 77 709 61 44"

class Video(BaseModel):
    type: str
    src: str
    name: Optional[str] = None

class PropertyBase(BaseModel):
    ti: str
    de: Optional[str] = ""
    ty: str = "Appartement"
    tr: str = "Vente"
    pr: int = 0
    nb: str = ""
    su: int = 0
    ro: int = 0
    be: int = 0
    ba: int = 0
    fe: List[str] = []
    im: List[str] = []
    vd: List[Video] = []
    ft: bool = False
    vi: int = 0
    ag: Agent = Agent()

class PropertyCreate(PropertyBase):
    pass

class PropertyResponse(PropertyBase):
    id: str

class LotBase(BaseModel):
    loc: str
    zone: str = ""
    lots: int = 0
    dispo: int = 0
    su: int = 0
    pr: int = 0
    st: str = "Disponible"
    fe: List[str] = []

class LotCreate(LotBase):
    pass

class LotResponse(LotBase):
    id: str

# Default properties data
DEFAULT_PROPERTIES = [
    {"id":"p1","ti":"Luxueux Appartement Vue Mer Almadies","de":"Superbe appartement de standing avec vue imprenable sur l'océan. Résidence sécurisée, finitions haut de gamme. 3 chambres, terrasse 25m².","ty":"Appartement","tr":"Vente","pr":185000000,"nb":"Almadies","su":180,"ro":5,"be":3,"ba":2,"fe":["Piscine","Parking","Sécurité 24h","Vue mer"],"im":["https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800","https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800"],"ft":True,"vi":342,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p2","ti":"Appartement Moderne 4P Mermoz","de":"Magnifique appartement contemporain entièrement rénové. Salon double avec balcon, cuisine équipée, chambres climatisées.","ty":"Appartement","tr":"Vente","pr":125000000,"nb":"Mermoz","su":140,"ro":4,"be":3,"ba":2,"fe":["Parking","Climatisation","Balcon"],"im":["https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800","https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800"],"ft":True,"vi":256,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p3","ti":"Studio Meublé Plateau","de":"Studio meublé et équipé au cœur du Plateau. Emplacement premium près ministères et banques.","ty":"Appartement","tr":"Vente","pr":45000000,"nb":"Plateau","su":35,"ro":1,"be":0,"ba":1,"fe":["Climatisation","Meublé"],"im":["https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800"],"ft":False,"vi":189,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p4","ti":"F3 à Louer Ngor","de":"Charmant F3 dans le village de Ngor, près de la plage. Séjour lumineux, cuisine équipée, 2 chambres, terrasse.","ty":"Appartement","tr":"Location","pr":450000,"nb":"Ngor","su":85,"ro":3,"be":2,"ba":1,"fe":["Terrasse","Climatisation"],"im":["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800"],"ft":False,"vi":178,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p5","ti":"Penthouse avec Piscine Privée","de":"Penthouse d'exception de 280m² avec piscine privée sur toit-terrasse. 4 chambres en suite. Vue panoramique 360°.","ty":"Appartement","tr":"Vente","pr":450000000,"nb":"Almadies","su":280,"ro":7,"be":4,"ba":4,"fe":["Piscine","Terrasse","Vue mer","Parking"],"im":["https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=800"],"ft":True,"vi":567,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p6","ti":"Villa Contemporaine Point E","de":"Splendide villa de 6 chambres. Piscine chauffée, jardin paysager, finitions luxe. Bureau, salle de sport.","ty":"Villa","tr":"Vente","pr":380000000,"nb":"Point E","su":450,"ro":10,"be":6,"ba":7,"fe":["Piscine","Jardin","Parking","Sécurité 24h"],"im":["https://images.unsplash.com/photo-1613977257363-707ba9348227?w=800"],"ft":True,"vi":478,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p7","ti":"Villa Coloniale Rénovée Fann","de":"Charmante villa coloniale entièrement rénovée. Hauts plafonds, parquet, vérandas, jardin tropical.","ty":"Villa","tr":"Vente","pr":295000000,"nb":"Fann","su":350,"ro":8,"be":4,"ba":3,"fe":["Jardin","Parking","Terrasse"],"im":["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],"ft":False,"vi":267,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p8","ti":"Villa Moderne Sacré-Cœur","de":"Belle villa moderne de 5 chambres. Construction récente, panneaux solaires. Double salon, garage 2 voitures.","ty":"Villa","tr":"Vente","pr":220000000,"nb":"Sacré-Cœur","su":280,"ro":8,"be":5,"ba":4,"fe":["Jardin","Parking","Sécurité 24h"],"im":["https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=800"],"ft":True,"vi":356,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p9","ti":"Villa à Louer Ouakam","de":"Grande villa sur 2 niveaux, idéale pour résidentiel ou professionnel. Jardin 400m², parking 5 véhicules.","ty":"Villa","tr":"Location","pr":2500000,"nb":"Ouakam","su":380,"ro":10,"be":6,"ba":4,"fe":["Jardin","Parking","Sécurité 24h"],"im":["https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=800"],"ft":False,"vi":198,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p10","ti":"Villa Pieds dans l'Eau Ngor","de":"Exceptionnelle villa front de mer. Accès direct plage privée. 5 chambres, piscine à débordement. Propriété rare.","ty":"Villa","tr":"Vente","pr":850000000,"nb":"Ngor","su":520,"ro":12,"be":5,"ba":5,"fe":["Piscine","Jardin","Vue mer","Terrasse"],"im":["https://images.unsplash.com/photo-1613977257592-4871e5fcd7c4?w=800"],"ft":True,"vi":723,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p11","ti":"Terrain Viabilisé 500m² Saly","de":"Excellent terrain viabilisé à Saly, 500m de la plage. Eau, électricité, assainissement. Idéal villa de vacances.","ty":"Terrain","tr":"Vente","pr":35000000,"nb":"Saly","su":500,"ro":0,"be":0,"ba":0,"fe":[],"im":["https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800"],"ft":True,"vi":234,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
    {"id":"p12","ti":"Grand Terrain 1200m² Mbour","de":"Terrain de 1200m² avec titre foncier, accès bitumé. Parfait pour immeuble locatif ou complexe résidentiel.","ty":"Terrain","tr":"Vente","pr":55000000,"nb":"Mbour","su":1200,"ro":0,"be":0,"ba":0,"fe":[],"im":["https://images.unsplash.com/photo-1628624747186-a941c476b7ef?w=800"],"ft":False,"vi":156,"ag":{"na":"Mame Cheikh Ndiaye","ph":"+221 77 709 61 44"}},
]

DEFAULT_LOTS = [
    {"id":"lot1","loc":"Bambilor","zone":"Zone A","lots":50,"dispo":35,"su":200,"pr":5000000,"st":"Disponible","fe":["Titre foncier","Eau","Électricité","Voirie"]},
    {"id":"lot2","loc":"Thiès","zone":"Cité Dialibatou","lots":100,"dispo":72,"su":150,"pr":3500000,"st":"Disponible","fe":["Titre foncier","Eau","Électricité"]},
    {"id":"lot3","loc":"Diass","zone":"Proche AIBD","lots":80,"dispo":45,"su":250,"pr":7000000,"st":"Disponible","fe":["Titre foncier","Eau","Électricité","Proximité aéroport"]},
    {"id":"lot4","loc":"Bayakh","zone":"Lac Rose","lots":60,"dispo":28,"su":300,"pr":6000000,"st":"Disponible","fe":["Titre foncier","Eau","Vue lac"]},
    {"id":"lot5","loc":"Sébikotane","zone":"Zone industrielle","lots":40,"dispo":15,"su":200,"pr":5500000,"st":"Limité","fe":["Titre foncier","Eau","Électricité","Voirie"]},
    {"id":"lot6","loc":"Keur Massar","zone":"Extension","lots":120,"dispo":89,"su":150,"pr":6500000,"st":"Disponible","fe":["Titre foncier","Eau","Électricité","Transport"]},
    {"id":"lot7","loc":"Kounoune","zone":"Résidentielle","lots":45,"dispo":20,"su":200,"pr":4500000,"st":"Limité","fe":["Titre foncier","Eau","Électricité"]},
    {"id":"lot8","loc":"Sindia","zone":"Village","lots":70,"dispo":55,"su":350,"pr":4000000,"st":"Disponible","fe":["Délibération","Eau"]},
]

def init_database():
    """Initialize database with default data if empty"""
    if properties_col.count_documents({}) == 0:
        properties_col.insert_many(DEFAULT_PROPERTIES)
    if lots_col.count_documents({}) == 0:
        lots_col.insert_many(DEFAULT_LOTS)

@app.on_event("startup")
async def startup():
    init_database()

# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "DIALIBATOU BTP API"}

# ============ PROPERTIES ENDPOINTS ============

@app.get("/api/properties", response_model=List[PropertyResponse])
async def get_properties():
    """Get all properties"""
    props = list(properties_col.find({}, {"_id": 0}))
    return props

@app.get("/api/properties/{prop_id}", response_model=PropertyResponse)
async def get_property(prop_id: str):
    """Get a single property by ID"""
    prop = properties_col.find_one({"id": prop_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop

@app.post("/api/properties", response_model=PropertyResponse)
async def create_property(prop: PropertyCreate):
    """Create a new property"""
    prop_dict = prop.model_dump()
    prop_dict["id"] = f"p{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    properties_col.insert_one(prop_dict)
    return PropertyResponse(**prop_dict)

@app.put("/api/properties/{prop_id}", response_model=PropertyResponse)
async def update_property(prop_id: str, prop: PropertyCreate):
    """Update an existing property"""
    prop_dict = prop.model_dump()
    prop_dict["id"] = prop_id
    result = properties_col.update_one({"id": prop_id}, {"$set": prop_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    return PropertyResponse(**prop_dict)

@app.delete("/api/properties/{prop_id}")
async def delete_property(prop_id: str):
    """Delete a property"""
    result = properties_col.delete_one({"id": prop_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": "Property deleted successfully"}

# ============ LOTS ENDPOINTS ============

@app.get("/api/lots", response_model=List[LotResponse])
async def get_lots():
    """Get all lots"""
    lots = list(lots_col.find({}, {"_id": 0}))
    return lots

@app.get("/api/lots/{lot_id}", response_model=LotResponse)
async def get_lot(lot_id: str):
    """Get a single lot by ID"""
    lot = lots_col.find_one({"id": lot_id}, {"_id": 0})
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot

@app.post("/api/lots", response_model=LotResponse)
async def create_lot(lot: LotCreate):
    """Create a new lot"""
    lot_dict = lot.model_dump()
    lot_dict["id"] = f"lot{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    lots_col.insert_one(lot_dict)
    return LotResponse(**lot_dict)

@app.put("/api/lots/{lot_id}", response_model=LotResponse)
async def update_lot(lot_id: str, lot: LotCreate):
    """Update an existing lot"""
    lot_dict = lot.model_dump()
    lot_dict["id"] = lot_id
    result = lots_col.update_one({"id": lot_id}, {"$set": lot_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lot not found")
    return LotResponse(**lot_dict)

@app.delete("/api/lots/{lot_id}")
async def delete_lot(lot_id: str):
    """Delete a lot"""
    result = lots_col.delete_one({"id": lot_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lot not found")
    return {"message": "Lot deleted successfully"}

# ============ BULK OPERATIONS ============

@app.post("/api/properties/bulk")
async def bulk_update_properties(properties: List[PropertyCreate]):
    """Replace all properties with new list"""
    properties_col.delete_many({})
    props_list = []
    for i, prop in enumerate(properties):
        prop_dict = prop.model_dump()
        prop_dict["id"] = f"p{int(datetime.now(timezone.utc).timestamp() * 1000) + i}"
        props_list.append(prop_dict)
    if props_list:
        properties_col.insert_many(props_list)
    return {"message": f"{len(props_list)} properties saved"}

@app.post("/api/lots/bulk")
async def bulk_update_lots(lots: List[LotCreate]):
    """Replace all lots with new list"""
    lots_col.delete_many({})
    lots_list = []
    for i, lot in enumerate(lots):
        lot_dict = lot.model_dump()
        lot_dict["id"] = f"lot{int(datetime.now(timezone.utc).timestamp() * 1000) + i}"
        lots_list.append(lot_dict)
    if lots_list:
        lots_col.insert_many(lots_list)
    return {"message": f"{len(lots_list)} lots saved"}

@app.post("/api/reset")
async def reset_database():
    """Reset database to default data"""
    properties_col.delete_many({})
    lots_col.delete_many({})
    properties_col.insert_many(DEFAULT_PROPERTIES)
    lots_col.insert_many(DEFAULT_LOTS)
    return {"message": "Database reset to default data"}

# ============ IMAGE UPLOAD ============

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image and return base64 data URL"""
    contents = await file.read()
    base64_data = base64.b64encode(contents).decode('utf-8')
    content_type = file.content_type or "image/jpeg"
    data_url = f"data:{content_type};base64,{base64_data}"
    return {"url": data_url, "filename": file.filename}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
