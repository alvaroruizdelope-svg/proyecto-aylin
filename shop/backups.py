"""Copias SQLite consistentes, fuera del proyecto. No contienen credenciales del código."""
from pathlib import Path
import os
import sqlite3
from django.conf import settings
from django.core.exceptions import ValidationError

def safe_path(value):
    raw=Path(value).expanduser()
    if raw.is_symlink(): raise ValidationError('No se admiten enlaces simbólicos.')
    p=raw.resolve()
    if p==settings.BASE_DIR or settings.BASE_DIR in p.parents: raise ValidationError('Las copias privadas deben estar fuera del proyecto.')
    return p

def backup_file(source,target):
    source=safe_path(source);target=safe_path(target)
    if source==target or target.exists() or not source.is_file(): raise ValidationError('Origen/destino de copia no válido; no se sobrescriben copias.')
    target.parent.mkdir(parents=True,exist_ok=True,mode=0o700);target.parent.chmod(0o700)
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600);os.close(fd)
    a=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True);b=sqlite3.connect(target)
    try:
        a.backup(b)
        if b.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValidationError('La copia no supera la comprobación de integridad.')
    finally:a.close();b.close()
    target.chmod(0o600)
    return target
