"""文件解析器模块"""

from .base import BaseParser
from .excel import ExcelParser
from .csv import CSVParser
from .json import JSONParser
from .txt import TXTParser
from .pdf import PDFParser
from .word import WordParser
from .image import ImageParser


def get_parser(file_path: str) -> BaseParser:
    """根据文件类型获取对应的解析器"""
    file_type = BaseParser.get_file_type(file_path)
    
    parsers = {
        "excel": ExcelParser(),
        "csv": CSVParser(),
        "json": JSONParser(),
        "txt": TXTParser(),
        "pdf": PDFParser(),
        "word": WordParser(),
        "image": ImageParser(),
    }
    
    parser = parsers.get(file_type)
    if parser is None:
        raise ValueError(f"不支持的文件类型: {file_type}")
    
    if not parser.can_parse(file_path):
        raise ValueError(f"无法解析该文件: {file_path}")
    
    return parser
