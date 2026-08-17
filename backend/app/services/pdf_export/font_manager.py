"""
字体管理器
负责字符分类、字体映射和文本分段
支持中文、英文、数学符号、科学符号的混排
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from loguru import logger


class FontCategory(Enum):
    """字符分类枚举"""
    CJK = "cjk"                    # 中日韩文字
    LATIN = "latin"               # 拉丁字母、数字
    GREEK = "greek"               # 希腊字母
    MATH_OPERATOR = "math"        # 数学运算符
    MATH_RELATION = "relation"    # 数学关系符
    SUPERSCRIPT = "super"         # 上标字符
    SUBSCRIPT = "sub"             # 下标字符
    ARROW = "arrow"               # 箭头符号
    MISC_SYMBOL = "misc"          # 其他符号
    PUNCTUATION = "punct"         # 标点符号


# ==================== 字符集定义 ====================

# 数学运算符
MATH_OPERATORS: Set[str] = {
    '∫', '∬', '∭', '∮', '∯', '∰',  # 积分符号
    '∑', '∏',                        # 求和、乘积
    '√', '∛', '∜',                   # 根号
    '∞', '∂', '∇', '∆',              # 无穷、偏导、梯度、增量
    '∀', '∃', '∄', '∅',              # 全称、存在、空集
    '∧', '∨', '¬', '⊕', '⊗',         # 逻辑运算
    '∩', '∪', '⊂', '⊃', '⊆', '⊇',    # 集合运算
    '⊄', '⊅', '∈', '∉', '∋', '∌',    # 属于关系
    '⟨', '⟩', '⌈', '⌉', '⌊', '⌋',    # 括号
    '∝', '∠', '∡', '⊥', '∥',         # 几何符号
    '⊙', '⊚', '⊛', '⊜', '⊝',         # 圆圈运算符
    '†', '‡', '∗', '⋆', '⋅', '∘',    # 其他运算符
    'ℕ', 'ℤ', 'ℚ', 'ℝ', 'ℂ',         # 数集符号
}

# 数学关系符
MATH_RELATIONS: Set[str] = {
    '≤', '≥', '≠', '≈', '≡', '≢',    # 比较关系
    '≪', '≫', '≮', '≯', '≰', '≱',    # 大小关系
    '∼', '≃', '≅', '≆', '≇',         # 相似关系
    '⊢', '⊣', '⊨', '⊩', '⊪',         # 逻辑关系
    '≺', '≻', '≼', '≽', '≾', '≿',    # 序关系
    '⊏', '⊐', '⊑', '⊒',              # 方形关系
    '∣', '∤', '∦',                   # 整除关系
    '≡', '≢', '≐', '≑',              # 等价关系
}

# 上标字符
SUPERSCRIPTS: Set[str] = {
    '⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹',  # 上标数字
    '⁺', '⁻', '⁼', '⁽', '⁾',                            # 上标运算符
    'ⁿ', 'ⁱ', 'ᵃ', 'ᵇ', 'ᶜ', 'ᵈ', 'ᵉ', 'ᶠ', 'ᵍ', 'ʰ',  # 上标字母
    'ʲ', 'ᵏ', 'ˡ', 'ᵐ', 'ᵒ', 'ᵖ', 'ʳ', 'ˢ', 'ᵗ', 'ᵘ',
    'ᵛ', 'ʷ', 'ˣ', 'ʸ', 'ᶻ',
    'ᵅ', 'ᵝ', 'ᵞ', 'ᵟ', 'ᵋ', 'ᶿ', 'ᶥ', 'ᶲ', 'ᵠ', 'ᵡ',  # 上标希腊字母
}

# 下标字符
SUBSCRIPTS: Set[str] = {
    '₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉',  # 下标数字
    '₊', '₋', '₌', '₍', '₎',                            # 下标运算符
    'ₐ', 'ₑ', 'ₒ', 'ₓ', 'ₔ', 'ₕ', 'ₖ', 'ₗ', 'ₘ', 'ₙ',  # 下标字母
    'ₚ', 'ₛ', 'ₜ',
    'ᵢ', 'ⱼ', 'ᵣ', 'ᵤ', 'ᵥ',                           # 下标字母（另一组）
    'ᵦ', 'ᵧ', 'ᵨ', 'ᵩ', 'ᵪ',                           # 下标希腊字母
}

# 箭头符号
ARROWS: Set[str] = {
    '→', '←', '↑', '↓', '↔', '↕',    # 基本箭头
    '⇒', '⇐', '⇑', '⇓', '⇔', '⇕',    # 双线箭头
    '↦', '↤', '↩', '↪', '↻', '↺',    # 特殊箭头
    '⟶', '⟵', '⟷', '⟹', '⟸', '⟺',    # 长箭头
    '↗', '↘', '↙', '↖',              # 斜箭头
    '⇀', '⇁', '↼', '↽',              # 半箭头
}

# 杂项符号
MISC_SYMBOLS: Set[str] = {
    '°', '′', '″', '‴',              # 度、分、秒
    '±', '∓', '×', '÷', '·',         # 运算符号
    '‰', '‱', '℃', '℉', 'Å',         # 单位符号
    '™', '©', '®', '℗',              # 商标版权
    '№', '℡', '℠', '℮',              # 其他符号
    '♠', '♣', '♥', '♦',              # 扑克符号
    '★', '☆', '✓', '✗', '✔', '✘',    # 星号、勾叉
    '§', '¶', '†', '‡', '※',         # 参考符号
    'µ', 'Ω', 'ℓ',                   # 单位字符
}


def classify_char(char: str) -> FontCategory:
    """
    对单个字符进行分类
    
    Args:
        char: 单个字符
        
    Returns:
        字符所属的FontCategory类别
    """
    if not char:
        return FontCategory.LATIN
    
    code = ord(char)
    
    # ==================== CJK 字符 ====================
    # CJK 统一表意文字
    if (0x4E00 <= code <= 0x9FFF or      # 基本区
        0x3400 <= code <= 0x4DBF or      # 扩展A
        0x20000 <= code <= 0x2A6DF or    # 扩展B
        0x2A700 <= code <= 0x2B73F or    # 扩展C
        0x2B740 <= code <= 0x2B81F or    # 扩展D
        0xF900 <= code <= 0xFAFF or      # 兼容汉字
        0x2F00 <= code <= 0x2FDF):       # 康熙部首
        return FontCategory.CJK
    
    # 日文假名
    if (0x3040 <= code <= 0x309F or      # 平假名
        0x30A0 <= code <= 0x30FF):       # 片假名
        return FontCategory.CJK
    
    # ==================== 希腊字母 ====================
    if (0x0370 <= code <= 0x03FF or      # 希腊字母和科普特字母
        0x1F00 <= code <= 0x1FFF):       # 扩展希腊字母
        return FontCategory.GREEK
    
    # ==================== 预定义字符集检查 ====================
    if char in MATH_OPERATORS:
        return FontCategory.MATH_OPERATOR
    
    if char in MATH_RELATIONS:
        return FontCategory.MATH_RELATION
    
    if char in SUPERSCRIPTS:
        return FontCategory.SUPERSCRIPT
    
    if char in SUBSCRIPTS:
        return FontCategory.SUBSCRIPT
    
    if char in ARROWS:
        return FontCategory.ARROW
    
    if char in MISC_SYMBOLS:
        return FontCategory.MISC_SYMBOL
    
    # ==================== Unicode 范围检查 ====================
    # 数学运算符区块
    if (0x2200 <= code <= 0x22FF or      # 数学运算符
        0x2A00 <= code <= 0x2AFF or      # 补充数学运算符
        0x27C0 <= code <= 0x27EF or      # 杂项数学符号-A
        0x2980 <= code <= 0x29FF):       # 杂项数学符号-B
        return FontCategory.MATH_OPERATOR
    
    # 箭头区块
    if (0x2190 <= code <= 0x21FF or      # 箭头
        0x27F0 <= code <= 0x27FF or      # 补充箭头-A
        0x2900 <= code <= 0x297F):       # 补充箭头-B
        return FontCategory.ARROW
    
    # 杂项符号区块
    if (0x2600 <= code <= 0x26FF or      # 杂项符号
        0x2700 <= code <= 0x27BF):       # 装饰符号
        return FontCategory.MISC_SYMBOL
    
    # 数学字母数字符号
    if 0x1D400 <= code <= 0x1D7FF:
        return FontCategory.MATH_OPERATOR
    
    # ==================== 标点符号 ====================
    # 中文标点
    if (0x3000 <= code <= 0x303F or      # CJK 符号和标点
        0xFF00 <= code <= 0xFFEF):       # 全角形式
        return FontCategory.PUNCTUATION
    
    # 通用标点
    if (0x2000 <= code <= 0x206F or      # 通用标点
        0x0020 <= code <= 0x002F or      # ASCII 标点
        0x003A <= code <= 0x0040 or
        0x005B <= code <= 0x0060 or
        0x007B <= code <= 0x007E):
        return FontCategory.PUNCTUATION
    
    # ==================== 拉丁字母和数字 ====================
    # 基本拉丁字母
    if (0x0041 <= code <= 0x005A or      # A-Z
        0x0061 <= code <= 0x007A or      # a-z
        0x0030 <= code <= 0x0039):       # 0-9
        return FontCategory.LATIN
    
    # 扩展拉丁字母（带变音符号）
    if (0x00C0 <= code <= 0x00FF or      # 拉丁补充
        0x0100 <= code <= 0x017F or      # 拉丁扩展-A
        0x0180 <= code <= 0x024F):       # 拉丁扩展-B
        return FontCategory.LATIN
    
    # ==================== 默认 ====================
    return FontCategory.LATIN


class FontManager:
    """
    字体管理器
    负责字体加载、字符分类和文本分段
    """
    
    # 默认字体配置
    DEFAULT_FONTS = {
        "main": "NotoSansSC-Regular.ttf",             # 主字体（中英文）
        "main_bold": "NotoSansSC-Bold.ttf",           # 主字体粗体
        "math": "NotoSansMath-Regular.ttf",           # 数学符号字体
        "symbols": "NotoSansSymbols-Regular.ttf",     # 特殊符号字体
    }
    
    # 字体类别映射：FontCategory -> 字体优先级列表
    FONT_CATEGORY_MAP = {
        FontCategory.CJK: ["main", "main_bold"],
        FontCategory.LATIN: ["main", "main_bold"],
        FontCategory.GREEK: ["main", "math"],
        FontCategory.MATH_OPERATOR: ["math", "main"],
        FontCategory.MATH_RELATION: ["math", "main"],
        FontCategory.SUPERSCRIPT: ["math", "main"],
        FontCategory.SUBSCRIPT: ["math", "main"],
        FontCategory.ARROW: ["math", "symbols"],
        FontCategory.MISC_SYMBOL: ["symbols", "math", "main"],
        FontCategory.PUNCTUATION: ["main"],
    }
    
    def __init__(self, fonts_dir: Optional[str] = None):
        """
        初始化字体管理器
        
        Args:
            fonts_dir: 字体文件目录路径，如果为None则使用默认路径
        """
        if fonts_dir:
            self.fonts_dir = Path(fonts_dir)
        else:
            # 默认使用服务目录下的fonts文件夹
            self.fonts_dir = Path(__file__).parent / "fonts"
        
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        
        # 已注册的字体：name -> path
        self.registered_fonts: Dict[str, Path] = {}
        
        # 字体覆盖范围缓存：name -> Set[int] (码点集合)
        self.font_cmaps: Dict[str, Set[int]] = {}
        
        # 是否已加载字体覆盖信息
        self._cmap_loaded = False
        
        logger.info(f"字体管理器初始化: fonts_dir={self.fonts_dir}")
    
    def get_fonts_dir(self) -> Path:
        """获取字体目录路径"""
        return self.fonts_dir
    
    def register_font(self, name: str, font_path: str) -> bool:
        """
        注册字体文件
        
        Args:
            name: 字体名称（用于引用）
            font_path: 字体文件路径
            
        Returns:
            是否注册成功
        """
        path = Path(font_path)
        if not path.exists():
            # 尝试在字体目录中查找
            path = self.fonts_dir / font_path
        
        if not path.exists():
            logger.warning(f"字体文件不存在: {font_path}")
            return False
        
        self.registered_fonts[name] = path
        logger.info(f"注册字体: {name} -> {path}")
        return True
    
    def auto_register_fonts(self) -> Dict[str, bool]:
        """
        自动注册默认字体
        
        Returns:
            注册结果：name -> success
        """
        results = {}
        for name, filename in self.DEFAULT_FONTS.items():
            font_path = self.fonts_dir / filename
            if font_path.exists():
                results[name] = self.register_font(name, str(font_path))
            else:
                results[name] = False
                logger.warning(f"默认字体文件不存在: {font_path}")
        return results
    
    def load_font_coverage(self, name: str) -> bool:
        """
        加载字体的字符覆盖范围
        
        Args:
            name: 字体名称
            
        Returns:
            是否加载成功
        """
        if name not in self.registered_fonts:
            return False
        
        font_path = self.registered_fonts[name]
        
        try:
            from fontTools.ttLib import TTFont
            font = TTFont(str(font_path))
            cmap = font.getBestCmap()
            self.font_cmaps[name] = set(cmap.keys()) if cmap else set()
            font.close()
            logger.info(f"加载字体覆盖范围: {name} -> {len(self.font_cmaps[name])} 个字符")
            return True
        except ImportError:
            logger.warning("fontTools 未安装，无法加载字体覆盖范围")
            return False
        except Exception as e:
            logger.error(f"加载字体覆盖范围失败: {name} | 错误: {str(e)}")
            return False
    
    def load_all_font_coverage(self) -> None:
        """加载所有已注册字体的覆盖范围"""
        for name in self.registered_fonts:
            self.load_font_coverage(name)
        self._cmap_loaded = True
    
    def get_font_path(self, name: str) -> Optional[Path]:
        """
        获取字体文件路径
        
        Args:
            name: 字体名称
            
        Returns:
            字体文件路径，如果不存在返回None
        """
        return self.registered_fonts.get(name)
    
    def get_font_for_char(self, char: str) -> str:
        """
        获取字符应使用的字体名称
        
        Args:
            char: 单个字符
            
        Returns:
            字体名称
        """
        category = classify_char(char)
        code = ord(char)
        
        # 获取该类别的字体优先级列表
        font_priority = self.FONT_CATEGORY_MAP.get(category, ["main"])
        
        # 如果已加载字体覆盖信息，检查字体是否支持该字符
        if self._cmap_loaded and self.font_cmaps:
            for font_name in font_priority:
                if font_name in self.font_cmaps:
                    if code in self.font_cmaps[font_name]:
                        return font_name
        
        # 默认返回优先级最高的已注册字体
        for font_name in font_priority:
            if font_name in self.registered_fonts:
                return font_name
        
        # 如果都没有，返回 main
        return "main"
    
    def segment_text(self, text: str) -> List[Tuple[str, str]]:
        """
        将文本按字体需求分段
        相同字体的连续字符合并为一段
        
        Args:
            text: 输入文本
            
        Returns:
            分段列表：[(font_name, text_segment), ...]
        """
        if not text:
            return []
        
        segments = []
        current_font = self.get_font_for_char(text[0])
        current_text = text[0]
        
        for char in text[1:]:
            font = self.get_font_for_char(char)
            if font == current_font:
                current_text += char
            else:
                segments.append((current_font, current_text))
                current_font = font
                current_text = char
        
        segments.append((current_font, current_text))
        return segments
    
    def get_font_info(self) -> Dict:
        """
        获取字体管理器的状态信息
        
        Returns:
            状态信息字典
        """
        return {
            "fonts_dir": str(self.fonts_dir),
            "fonts_dir_exists": self.fonts_dir.exists(),
            "registered_fonts": {
                name: str(path) for name, path in self.registered_fonts.items()
            },
            "font_coverage_loaded": self._cmap_loaded,
            "font_coverage": {
                name: len(cmap) for name, cmap in self.font_cmaps.items()
            } if self.font_cmaps else {},
            "default_fonts": self.DEFAULT_FONTS,
            "missing_fonts": [
                name for name, filename in self.DEFAULT_FONTS.items()
                if not (self.fonts_dir / filename).exists()
            ]
        }
    
    def check_fonts_available(self) -> Dict[str, bool]:
        """
        检查所有默认字体是否可用
        
        Returns:
            字体可用性：name -> available
        """
        return {
            name: (self.fonts_dir / filename).exists()
            for name, filename in self.DEFAULT_FONTS.items()
        }


# ==================== 工具函数 ====================

def get_char_category(char: str) -> str:
    """
    获取字符的类别名称（便捷函数）
    
    Args:
        char: 单个字符
        
    Returns:
        类别名称字符串
    """
    return classify_char(char).value


def analyze_text_composition(text: str) -> Dict:
    """
    分析文本的字符组成
    
    Args:
        text: 输入文本
        
    Returns:
        字符组成统计
    """
    from collections import Counter
    
    categories = Counter()
    for char in text:
        cat = classify_char(char)
        categories[cat.value] += 1
    
    total = len(text)
    return {
        "total_chars": total,
        "categories": dict(categories),
        "percentages": {
            cat: round(count / total * 100, 2)
            for cat, count in categories.items()
        } if total > 0 else {}
    }
