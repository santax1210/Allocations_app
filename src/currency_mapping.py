"""
Mapeo centralizado de nombres de divisas de Refinitiv a códigos ISO 4217.

Este módulo contiene el mapeo único y autoritativo que debe usarse en todo el sistema
para convertir nombres largos de monedas (ej: "US DOLLAR", "CHILEAN PESO") a códigos
ISO estándar (ej: "USD", "CLP").

IMPORTANTE: Este mapeo es crítico para asegurar que las allocations externas (Refinitiv)
coincidan exactamente con las allocations internas. Cualquier error aquí causará
inconsistencias en las distribuciones de moneda.
"""

# Mapeo único y autoritativo de nombres Refinitiv -> Códigos ISO 4217
CURRENCY_MAP_REFINITIV_TO_ISO = {
    # Monedas principales (mayúsculas - formato Refinitiv típico)
    'CHILEAN PESO': 'CLP',
    'US DOLLAR': 'USD',
    'EURO': 'EUR',
    'HONG KONG DOLLAR': 'HKD',
    'JAPANESE YEN': 'JPY',
    'UK POUND STERLING': 'GBP',
    'BRITISH POUND': 'GBP',
    'SWISS FRANC': 'CHF',
    'CANADIAN DOLLAR': 'CAD',
    'AUSTRALIAN DOLLAR': 'AUD',
    'NEW ZEALAND DOLLAR': 'NZD',
    'CHINESE YUAN': 'CNY',
    'CHINESE R YUAN HK': 'CNY',
    'CHINESE YUAN (OFFSHORE)': 'CNY',
    'SOUTH KOREAN WON': 'KRW',
    'KOREAN WON': 'KRW',
    'SINGAPORE DOLLAR': 'SGD',
    'MEXICAN PESO': 'MXN',
    'BRAZILIAN REAL': 'BRL',
    'ARGENTINIAN PESO': 'ARS',
    'COLOMBIAN PESO': 'COP',
    'PERU NEW SOL': 'PEN',
    'PERUVIAN SOL': 'PEN',
    'SOUTH AFRICAN RAND': 'ZAR',
    'DANISH KRONE': 'DKK',
    'NORWEGIAN KRONE': 'NOK',
    'SWEDISH KRONA': 'SEK',
    'CZECH KORUNA': 'CZK',
    'CZECH CROWN': 'CZK',
    'SAUDI ARABIAN RIYAL': 'SAR',
    'SAUDI RIYAL': 'SAR',
    
    # Categoría especial para monedas agrupadas y monedas menos relevantes
    'OTROS': 'OTROS',
    'OTHERS': 'OTROS',
    'OTHER': 'OTROS',
    'OTHER CURRENCIES': 'OTROS',
    'OTRAS MONEDAS': 'OTROS',
    
    # Monedas específicas clasificadas como "OTROS"
    'VIETNAMESE DONG': 'OTROS',
    'SRI LANKA RUPEE': 'OTROS',
    'SRI LANKAN RUPEE': 'OTROS',
    'VIETNAM DONG': 'OTROS',
    'NETHERLANDS GUILDER': 'OTROS',
    'DUTCH GUILDER': 'OTROS',
    
    # Categorías regionales que Refinitiv agrupa como "OTROS"
    'ROMANIA': 'OTROS',
    'ROMANIAN LEU': 'OTROS',
    'REST OF THE WORLD': 'OTROS',
    'REST OF WORLD': 'OTROS',
    'OTHER EUROPEAN CURRENCIES': 'OTROS',
    'OTHER ASIAN CURRENCIES': 'OTROS',
    'LATIN AMERICA': 'OTROS',
    'OTHER LATIN AMERICAN CURRENCIES': 'OTROS',
    
    # Otras monedas globales
    'TAIWAN DOLLAR': 'TWD',
    'UAE DIRHAM': 'AED',
    'EGYPTIAN POUND': 'EGP',
    'INDIAN RUPEE': 'INR',
    'INDONESIA RUPIAH': 'IDR',
    'ISRAELI SHEKEL': 'ILS',
    'KUWAIT DINAR': 'KWD',
    'KAZAKHSTAN TENGE': 'KZT',
    'MALAYSIAN RINGGIT': 'MYR',
    'PHILIPPINE PESO': 'PHP',
    'POLISH ZLOTY': 'PLN',
    'RUSSIAN RUBLE': 'RUB',
    'THAI BAHT': 'THB',
    'TURKISH LIRA': 'TRY',
    'URUGUAY PESO URUGUAYO': 'UYU',
    'UKRAINIAN HRYVNIA': 'UAH',
    'BENIN CFA FRANC': 'XOF',
    
    # Variantes con capitalización mixta (Title Case)
    'Australian Dollar': 'AUD',
    'Brazilian Real': 'BRL',
    'Canadian Dollar': 'CAD',
    'Chilean Peso': 'CLP',
    'Chinese Yuan': 'CNY',
    'Chinese Yuan (Offshore)': 'CNY',
    'Colombian Peso': 'COP',
    'Danish Krone': 'DKK',
    'Dominican Republic Peso': 'DOP',
    'Egyptian Pound': 'EGP',
    'Euro': 'EUR',
    'Hong Kong Dollar': 'HKD',
    'Indian Rupee': 'INR',
    'Indonesia Rupiah': 'IDR',
    'Israeli Shekel': 'ILS',
    'Japanese Yen': 'JPY',
    'Malaysian Ringgit': 'MYR',
    'Mexican Peso': 'MXN',
    'New Zealand Dollar': 'NZD',
    'Nigerian Naira': 'NGN',
    'Norwegian Krone': 'NOK',
    'Philippine Peso': 'PHP',
    'Polish Zloty': 'PLN',
    'Singapore Dollar': 'SGD',
    'South African Rand': 'ZAR',
    'South Korean Won': 'KRW',
    'Swedish Krona': 'SEK',
    'Swiss Franc': 'CHF',
    'Czech Koruna': 'CZK',
    'Czech Crown': 'CZK',
    'Saudi Arabian Riyal': 'SAR',
    'Saudi Riyal': 'SAR',
    'Taiwan Dollar': 'TWD',
    'Thai Baht': 'THB',
    'Turkish Lira': 'TRY',
    'UAE Dirham': 'AED',
    'UK Pound Sterling': 'GBP',
    'US Dollar': 'USD',
    'Paraguayan Guarani': 'PYG',
    
    # Categoría especial (variantes Title Case)
    'Otros': 'OTROS',
    'Others': 'OTROS',
    'Other': 'OTROS',
    'Other Currencies': 'OTROS',
    
    # Monedas específicas clasificadas como "OTROS" (Title Case)
    'Vietnamese Dong': 'OTROS',
    'Sri Lanka Rupee': 'OTROS',
    'Sri Lankan Rupee': 'OTROS',
    'Vietnam Dong': 'OTROS',
    'Netherlands Guilder': 'OTROS',
    'Dutch Guilder': 'OTROS',
    
    # Categorías regionales (Title Case)
    'Romania': 'OTROS',
    'Romanian Leu': 'OTROS',
    'Rest of the World': 'OTROS',
    'Rest of World': 'OTROS',
    'Other European Currencies': 'OTROS',
    'Other Asian Currencies': 'OTROS',
    'Latin America': 'OTROS',
    'Other Latin American Currencies': 'OTROS',
    
    # Variantes adicionales encontradas en datos reales
    'POUND STERLING': 'GBP',
    'YEN': 'JPY',
    'YUAN': 'CNY',
    'WON': 'KRW',
    'RENMINBI': 'CNY',
    
    # Nuevas monedas exóticas mapeadas a OTROS (2025-01-27)
    'ALBANIA LEK': 'OTROS', 'ALL': 'OTROS',
    'ARMENIA DRAM': 'OTROS', 'AMD': 'OTROS',
    'AZERBAIJANI MANAT': 'OTROS', 'AZN': 'OTROS',
    'DOMINICAN REPUBLIC PESO': 'OTROS', 'DOP': 'OTROS',
    'HUNGARY FORINT': 'OTROS', 'HUF': 'OTROS',
    'KAZAKHSTAN': 'OTROS', 'KAZAKHSTAN TENGE': 'OTROS', 'KZT': 'OTROS',
    'KUWAIT': 'OTROS', 'KUWAITI DINAR': 'OTROS', 'KWD': 'OTROS',
    'NIGERIAN NAIRA': 'OTROS', 'NGN': 'OTROS',
    'PARAGUAYAN GUARANI': 'OTROS', 'PYG': 'OTROS',
    'UZBEKISTAN SOM': 'OTROS', 'UZBEKISTAN': 'OTROS', 'UZS': 'OTROS',
    
    # Valores especiales a ignorar/filtrar
    'ROUNDING ADJUSTMENT': 'OTROS',  # Ajuste de redondeo, agrupar en OTROS
    'Rounding Adjustment': 'OTROS',
}


