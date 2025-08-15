import os
from enum import Enum
from typing import Dict, Optional, List

from PySide6.QtCore import QCoreApplication


class Language(Enum):
    ENGLISH = "en"
    FRENCH = "fr"

    @staticmethod
    def from_env(value: Optional[str]) -> "Language":
        if not value:
            return Language.ENGLISH
        val = value.lower()
        if val.startswith("fr"):
            return Language.FRENCH
        return Language.ENGLISH


class AppConfig:
    """Lightweight runtime config.

    Currently reads language from environment variable LANG (default 'en').
    """

    def __init__(self) -> None:
        self.language: Language = Language.from_env(os.getenv("LANG", "en"))


# Singleton app config (used by translate_* helpers when language not provided)
app_config = AppConfig()


class I18nMixin:
    """Provide self.str() to mark strings for Qt translation with view class context."""

    def str(self, text: str) -> str:
        return QCoreApplication.translate(self.__class__.__name__, text)


def tr_mod(context: str, text: str) -> str:
    """Module-level translation helper when no instance (e.g., logs, main)."""
    return QCoreApplication.translate(context, text)


# Non-Qt translatable labels (e.g., DB-fixed values, column names not emitted via Qt)
# Extend these dictionaries as needed. If key is missing, the key itself is returned.
_NON_QT_LABELS: Dict[str, Dict[str, str]] = {
    # Example keys; replace/extend with your real DB-fixed labels
    # "STATUS": {"en": "Status", "fr": "Statut"},
    # "TYPE": {"en": "Type", "fr": "Type"},
}


def nx(key: str, lang: Optional[Language] = None) -> str:
    """Return localized string for a non-Qt label.

    - key: logical key present in _NON_QT_LABELS
    - lang: override current language; if None, derives from LANG env
    """
    language = lang or Language.from_env(os.getenv("LANG", "en"))
    lang_code = language.value
    mapping = _NON_QT_LABELS.get(key)
    if not mapping:
        return key
    return mapping.get(lang_code, mapping.get("en", key))


# =============================================================================
# Domain dictionaries (FR/EN) for non-Qt managed labels shown in Python code
# Keys are French canonical values (as stored in DB); values are per-language labels.
# Extend as needed and/or add more languages later.
# =============================================================================

# 1) MENUS
MENU_LABELS: Dict[str, Dict[Language, str]] = {
    "Fichier": {Language.FRENCH: "Fichier", Language.ENGLISH: "File"},
    "Gestion": {Language.FRENCH: "Gestion", Language.ENGLISH: "Management"},
    "Stock": {Language.FRENCH: "Stock", Language.ENGLISH: "Inventory"},
    "Maintenance": {Language.FRENCH: "Maintenance", Language.ENGLISH: "Maintenance"},
    "Aide": {Language.FRENCH: "Aide", Language.ENGLISH: "Help"},
}

# 2) FILTRES GENERIQUES
filter_labels: Dict[str, Dict[Language, str]] = {
    "All": {Language.FRENCH: "Tous", Language.ENGLISH: "All"},
    "AllOpen": {Language.FRENCH: "Tous Ouverts", Language.ENGLISH: "All Open"},
    "AllClosed": {Language.FRENCH: "Tous Fermés", Language.ENGLISH: "All Closed"},
    "Unassigned": {Language.FRENCH: "Non Assigné", Language.ENGLISH: "Unassigned"},
    "Afficher archives": {Language.FRENCH: "Afficher archives", Language.ENGLISH: "Show archives"},
}

# 3) ENTRETIEN / OT: Types, Priorités, Statuts
type_translations: Dict[str, Dict[Language, str]] = {
    "Preventif": {Language.FRENCH: "Préventif", Language.ENGLISH: "Preventive"},
    "Correctif": {Language.FRENCH: "Correctif", Language.ENGLISH: "Corrective"},
    "Amelioratif": {Language.FRENCH: "Amélioratif", Language.ENGLISH: "Improvement"},
    "Demande": {Language.FRENCH: "Demande", Language.ENGLISH: "Request"},
    "Reglementaire": {Language.FRENCH: "Réglementaire", Language.ENGLISH: "Regulatory"},
}

