#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Utilidades para detectar recursos del sistema y optimizar según capacidad."""
import os
import multiprocessing
from typing import Dict, Any


def get_system_info() -> Dict[str, Any]:
    """Obtiene información del sistema."""
    info = {
        'cpu_count': multiprocessing.cpu_count(),
        'low_resource_mode': False,
        'max_workers': 1,
        'thread_limit': 1
    }
    
    # Detectar RAM
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            for line in meminfo.splitlines():
                if line.startswith('MemTotal:'):
                    total_kb = int(line.split()[1])
                    total_gb = total_kb / (1024 * 1024)
                    info['ram_gb'] = round(total_gb, 2)
                    if total_gb < 4:
                        info['low_resource_mode'] = True
                    break
    except Exception:
        info['ram_gb'] = None
    
    # Ajustar workers según recursos
    if info['low_resource_mode'] or info['cpu_count'] <= 2:
        info['max_workers'] = 1
        info['thread_limit'] = 2
    elif info['cpu_count'] >= 4:
        info['max_workers'] = min(2, info['cpu_count'] // 2)
        info['thread_limit'] = 4
    else:
        info['max_workers'] = 1
        info['thread_limit'] = 2
    
    return info


def apply_low_resource_mode():
    """Aplica variables de entorno para modo bajo recursos."""
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('MKL_NUM_THREADS', '1')
    os.environ.setdefault('NUMEXPR_NUM_THREADS', '1')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')


SYSTEM_INFO = get_system_info()
if SYSTEM_INFO['low_resource_mode']:
    apply_low_resource_mode()
