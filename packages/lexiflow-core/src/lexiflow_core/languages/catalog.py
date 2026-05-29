"""Built-in searchable language catalog."""

from __future__ import annotations

from lexiflow_core.languages.models import LanguageInfo

_CATALOG: tuple[LanguageInfo, ...] = (
    LanguageInfo(iso="ar", name="Arabic", flag="🇸🇦"),
    LanguageInfo(iso="bg", name="Bulgarian", flag="🇧🇬"),
    LanguageInfo(iso="ca", name="Catalan", flag="🇪🇸"),
    LanguageInfo(iso="zh", name="Chinese", flag="🇨🇳"),
    LanguageInfo(iso="hr", name="Croatian", flag="🇭🇷"),
    LanguageInfo(iso="cs", name="Czech", flag="🇨🇿"),
    LanguageInfo(iso="da", name="Danish", flag="🇩🇰"),
    LanguageInfo(iso="nl", name="Dutch", flag="🇳🇱"),
    LanguageInfo(iso="en", name="English", flag="🇬🇧"),
    LanguageInfo(iso="et", name="Estonian", flag="🇪🇪"),
    LanguageInfo(iso="fi", name="Finnish", flag="🇫🇮"),
    LanguageInfo(iso="fr", name="French", flag="🇫🇷"),
    LanguageInfo(iso="de", name="German", flag="🇩🇪"),
    LanguageInfo(iso="el", name="Greek", flag="🇬🇷"),
    LanguageInfo(iso="he", name="Hebrew", flag="🇮🇱"),
    LanguageInfo(iso="hi", name="Hindi", flag="🇮🇳"),
    LanguageInfo(iso="hu", name="Hungarian", flag="🇭🇺"),
    LanguageInfo(iso="id", name="Indonesian", flag="🇮🇩"),
    LanguageInfo(iso="it", name="Italian", flag="🇮🇹"),
    LanguageInfo(iso="ja", name="Japanese", flag="🇯🇵"),
    LanguageInfo(iso="ko", name="Korean", flag="🇰🇷"),
    LanguageInfo(iso="lv", name="Latvian", flag="🇱🇻"),
    LanguageInfo(iso="lt", name="Lithuanian", flag="🇱🇹"),
    LanguageInfo(iso="no", name="Norwegian", flag="🇳🇴"),
    LanguageInfo(iso="pl", name="Polish", flag="🇵🇱"),
    LanguageInfo(iso="pt", name="Portuguese", flag="🇵🇹"),
    LanguageInfo(iso="ro", name="Romanian", flag="🇷🇴"),
    LanguageInfo(iso="sk", name="Slovak", flag="🇸🇰"),
    LanguageInfo(iso="sl", name="Slovenian", flag="🇸🇮"),
    LanguageInfo(iso="es", name="Spanish", flag="🇪🇸"),
    LanguageInfo(iso="sv", name="Swedish", flag="🇸🇪"),
    LanguageInfo(iso="tr", name="Turkish", flag="🇹🇷"),
    LanguageInfo(iso="uk", name="Ukrainian", flag="🇺🇦"),
    LanguageInfo(iso="vi", name="Vietnamese", flag="🇻🇳"),
)

_BY_ISO: dict[str, LanguageInfo] = {lang.iso: lang for lang in _CATALOG}


def list_languages() -> list[LanguageInfo]:
    """Return all predefined catalog languages."""
    return list(_CATALOG)


def get_language(iso: str) -> LanguageInfo:
    """Return catalog metadata for an ISO 639-1 code."""
    try:
        return _BY_ISO[iso]
    except KeyError as exc:
        raise KeyError(f"unknown language: {iso}") from exc
