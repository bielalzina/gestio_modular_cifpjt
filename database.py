import os
from google.cloud import firestore
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Initialize Firestore
project_id = os.getenv('FIRESTORE_PROJECT_ID')
print(f"DEBUG: Conectando a Firestore con Proyecto: {project_id}")
db = firestore.Client(project=project_id)

def get_next_id(collection_name):
    """
    Increments a counter in a specific document and returns the new value.
    Uses a transaction to ensure atomicity.
    """
    doc_ref = db.collection('counters').document(collection_name)

    @firestore.transactional
    def update_in_transaction(transaction, doc_ref):
        snapshot = doc_ref.get(transaction=transaction)
        if snapshot.exists:
            new_count = snapshot.get('count') + 1
            transaction.update(doc_ref, {'count': new_count})
        else:
            new_count = 1
            transaction.set(doc_ref, {'count': new_count})
        return new_count

    transaction = db.transaction()
    return update_in_transaction(transaction, doc_ref)

def add_registre(data):
    """
    Adds a registry entry (Entrada or Salida) to Firestore.
    """
    tipo = data.get('tipo', 'entrada').lower()
    collection = f'registre_{tipo}'
    
    # Get incremental ID
    reg_id = get_next_id(collection)
    
    # Prepare document data
    doc_data = data.copy()
    if 'tipo' in doc_data:
        del doc_data['tipo']
    doc_data['num_registre'] = reg_id
    doc_data['timestamp'] = datetime.utcnow()
    
    # Save to Firestore
    db.collection(collection).document(str(reg_id)).set(doc_data)
    return reg_id

def get_recent_registres(limit=5):
    """
    Retrieves the last 5 entries from both Entrada and Salida, ordered by timestamp.
    """
    entradas = db.collection('registre_entrada').order_by(
        'timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
    
    salidas = db.collection('registre_salida').order_by(
        'timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
    
    all_regs = []
    for doc in entradas:
        d = doc.to_dict()
        d['id'] = doc.id
        d['tipo_ui'] = 'Entrada'
        all_regs.append(d)
        
    for doc in salidas:
        d = doc.to_dict()
        d['id'] = doc.id
        d['tipo_ui'] = 'Sortida'
        all_regs.append(d)
        
    # Sort combined list by timestamp descending and take top N
    all_regs.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_regs[:limit]
