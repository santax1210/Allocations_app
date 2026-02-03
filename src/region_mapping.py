
# Diccionario de Mapeo de Regiones
# Keys: Nombres normalizados (lowercase, stripped) desde Refinitiv (headers del CSV externo)
# Values: Nombres de columnas internas en 'allocations 2.csv'

REGION_MAP_REFINITIV_TO_INTERNAL = {
    # AFRICA
    "africa eme.": "Africa Eme.",
    "africa front.": "Africa Front.",
    "middle_east_&_africa": "Africa Eme.", # Asignación aproximada, user review needed
    
    # ASIA
    "asia des.": "Asia Des.",
    "asia eme.": "Asia Eme.",
    "asia front.": "Asia Front.",
    "apac_(ex_japan)_fi": "Asia Des.",
    "people's_republic_of_china": "Asia Eme.",
    "peopleâ€™s_republic_of_china": "Asia Eme.", # Encoding artifact handling
    "peopleã¢â\x82¬â\x84¢s_republic_of_china": "Asia Eme.", # Exact CSV encoding
    "uzbekistan": "Asia Eme.",
    "azerbaijan": "Asia Eme.",
    
    # CHILE
    "chile": "Chile",
    
    # EUROPA
    "europa des.": "Europa Des.",
    "europe_eq": "Europa Des.",
    "europe_fi": "Europa Des.",
    "europa eme.": "Europa Eme.",
    "europa front.": "Europa Front.",
    "faroe_islands": "Europa Des.",
    
    # LATAM
    "latam eme.": "Latam Eme.",
    "latam front.": "Latam Front.",
    "mexice": "Latam Eme.", # Typos handling
    "mexico": "Latam Eme.",
    "honduras": "Latam Front.",
    "latam eme. ex-chile": "Latam Eme. ex-Chile",
    
    # MIDDLE EAST
    "m. oriente eme.": "M. Oriente Eme.",
    "m. oriente front.": "M. Oriente Front.",
    "türkiye": "M. Oriente Eme.",
    "turkiye": "M. Oriente Eme.",
    "tãƒâ¼rkiye": "M. Oriente Eme.",
    "tã\x83â¼rkiye": "M. Oriente Eme.", # Exact CSV encoding
    
    # NORTEAMERICA
    "norteamerica": "Norteamerica",
    "north_america_fi": "Norteamerica",
    
    # OCEANIA
    "oceanía": "Oceanía",
    "oceania": "Oceanía",
    "oceanã\xada": "Oceanía",
    "australia_&_new_zealand": "Oceanía",
    
    # GLOBAL / OTROS / CASH
    "global des.": "Global Des.",
    "global eme.": "Global Eme.",
    "globales": "Globales",
    "world": "Globales",
    "cash/equiv": "Otros", # O Caja? Asumiremos Otros por ahora para cuadrar con columnas internas
    "cash_&_forwards": "Otros",
    "otros": "Otros",
    "technology": "Temáticos", # Asumo Temáticos para sectores específicos
    
    # FALLBACKS / GENERIC
    "emerging_market_fi": "Global Eme.",
    "n/a": "N/A"
}

def normalize_region_name(name):
    """Normaliza el nombre de la región para búsqueda insensible a mayúsculas/espacios."""
    if not isinstance(name, str):
        return str(name)
    return name.strip().lower()

def get_internal_region_name(refinitiv_name):
    """Devuelve el nombre de la columna interna correspondiente."""
    norm_name = normalize_region_name(refinitiv_name)
    return REGION_MAP_REFINITIV_TO_INTERNAL.get(norm_name, None)
