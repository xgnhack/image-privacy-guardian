#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终JPG处理质量测试
"""

import os
import sys
from PIL import Image

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sanitizer_engine import ImageSanitizer

def test_jpg_processing():
    """测试JPG图像处理"""
    print("🚀 开始JPG图像处理最终测试\n")
    
    # 创建输出目录
    output_dir = "output_jpg_final_test"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 查找JPG文件
    jpg_files = []
    for file in os.listdir('.'):
        if file.lower().endswith(('.jpg', '.jpeg')):
            jpg_files.append(file)
    
    if not jpg_files:
        print("❌ 未找到JPG文件")
        return
    
    print(f"找到 {len(jpg_files)} 个JPG文件\n")
    
    # 创建图像清理器
    sanitizer = ImageSanitizer()
    
    for jpg_file in jpg_files:
        print(f"测试JPG: {jpg_file}")
        print("=" * 50)
        
        try:
            # 获取原始图像信息
            with Image.open(jpg_file) as original_img:
                original_size = os.path.getsize(jpg_file)
                print(f"原始图像:")
                print(f"  格式: {original_img.format}")
                print(f"  模式: {original_img.mode}")
                print(f"  尺寸: {original_img.size}")
                print(f"  文件大小: {original_size:,} 字节")
            
            # 处理图像
            output_path = os.path.join(output_dir, f"processed_{jpg_file}")
            print(f"🖼️ 处理JPG图像...")
            
            result = sanitizer.clean_image(jpg_file, output_path)
            
            if result:
                print("✅ JPG图像清理完成")
                
                # 获取处理后图像信息
                if os.path.exists(output_path):
                    with Image.open(output_path) as processed_img:
                        processed_size = os.path.getsize(output_path)
                        print(f"处理后图像:")
                        print(f"  格式: {processed_img.format}")
                        print(f"  模式: {processed_img.mode}")
                        print(f"  尺寸: {processed_img.size}")
                        print(f"  文件大小: {processed_size:,} 字节")
                        
                        # 计算文件大小变化
                        size_diff = processed_size - original_size
                        size_change_percent = (size_diff / original_size) * 100
                        
                        if size_diff > 0:
                            print(f"文件大小变化: +{size_diff:,} 字节 (+{size_change_percent:.1f}%)")
                        else:
                            print(f"文件大小变化: {size_diff:,} 字节 ({size_change_percent:.1f}%)")
                        
                        # 评估质量保持情况
                        if abs(size_change_percent) <= 5:
                            print("✅ 文件大小变化在可接受范围内")
                        elif abs(size_change_percent) <= 10:
                            print("⚠️ 文件大小变化较大但可接受")
                        else:
                            print("❌ 文件大小变化过大")
                else:
                    print("❌ 处理后的文件不存在")
            else:
                print("❌ JPG图像清理失败")
                
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
        
        print()
    
    print(f"测试完成！处理后的JPG图像保存在: {output_dir}")

if __name__ == "__main__":
    test_jpg_processing()