#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试脚本 - 测试JPG和PNG处理效果
"""

import os
import sys
from PIL import Image

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sanitizer_engine import ImageSanitizer

def test_comprehensive():
    print("🚀 开始综合图像处理测试")
    print()
    
    # 初始化清理器
    sanitizer = ImageSanitizer()
    
    # 测试文件夹
    test_folder = "d:/tmp/adobe/test"
    output_folder = os.path.join(test_folder, "output_comprehensive_test")
    os.makedirs(output_folder, exist_ok=True)
    
    # 查找JPG和PNG文件
    jpg_files = [f for f in os.listdir(test_folder) if f.lower().endswith(('.jpg', '.jpeg'))]# 扫描PNG文件
    png_folder = os.path.join(test_folder, 'png')
    png_files = []
    if os.path.exists(png_folder):
        png_files = [f for f in os.listdir(png_folder) if f.lower().endswith('.png')]
    
    print(f"找到 {len(jpg_files)} 个JPG文件")
    print(f"找到 {len(png_files)} 个PNG文件")
    print()
    
    # 测试JPG文件
    print("=" * 60)
    print("测试JPG文件处理")
    print("=" * 60)
    
    jpg_results = []
    for jpg_file in jpg_files[:3]:  # 限制测试数量
        input_path = os.path.join(test_folder, jpg_file)
        output_path = os.path.join(output_folder, f"processed_{jpg_file}")
        
        print(f"\n测试JPG: {jpg_file}")
        print("=" * 50)
        
        try:
            # 获取原始信息
            with Image.open(input_path) as img:
                original_format = img.format
                original_mode = img.mode
                original_size = img.size
                original_file_size = os.path.getsize(input_path)
                
            print(f"原始图像:")
            print(f"  格式: {original_format}")
            print(f"  模式: {original_mode}")
            print(f"  尺寸: {original_size}")
            print(f"  文件大小: {original_file_size:,} 字节")
            
            # 处理图像
            success = sanitizer.clean_image(
                input_path=input_path,
                output_path=output_path,
                remove_metadata=True,
                advanced_cleaning=False
            )
            
            if success:
                # 获取处理后信息
                with Image.open(output_path) as img:
                    processed_format = img.format
                    processed_mode = img.mode
                    processed_size = img.size
                    processed_file_size = os.path.getsize(output_path)
                    
                print(f"处理后图像:")
                print(f"  格式: {processed_format}")
                print(f"  模式: {processed_mode}")
                print(f"  尺寸: {processed_size}")
                print(f"  文件大小: {processed_file_size:,} 字节")
                
                # 计算变化
                size_change = processed_file_size - original_file_size
                size_change_percent = (size_change / original_file_size) * 100
                
                print(f"文件大小变化: {size_change:+,} 字节 ({size_change_percent:+.1f}%)")
                
                # 评估结果
                if abs(size_change_percent) <= 10:  # 10%以内认为可接受
                    print("✅ 文件大小变化在可接受范围内")
                    status = "PASS"
                else:
                    print("❌ 文件大小变化过大")
                    status = "FAIL"
                    
                jpg_results.append({
                    'file': jpg_file,
                    'status': status,
                    'size_change_percent': size_change_percent
                })
                
            else:
                print(f"❌ 处理失败")
                jpg_results.append({
                    'file': jpg_file,
                    'status': 'ERROR',
                    'size_change_percent': None
                })
                
        except Exception as e:
            print(f"❌ 处理异常: {str(e)}")
            jpg_results.append({
                'file': jpg_file,
                'status': 'ERROR',
                'size_change_percent': None
            })
    
    # 测试PNG文件
    print("\n" + "=" * 60)
    print("测试PNG文件处理")
    print("=" * 60)
    
    png_results = []
    for png_file in png_files[:3]:  # 限制测试数量
        input_path = os.path.join(png_folder, png_file)
        output_path = os.path.join(output_folder, f"processed_{png_file}")
        
        print(f"\n测试PNG: {png_file}")
        print("=" * 50)
        
        try:
            # 获取原始信息
            with Image.open(input_path) as img:
                original_format = img.format
                original_mode = img.mode
                original_size = img.size
                original_file_size = os.path.getsize(input_path)
                has_transparency = img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                
            print(f"原始图像:")
            print(f"  格式: {original_format}")
            print(f"  模式: {original_mode}")
            print(f"  尺寸: {original_size}")
            print(f"  文件大小: {original_file_size:,} 字节")
            print(f"  透明度: {'是' if has_transparency else '否'}")
            
            # 处理图像
            success = sanitizer.clean_image(
                input_path=input_path,
                output_path=output_path,
                remove_metadata=True,
                advanced_cleaning=False
            )
            
            if success:
                # 获取处理后信息
                with Image.open(output_path) as img:
                    processed_format = img.format
                    processed_mode = img.mode
                    processed_size = img.size
                    processed_file_size = os.path.getsize(output_path)
                    processed_has_transparency = img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                    
                print(f"处理后图像:")
                print(f"  格式: {processed_format}")
                print(f"  模式: {processed_mode}")
                print(f"  尺寸: {processed_size}")
                print(f"  文件大小: {processed_file_size:,} 字节")
                print(f"  透明度: {'是' if processed_has_transparency else '否'}")
                
                # 计算变化
                size_change = processed_file_size - original_file_size
                size_change_percent = (size_change / original_file_size) * 100
                
                print(f"文件大小变化: {size_change:+,} 字节 ({size_change_percent:+.1f}%)")
                
                # 评估结果
                transparency_preserved = (has_transparency == processed_has_transparency)
                size_acceptable = abs(size_change_percent) <= 50  # PNG允许更大的变化
                
                if transparency_preserved and size_acceptable:
                    print("✅ PNG处理成功，透明度保持")
                    status = "PASS"
                elif not transparency_preserved:
                    print("❌ 透明度未正确保持")
                    status = "FAIL"
                else:
                    print("⚠️ 文件大小变化较大但可接受")
                    status = "WARN"
                    
                png_results.append({
                    'file': png_file,
                    'status': status,
                    'size_change_percent': size_change_percent,
                    'transparency_preserved': transparency_preserved
                })
                
            else:
                print(f"❌ 处理失败")
                png_results.append({
                    'file': png_file,
                    'status': 'ERROR',
                    'size_change_percent': None,
                    'transparency_preserved': False
                })
                
        except Exception as e:
            print(f"❌ 处理异常: {str(e)}")
            png_results.append({
                'file': png_file,
                'status': 'ERROR',
                'size_change_percent': None,
                'transparency_preserved': False
            })
    
    # 总结报告
    print("\n" + "=" * 60)
    print("综合测试报告")
    print("=" * 60)
    
    print("\nJPG测试结果:")
    jpg_pass = sum(1 for r in jpg_results if r['status'] == 'PASS')
    jpg_total = len(jpg_results)
    for result in jpg_results:
        status_icon = "✅" if result['status'] == 'PASS' else "❌"
        change = f"{result['size_change_percent']:+.1f}%" if result['size_change_percent'] is not None else "N/A"
        print(f"  {status_icon} {result['file']}: {result['status']} (大小变化: {change})")
    jpg_rate = jpg_pass/jpg_total*100 if jpg_total > 0 else 0
    print(f"JPG通过率: {jpg_pass}/{jpg_total} ({jpg_rate:.1f}%)")
    
    print("\nPNG测试结果:")
    png_pass = sum(1 for r in png_results if r['status'] in ['PASS', 'WARN'])
    png_total = len(png_results)
    if png_total > 0:
        for result in png_results:
            status_icon = "✅" if result['status'] in ['PASS', 'WARN'] else "❌"
            change = f"{result['size_change_percent']:+.1f}%" if result['size_change_percent'] is not None else "N/A"
            transparency = "保持" if result['transparency_preserved'] else "丢失"
            print(f"  {status_icon} {result['file']}: {result['status']} (大小变化: {change}, 透明度: {transparency})")
        print(f"PNG通过率: {png_pass}/{png_total} ({png_pass/png_total*100:.1f}%)")
    else:
        print("  没有找到PNG文件进行测试")
        print(f"PNG通过率: 0/0 (N/A)")
    
    print(f"\n处理后的图像保存在: {output_folder}")
    
    # 总体评估
    overall_pass = jpg_pass == jpg_total and png_pass == png_total
    if overall_pass:
        print("\n🎉 综合测试通过！JPG和PNG处理都正常工作。")
    else:
        print("\n⚠️ 部分测试未通过，需要进一步优化。")
    
    return overall_pass

if __name__ == "__main__":
    test_comprehensive()