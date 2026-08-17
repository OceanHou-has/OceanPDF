"""
阅读顺序计算服务

负责为PDF页面中的元素计算阅读顺序
规则：
1. 每页的阅读顺序从1开始
2. 按照元素的block_id排序（自上而下）
3. 合并框使用第一个source_ids指向的元素的block_id作为排序依据
"""

from typing import List, Dict, Any


def extract_sort_key(element: Dict[str, Any]) -> str:
    """
    提取用于排序的key
    
    对于普通元素：返回其block_id
    对于合并元素：返回第一个source_ids指向的元素的block_id
    
    Args:
        element: 元素对象
        
    Returns:
        str: 用于排序的block_id
    """
    # 如果是合并元素且有source_ids
    if element.get('is_merged') and element.get('source_ids'):
        # 使用第一个源元素的block_id作为排序依据
        return element['source_ids'][0]
    
    # 普通元素直接返回block_id
    return element.get('block_id', '')


def calculate_reading_order(page_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    计算页面元素的阅读顺序
    
    只对可排序的元素类型（section_title, paragraph, list）分配阅读顺序
    文档标题不参与排序
    
    Args:
        page_elements: 页面元素列表
        
    Returns:
        List[Dict[str, Any]]: 更新了阅读顺序的元素列表
    """
    # 可排序的类型（不包括document_title）
    sortable_types = {'section_title', 'section_title_2', 'section_title_3', 'paragraph', 'list'}
    
    # 筛选出可排序的元素（已标注且类型在可排序列表中）
    sortable_elements = []
    for element in page_elements:
        # 跳过被合并的源元素
        if element.get('parent_id'):
            continue
        
        # 只处理已标注且类型可排序的元素
        if element.get('type') in sortable_types:
            sortable_elements.append(element)
    
    # 按照block_id排序（对于合并元素使用第一个source_ids的block_id）
    sortable_elements.sort(key=extract_sort_key)
    
    # 分配阅读顺序（从1开始）
    for idx, element in enumerate(sortable_elements, start=1):
        element['reading_order'] = idx
    
    # 清除不可排序元素的阅读顺序
    for element in page_elements:
        if element.get('type') not in sortable_types or element.get('parent_id'):
            element['reading_order'] = None
    
    return page_elements


def recalculate_page_reading_order(parsed_data: Dict[str, Any], page_num: int) -> Dict[str, Any]:
    """
    重新计算指定页面的阅读顺序
    
    Args:
        parsed_data: 完整的解析数据
        page_num: 页码（从0开始）
        
    Returns:
        Dict[str, Any]: 更新后的解析数据
    """
    if not parsed_data or 'pages' not in parsed_data:
        return parsed_data
    
    if page_num < 0 or page_num >= len(parsed_data['pages']):
        return parsed_data
    
    # 获取指定页面
    page = parsed_data['pages'][page_num]
    
    # 计算阅读顺序
    page['elements'] = calculate_reading_order(page['elements'])
    
    return parsed_data
