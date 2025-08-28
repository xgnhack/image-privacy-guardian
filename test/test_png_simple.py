#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的PNG透明度处理测试
"""

import os
import sys
sys.path.append('..')
from sanitizer_engine import ImageSanitizer
from PIL import Image

def test_png_processing():
    """
    测试PNG图像处理
    """
    png_dir = "png"
    output_dir = "output_png_test"
    
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if not os.path.exists(png_dir):
        print(f"PNG目录不存在: {png_dir}")
        return
    
    # 初始化清理器
    sanitizer = ImageSanitizer()
    
    png_files = [f for f in os.listdir(png_dir) if f.lower().endswith('.png')]
    
    if not png_files:
        print("没有找到PNG文件")
        return
    
    print(f"找到 {len(png_files)} 个PNG文件")
    
    for png_file in png_files[:3]:  # 测试前3个文件
        png_path = os.path.join(png_dir, png_file)
        output_path = os.path.join(output_dir, f"processed_{png_file}")
        
        print(f"\n测试PNG: {png_file}")
        print("=" * 50)
        
        try:
            # 获取原始图像信息
            with Image.open(png_path) as img:
                print(f"原始图像:")
                print(f"  格式: {img.format}")
                print(f"  模式: {img.mode}")
                print(f"  尺寸: {img.size}")
                print(f"  文件大小: {os.path.getsize(png_path):,} 字节")
                print(f"  是否有透明度: {img.mode in ('RGBA', 'LA')}")
            
            # 处理图像
            print("🖼️ 处理PNG图像...")
            result = sanitizer.clean_image(png_path, output_path)
            
            if result:
                print("✅ PNG图像清理完成")
                
                # 获取处理后图像信息
                with Image.open(output_path) as processed_img:
                    print(f"处理后图像:")
                    print(f"  格式: {processed_img.format}")
                    print(f"  模式: {processed_img.mode}")
                    print(f"  尺寸: {processed_img.size}")
                    print(f"  文件大小: {os.path.getsize(output_path):,} 字节")
                    print(f"  是否有透明度: {processed_img.mode in ('RGBA', 'LA')}")
                    
                    # 检查文件大小变化
                    original_size = os.path.getsize(png_path)
                    processed_size = os.path.getsize(output_path)
                    size_change = processed_size - original_size
                    size_change_percent = (size_change / original_size) * 100
                    
                    print(f"文件大小变化: {size_change:+,} 字节 ({size_change_percent:+.1f}%)")
                    
                    # 检查透明度是否保持
                    with Image.open(png_path) as original:
                        if original.mode in ('RGBA', 'LA') and processed_img.mode in ('RGBA', 'LA'):
                            print("✅ 透明度已保持")
                        elif original.mode in ('RGBA', 'LA') and processed_img.mode not in ('RGBA', 'LA'):
                            print("❌ 透明度丢失")
                        else:
                            print("ℹ️ 原图无透明度")
            else:
                print("❌ PNG图像清理失败")
                
        except Exception as e:
            print(f"❌ 处理失败: {e}")
    
    print(f"\n测试完成！处理后的PNG图像保存在: {output_dir}")

if __name__ == "__main__":
    test_png_processing()