priority_translations: Dict[str, Dict[Language, str]] = {
    "Basse": {Language.FRENCH: "Basse", Language.ENGLISH: "Low"},
    "Normale": {Language.FRENCH: "Normale", Language.ENGLISH: "Normal"},
    "Moyenne": {Language.FRENCH: "Moyenne", Language.ENGLISH: "Medium"},
    "Haute": {Language.FRENCH: "Haute", Language.ENGLISH: "High"},
    "Urgente": {Language.FRENCH: "Urgente", Language.ENGLISH: "Urgent"},
}

status_translations: Dict[str, Dict[Language, str]] = {
    "Créé": {Language.FRENCH: "Créé", Language.ENGLISH: "Created"},
    "Planifié": {Language.FRENCH: "Planifié", Language.ENGLISH: "Scheduled"},
    "EnCours": {Language.FRENCH: "En Cours", Language.ENGLISH: "In Progress"},
    "Terminé": {Language.FRENCH: "Terminé", Language.ENGLISH: "Completed"},
    "Annulé": {Language.FRENCH: "Annulé", Language.ENGLISH: "Cancelled"},
    "Suspendu": {Language.FRENCH: "Suspendu", Language.ENGLISH: "Suspended"},
    "AttentePieces": {Language.FRENCH: "Attente Pièces", Language.ENGLISH: "Waiting for Parts"},
    "Pret": {Language.FRENCH: "Prêt", Language.ENGLISH: "Ready"},
    "Archivé": {Language.FRENCH: "Archivé", Language.ENGLISH: "Archived"},
}

# 4) COMMANDES (achats) : Statuts
purchase_order_status_translations: Dict[str, Dict[Language, str]] = {
    "Brouillon": {Language.FRENCH: "Brouillon", Language.ENGLISH: "Draft"},
    "Validee": {Language.FRENCH: "Validee", Language.ENGLISH: "Validated"},
    "Envoyee": {Language.FRENCH: "Envoyee", Language.ENGLISH: "Sent"},
    "Partielle": {Language.FRENCH: "Partielle", Language.ENGLISH: "Partial"},
    "Livree": {Language.FRENCH: "Livree", Language.ENGLISH: "Delivered"},
    "Annulee": {Language.FRENCH: "Annulee", Language.ENGLISH: "Cancelled"},
}

# =============================================================================
# Translation helpers (forward: FR key -> label in target lang)
# If language is None, use app_config.language
# =============================================================================

def translate_menu_label(label_key: str, language: Optional[Language] = None) -> str:
    language = language or app_config.language
    return MENU_LABELS.get(label_key, {}).get(language, label_key)


def translate_label(label_key: str, language: Optional[Language] = None) -> str:
    language = language or app_config.language
    return filter_labels.get(label_key, {}).get(language, label_key)


def translate_type(ot_type: str, language: Optional[Language] = None) -> str:
    language = language or app_config.language
    return type_translations.get(ot_type, {}).get(language, ot_type)


def translate_priority(priority: str, language: Optional[Language] = None) -> str:
    language = language or app_config.language
    return priority_translations.get(priority, {}).get(language, priority)


def translate_status(status: str, language: Optional[Language] = None) -> str:
    language = language or app_config.language
    return status_translations.get(status, {}).get(language, status)


def translate_purchase_order_status(status: str, language: Optional[Language] = None) -> str:
    language = language or app_config.language
    return purchase_order_status_translations.get(status, {}).get(language, status)

# =============================================================================
# Reverse helpers (UI label in source_language -> French canonical key)
# Useful when storing back to DB.
# =============================================================================

def _reverse_lookup(d: Dict[str, Dict[Language, str]], translated: str, source_language: Language) -> str:
    if source_language == Language.FRENCH:
        return translated
    for fr_key, mapping in d.items():
        if mapping.get(source_language) == translated:
            return fr_key
    return translated


def reverse_translate_status(translated_status: str, source_language: Optional[Language] = None) -> str:
    source_language = source_language or app_config.language
    return _reverse_lookup(status_translations, translated_status, source_language)


def reverse_translate_type(translated_type: str, source_language: Optional[Language] = None) -> str:
    source_language = source_language or app_config.language
    return _reverse_lookup(type_translations, translated_type, source_language)


def reverse_translate_priority(translated_priority: str, source_language: Optional[Language] = None) -> str:
    source_language = source_language or app_config.language
    return _reverse_lookup(priority_translations, translated_priority, source_language)


def reverse_translate_purchase_order_status(translated_status: str, source_language: Optional[Language] = None) -> str:
    source_language = source_language or app_config.language
    return _reverse_lookup(purchase_order_status_translations, translated_status, source_language)
