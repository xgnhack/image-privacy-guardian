#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JPG保存调试脚本
用于验证JPG图片保存是否正确
"""

import os
from PIL import Image
from sanitizer_engine import ImageSanitizer

def debug_jpg_save():
    """调试JPG保存问题"""
    # 测试文件路径
    test_jpg = r"d:\tmp\adobe\test\jpg\1-张艳华.jpg"
    output_jpg = r"d:\tmp\adobe\test\debug_output.jpg"
    
    print("JPG保存调试测试")
    print("=" * 40)
    
    # 检查原始文件
    if not os.path.exists(test_jpg):
        print(f"测试文件不存在: {test_jpg}")
        return
    
    # 获取原始文件信息
    with Image.open(test_jpg) as img:
        print(f"原始文件信息:")
        print(f"  格式: {img.format}")
        print(f"  模式: {img.mode}")
        print(f"  尺寸: {img.size}")
        print(f"  文件大小: {os.path.getsize(test_jpg):,} 字节")
    
    # 使用sanitizer处理
    sanitizer = ImageSanitizer()
    print(f"\n使用ImageSanitizer处理...")
    success = sanitizer.clean_image(test_jpg, output_jpg)
    
    if success and os.path.exists(output_jpg):
        # 检查输出文件
        with Image.open(output_jpg) as img:
            print(f"\n输出文件信息:")
            print(f"  格式: {img.format}")
            print(f"  模式: {img.mode}")
            print(f"  尺寸: {img.size}")
            print(f"  文件大小: {os.path.getsize(output_jpg):,} 字节")
        
        # 检查文件头
        with open(output_jpg, 'rb') as f:
            header = f.read(10)
            print(f"\n文件头 (前10字节): {header.hex()}")
            
            # JPEG文件应该以 FF D8 开头
            if header[:2] == b'\xff\xd8':
                print(f"  ✅ 正确的JPEG文件头")
            elif header[:8] == b'\x89PNG\r\n\x1a\n':
                print(f"  ❌ 这是PNG文件头，不是JPEG！")
            else:
                print(f"  ⚠️  未知文件格式")
    else:
        print(f"处理失败或输出文件不存在")
    
    # 测试直接PIL保存
    print(f"\n测试直接PIL保存...")
    direct_output = r"d:\tmp\adobe\test\debug_direct.jpg"
    
    with Image.open(test_jpg) as img:
        # 清除EXIF数据
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(list(img.getdata()))
        
        # 保存为JPEG
        clean_img.save(direct_output, 'JPEG', quality=95, optimize=True)
    
    if os.path.exists(direct_output):
        with Image.open(direct_output) as img:
            print(f"直接保存结果:")
            print(f"  格式: {img.format}")
            print(f"  模式: {img.mode}")
            print(f"  文件大小: {os.path.getsize(direct_output):,} 字节")
        
        # 检查文件头
        with open(direct_output, 'rb') as f:
            header = f.read(10)
            print(f"  文件头: {header.hex()}")
            if header[:2] == b'\xff\xd8':
                print(f"  ✅ 正确的JPEG文件头")
            else:
                print(f"  ❌ 错误的文件头")

if __name__ == "__main__":
    debug_jpg_save()