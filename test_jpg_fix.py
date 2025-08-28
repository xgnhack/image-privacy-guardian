#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JPG修复验证脚本
验证JPG文件是否能正确保存为JPEG格式
"""

import os
import shutil
from PIL import Image
from sanitizer_engine import ImageSanitizer

def test_jpg_fix():
    """测试JPG修复效果"""
    print("JPG修复验证测试")
    print("=" * 50)
    
    # 创建测试目录
    test_dir = r"d:\tmp\adobe\test\jpg_fix_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # 复制一个测试文件并重命名为英文
    source_jpg = r"d:\tmp\adobe\test\jpg\1-张艳华.jpg"
    test_jpg = os.path.join(test_dir, "test_image.jpg")
    
    if os.path.exists(source_jpg):
        shutil.copy2(source_jpg, test_jpg)
        print(f"✅ 复制测试文件: {test_jpg}")
    else:
        print(f"❌ 源文件不存在: {source_jpg}")
        return
    
    # 获取原始文件信息
    original_size = os.path.getsize(test_jpg)
    with open(test_jpg, 'rb') as f:
        original_header = f.read(10).hex()
    
    with Image.open(test_jpg) as img:
        original_format = img.format
        original_mode = img.mode
        original_dimensions = img.size
    
    print(f"\n原始文件信息:")
    print(f"  格式: {original_format}")
    print(f"  模式: {original_mode}")
    print(f"  尺寸: {original_dimensions}")
    print(f"  大小: {original_size:,} 字节")
    print(f"  文件头: {original_header}")
    
    # 使用ImageSanitizer处理
    output_jpg = os.path.join(test_dir, "processed_test_image.jpg")
    sanitizer = ImageSanitizer()
    
    print(f"\n使用ImageSanitizer处理...")
    success = sanitizer.clean_image(test_jpg, output_jpg)
    
    if not success:
        print(f"❌ 处理失败")
        return
    
    # 检查处理后的文件
    if not os.path.exists(output_jpg):
        print(f"❌ 输出文件不存在")
        return
    
    processed_size = os.path.getsize(output_jpg)
    with open(output_jpg, 'rb') as f:
        processed_header = f.read(10).hex()
    
    with Image.open(output_jpg) as img:
        processed_format = img.format
        processed_mode = img.mode
        processed_dimensions = img.size
    
    print(f"\n处理后文件信息:")
    print(f"  格式: {processed_format}")
    print(f"  模式: {processed_mode}")
    print(f"  尺寸: {processed_dimensions}")
    print(f"  大小: {processed_size:,} 字节")
    print(f"  文件头: {processed_header}")
    
    # 验证结果
    print(f"\n验证结果:")
    
    # 检查格式
    if processed_format == 'JPEG':
        print(f"✅ 格式正确: {processed_format}")
    else:
        print(f"❌ 格式错误: 期望JPEG，实际{processed_format}")
    
    # 检查文件头
    if processed_header.startswith('ffd8'):
        print(f"✅ JPEG文件头正确")
    else:
        print(f"❌ 文件头错误: {processed_header}")
    
    # 检查尺寸
    if processed_dimensions == original_dimensions:
        print(f"✅ 尺寸保持一致: {processed_dimensions}")
    else:
        print(f"❌ 尺寸改变: {original_dimensions} -> {processed_dimensions}")
    
    # 检查模式
    if processed_mode == original_mode:
        print(f"✅ 颜色模式保持一致: {processed_mode}")
    else:
        print(f"⚠️  颜色模式改变: {original_mode} -> {processed_mode}")
    
    # 文件大小变化
    size_change = processed_size - original_size
    size_change_percent = (size_change / original_size) * 100
    
    print(f"\n文件大小变化: {size_change:+,} 字节 ({size_change_percent:+.1f}%)")
    
    if abs(size_change_percent) < 10:
        print(f"✅ 文件大小变化在合理范围内")
    elif abs(size_change_percent) < 30:
        print(f"⚠️  文件大小变化较大")
    else:
        print(f"❌ 文件大小变化过大")
    
    print(f"\n测试完成！输出文件: {output_jpg}")

if __name__ == "__main__":
    test_jpg_fix()