def normalize_currency_name(currency_name: str) -> str:
    """
    Normaliza un nombre de moneda de Refinitiv a su código ISO 4217.
    
    Args:
        currency_name: Nombre de la moneda en formato Refinitiv (ej: "US DOLLAR", "Euro")
    
    Returns:
        Código ISO de 3 letras (ej: "USD", "EUR"), o el nombre original si no se encuentra mapeo
    
    Examples:
        >>> normalize_currency_name("US DOLLAR")
        'USD'
        >>> normalize_currency_name("Chilean Peso")
        'CLP'
        >>> normalize_currency_name("EURO")
        'EUR'
    """
    if not currency_name or not isinstance(currency_name, str):
        return currency_name
    
    # Intentar mapeo directo primero (preservando caso)
    if currency_name in CURRENCY_MAP_REFINITIV_TO_ISO:
        return CURRENCY_MAP_REFINITIV_TO_ISO[currency_name]
    
    # Intentar con mayúsculas (formato más común de Refinitiv)
    normalized = currency_name.upper().strip()
    if normalized in CURRENCY_MAP_REFINITIV_TO_ISO:
        return CURRENCY_MAP_REFINITIV_TO_ISO[normalized]
    
    # Si no se encuentra, devolver el nombre original
    # (esto permite que códigos ISO ya normalizados pasen sin cambios)
    return currency_name


