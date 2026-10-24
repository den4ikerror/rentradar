from services.sources.olx import OlxAdapter
from services.sources.domria import DomRiaAdapter
from services.sources.lunua import LunUaAdapter
from services.sources.rieltor import RieltorAdapter
from services.sources.flatfy import FlatfyAdapter
from services.sources.base import SourceAdapter

# Додати нове джерело: створити клас за зразком services/sources/olx.py
# і дописати його інстанс у цей список — більше нічого чіпати не треба,
# scheduler.py автоматично підхопить його в наступному скані.
ALL_SOURCES: list[SourceAdapter] = [
    OlxAdapter(),
    DomRiaAdapter(),
    LunUaAdapter(),
    RieltorAdapter(),
    FlatfyAdapter(),
]
