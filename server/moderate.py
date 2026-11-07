"""Moderación LOCAL por operador del sistema; no es un panel web privado.
Requiere acceso al directorio privado del servidor, protegido por permisos del SO.
No contiene credenciales ni abre endpoints de administración.
"""
import argparse
import os
import time
from app import Store, default_private_directory

def decide(store, review_id, decision, reason):
    if decision not in ('approved', 'rejected') or not reason or len(reason.strip()) < 5:
        raise ValueError('Decisión o motivo no válidos.')
    with store.connect() as db:
        row = db.execute('SELECT id,status FROM reviews WHERE id=?', (review_id,)).fetchone()
        if not row:
            raise ValueError('Opinión no encontrada.')
        if decision == 'approved' and row['status'] != 'approved':
            db.execute('UPDATE reviews SET published_at=COALESCE(published_at,?) WHERE id=?', (time.time(), review_id))
        db.execute('UPDATE reviews SET status=?,reason=? WHERE id=?', (decision, reason.strip(), review_id))
        db.execute('INSERT INTO moderation (review_id,decision,reason,created) VALUES (?,?,?,?)',
                   (review_id, decision, reason.strip(), time.time()))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Moderación manual local de opiniones demo')
    parser.add_argument('--list', action='store_true', help='Listar opiniones pendientes para revisión humana')
    parser.add_argument('--id', type=int)
    parser.add_argument('--decision', choices=['approved', 'rejected'])
    parser.add_argument('--reason')
    args = parser.parse_args()
    store = Store(os.environ.get('SHOP_PRIVATE_DIR', default_private_directory()))
    if args.list:
        with store.connect() as db:
            for row in db.execute("SELECT id,product,public_name,rating,comment,verified FROM reviews WHERE status='pending'"):
                print(dict(row))
    elif args.id and args.decision and args.reason:
        decide(store, args.id, args.decision, args.reason)
        print('Moderación registrada. Las opiniones negativas legítimas deben aprobarse igual que las positivas.')
    else:
        parser.error('Utiliza --list o --id, --decision y --reason.')