def validate_currency_code(code: str) -> bool:
    """
    Valida si un código parece ser un código ISO 4217 válido.
    
    Args:
        code: Código de moneda a validar
    
    Returns:
        True si parece un código ISO válido (3 letras mayúsculas)
    """
    if not code or not isinstance(code, str):
        return False
    return len(code) == 3 and code.isupper() and code.isalpha()


def get_all_iso_codes() -> set:
    """
    Obtiene el conjunto de todos los códigos ISO únicos en el mapeo.
    
    Returns:
        Set de códigos ISO de 3 letras (ej: {'USD', 'CLP', 'EUR', ...})
    """
    return set(CURRENCY_MAP_REFINITIV_TO_ISO.values())


def verify_currency_consistency(external_currencies: list, internal_currencies: list) -> dict:
    """
    Verifica la consistencia entre códigos de monedas externas e internas.
    
    Args:
        external_currencies: Lista de códigos de moneda de allocations externas
        internal_currencies: Lista de códigos de moneda de allocations internas
    
    Returns:
        Dict con información de consistencia:
        - 'consistent': bool
        - 'external_only': set de monedas solo en externas
        - 'internal_only': set de monedas solo en internas
        - 'common': set de monedas en ambas
    """
    ext_set = set(external_currencies)
    int_set = set(internal_currencies)
    
    return {
        'consistent': ext_set == int_set,
        'external_only': ext_set - int_set,
        'internal_only': int_set - ext_set,
        'common': ext_set & int_set,
        'external_count': len(ext_set),
        'internal_count': len(int_set),
        'common_count': len(ext_set & int_set)
    }
