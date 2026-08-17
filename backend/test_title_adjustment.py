"""
测试标题bbox调整功能
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.translation.pretranslation_service import PretranslationService
from app.services.annotation.paper_analyzer import PaperAnalyzer


def test_title_adjustment():
    """测试标题bbox调整功能"""
    
    # 使用示例PDF
    pdf_name = "Slope stability and failure dynamics of rainfall-induced landslide-Algorithm and applications"
    
    print(f"📄 测试PDF: {pdf_name}")
    print("=" * 80)
    
    # 1. 加载强段落信息
    print("\n1️⃣ 加载强段落信息...")
    paper_analyzer = PaperAnalyzer()
    metadata = paper_analyzer.load_metadata(pdf_name)
    
    if not metadata:
        print("❌ 未找到元数据，请先上传并解析PDF")
        return
    
    paper_layout = metadata.get("paper_layout")
    if not paper_layout:
        print("❌ 未找到论文版面信息")
        return
    
    print(f"✅ 强段落宽度: {paper_layout.get('strong_paragraph_width')} px")
    print(f"✅ 栏数: {paper_layout.get('column_count')}")
    print(f"✅ 栏位置: {paper_layout.get('column_positions')}")
    
    # 2. 生成预翻译文件（会自动调整标题bbox）
    print("\n2️⃣ 生成预翻译文件（调整标题bbox）...")
    pretrans_service = PretranslationService()
    
    result = pretrans_service.generate_pretranslation(
        pdf_name=pdf_name,
        source_lang="en",
        target_lang="zh-CN",
        aggregate_titles=False,
        use_dps=False,
        force=True  # 强制重新生成以看到调整效果
    )
    
    if not result.get("success"):
        print(f"❌ 生成预翻译文件失败: {result.get('error')}")
        return
    
    print(f"✅ 预翻译文件生成成功")
    print(f"   文件路径: {result.get('file_path')}")
    
    # 3. 检查调整后的bbox
    print("\n3️⃣ 检查标题元素的bbox调整...")
    pretrans_path = Path(result.get("file_path"))
    
    if not pretrans_path.exists():
        print("❌ 预翻译文件不存在")
        return
    
    with open(pretrans_path, 'r', encoding='utf-8') as f:
        pretrans_data = json.load(f)
    
    # 统计标题元素
    title_tasks = []
    for task in pretrans_data.get("translation_tasks", []):
        element_type = task.get("element_type")
        if element_type in {"section_title", "section_title_2", "section_title_3"}:
            if task.get("is_aggregated"):
                # 聚合任务：检查每个子块
                for block in task.get("aggregated_blocks", []):
                    title_tasks.append({
                        "type": block["element_type"],
                        "bbox": block["bbox"],
                        "text": block["text"][:50] + "..." if len(block["text"]) > 50 else block["text"]
                    })
            else:
                # 独立任务
                title_tasks.append({
                    "type": element_type,
                    "bbox": task.get("bbox"),
                    "text": task.get("source_text", "")[:50] + "..." if len(task.get("source_text", "")) > 50 else task.get("source_text", "")
                })
    
    print(f"\n找到 {len(title_tasks)} 个标题元素：")
    print("-" * 80)
    
    strong_width = paper_layout.get("strong_paragraph_width")
    column_positions = paper_layout.get("column_positions", [])
    column_xs = [col.get("x") for col in column_positions]
    
    for i, task in enumerate(title_tasks[:10], 1):  # 只显示前10个
        bbox = task["bbox"]
        if bbox:
            x0, y0, x1, y1 = bbox
            width = x1 - x0
            
            # 检查宽度是否匹配强段落
            width_match = abs(width - strong_width) < 1.0  # 允许1像素误差
            
            # 检查X坐标是否对齐到栏位置
            x_aligned = any(abs(x0 - col_x) < 1.0 for col_x in column_xs)
            
            status = "✅" if (width_match and x_aligned) else "⚠️"
            
            print(f"{i}. {status} {task['type']}")
            print(f"   文本: {task['text']}")
            print(f"   bbox: [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]")
            print(f"   宽度: {width:.1f} px {'✓' if width_match else f'(预期: {strong_width})'}")
            print(f"   X坐标: {x0:.1f} {'✓' if x_aligned else f'(预期: {column_xs})'}")
            print()
    
    if len(title_tasks) > 10:
        print(f"... 还有 {len(title_tasks) - 10} 个标题元素未显示")
    
    print("=" * 80)
    print("✅ 测试完成！")


if __name__ == "__main__":
    test_title_adjustment()
