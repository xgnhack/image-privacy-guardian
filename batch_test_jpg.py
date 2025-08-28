#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量JPG测试脚本
测试多个JPG文件的处理效果
"""

import os
import glob
import shutil
from PIL import Image
from sanitizer_engine import ImageSanitizer

def batch_test_jpg():
    """批量测试JPG文件处理"""
    print("批量JPG处理测试")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = r"d:\tmp\adobe\test\batch_jpg_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # 查找JPG文件
    jpg_pattern = r"d:\tmp\adobe\test\jpg\*.jpg"
    jpg_files = glob.glob(jpg_pattern)
    
    if not jpg_files:
        print(f"❌ 未找到JPG文件: {jpg_pattern}")
        return
    
    print(f"找到 {len(jpg_files)} 个JPG文件")
    
    sanitizer = ImageSanitizer()
    results = []
    
    for i, jpg_file in enumerate(jpg_files[:3], 1):  # 只测试前3个文件
        print(f"\n测试 {i}/3: {os.path.basename(jpg_file)}")
        print("-" * 40)
        
        # 复制到测试目录并重命名
        test_input = os.path.join(test_dir, f"input_{i}.jpg")
        test_output = os.path.join(test_dir, f"output_{i}.jpg")
        
        try:
            shutil.copy2(jpg_file, test_input)
            
            # 获取原始信息
            original_size = os.path.getsize(test_input)
            with Image.open(test_input) as img:
                original_format = img.format
                original_mode = img.mode
                original_dimensions = img.size
            
            print(f"原始: {original_format} {original_mode} {original_dimensions} {original_size:,}字节")
            
            # 处理图像
            success = sanitizer.clean_image(test_input, test_output)
            
            if success and os.path.exists(test_output):
                # 获取处理后信息
                processed_size = os.path.getsize(test_output)
                with open(test_output, 'rb') as f:
                    header = f.read(4).hex()
                
                with Image.open(test_output) as img:
                    processed_format = img.format
                    processed_mode = img.mode
                    processed_dimensions = img.size
                
                print(f"处理后: {processed_format} {processed_mode} {processed_dimensions} {processed_size:,}字节")
                
                # 验证结果
                format_ok = processed_format == 'JPEG'
                header_ok = header.startswith('ffd8')
                size_ok = processed_dimensions == original_dimensions
                mode_ok = processed_mode == original_mode
                
                size_change_percent = ((processed_size - original_size) / original_size) * 100
                
                result = {
                    'file': os.path.basename(jpg_file),
                    'format_ok': format_ok,
                    'header_ok': header_ok,
                    'size_ok': size_ok,
                    'mode_ok': mode_ok,
                    'size_change': size_change_percent,
                    'success': format_ok and header_ok and size_ok and mode_ok
                }
                
                results.append(result)
                
                status = "✅" if result['success'] else "❌"
                print(f"{status} 格式:{format_ok} 文件头:{header_ok} 尺寸:{size_ok} 模式:{mode_ok} 大小变化:{size_change_percent:+.1f}%")
                
            else:
                print(f"❌ 处理失败")
                results.append({
                    'file': os.path.basename(jpg_file),
                    'success': False,
                    'error': '处理失败'
                })
                
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            results.append({
                'file': os.path.basename(jpg_file),
                'success': False,
                'error': str(e)
            })
    
    # 总结报告
    print(f"\n" + "=" * 60)
    print(f"批量测试总结")
    print(f"=" * 60)
    
    success_count = sum(1 for r in results if r.get('success', False))
    total_count = len(results)
    
    print(f"总测试数: {total_count}")
    print(f"成功数: {success_count}")
    print(f"成功率: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print(f"\n🎉 所有JPG文件处理成功！")
        print(f"✅ JPG格式修复验证通过")
    else:
        print(f"\n⚠️  部分文件处理失败，需要进一步检查")
    
    print(f"\n测试文件保存在: {test_dir}")

if __name__ == "__main__":
    batch_test_jpg()