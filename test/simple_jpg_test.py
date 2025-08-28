#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的JPG质量对比测试
"""

import os
import sys
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sanitizer_engine import ImageSanitizer

def compare_images(original_path, processed_path):
    """对比两张图像的质量"""
    try:
        # 打开图像
        with Image.open(original_path) as orig:
            with Image.open(processed_path) as proc:
                # 转换为numpy数组
                orig_array = np.array(orig)
                proc_array = np.array(proc)
                
                # 计算SSIM
                if len(orig_array.shape) == 3:  # 彩色图像
                    ssim_score = ssim(orig_array, proc_array, multichannel=True, channel_axis=2)
                else:  # 灰度图像
                    ssim_score = ssim(orig_array, proc_array)
                
                # 计算MSE
                mse = np.mean((orig_array - proc_array) ** 2)
                
                # 计算PSNR
                if mse == 0:
                    psnr = float('inf')
                else:
                    psnr = 20 * np.log10(255.0 / np.sqrt(mse))
                
                return {
                    'ssim': ssim_score,
                    'mse': mse,
                    'psnr': psnr,
                    'original_size': os.path.getsize(original_path),
                    'processed_size': os.path.getsize(processed_path)
                }
    except Exception as e:
        print(f"对比失败: {e}")
        return None

def main():
    """主测试函数"""
    # 测试目录
    test_dir = "d:\\tmp\\adobe\\test"
    jpg_dir = os.path.join(test_dir, "jpg")
    output_dir = os.path.join(test_dir, "simple_test_output")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化清理器
    sanitizer = ImageSanitizer()
    
    # 获取JPG文件列表
    jpg_files = [f for f in os.listdir(jpg_dir) if f.lower().endswith('.jpg')]
    
    print("=" * 60)
    print("JPG质量保护测试")
    print("=" * 60)
    
    results = []
    
    for jpg_file in jpg_files[:3]:  # 只测试前3个文件
        original_path = os.path.join(jpg_dir, jpg_file)
        output_path = os.path.join(output_dir, f"processed_{jpg_file}")
        
        print(f"\n测试文件: {jpg_file}")
        print("-" * 40)
        
        # 获取原始文件信息
        original_size = os.path.getsize(original_path)
        print(f"原始文件大小: {original_size:,} 字节")
        
        # 处理图像
        success = sanitizer.clean_image(
            input_path=original_path,
            output_path=output_path,
            remove_metadata=True,
            advanced_cleaning=False
        )
        
        if success and os.path.exists(output_path):
            # 获取处理后文件信息
            processed_size = os.path.getsize(output_path)
            size_change = processed_size - original_size
            size_change_percent = (size_change / original_size) * 100
            
            print(f"处理后文件大小: {processed_size:,} 字节")
            print(f"大小变化: {size_change:+,} 字节 ({size_change_percent:+.1f}%)")
            
            # 对比图像质量
            comparison = compare_images(original_path, output_path)
            if comparison:
                print(f"SSIM相似度: {comparison['ssim']:.4f} (1.0为完全相同)")
                print(f"PSNR: {comparison['psnr']:.2f} dB (>30为高质量)")
                print(f"MSE: {comparison['mse']:.2f}")
                
                # 质量评估
                if comparison['ssim'] > 0.95:
                    quality_status = "✅ 优秀"
                elif comparison['ssim'] > 0.90:
                    quality_status = "✅ 良好"
                elif comparison['ssim'] > 0.85:
                    quality_status = "⚠️ 一般"
                else:
                    quality_status = "❌ 较差"
                
                print(f"质量评估: {quality_status}")
                
                results.append({
                    'file': jpg_file,
                    'ssim': comparison['ssim'],
                    'psnr': comparison['psnr'],
                    'size_change_percent': size_change_percent,
                    'quality_status': quality_status
                })
            else:
                print("❌ 质量对比失败")
        else:
            print("❌ 处理失败")
    
    # 总结报告
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if results:
        avg_ssim = sum(r['ssim'] for r in results) / len(results)
        avg_psnr = sum(r['psnr'] for r in results) / len(results)
        avg_size_change = sum(r['size_change_percent'] for r in results) / len(results)
        
        print(f"平均SSIM: {avg_ssim:.4f}")
        print(f"平均PSNR: {avg_psnr:.2f} dB")
        print(f"平均文件大小变化: {avg_size_change:+.1f}%")
        
        excellent_count = sum(1 for r in results if '优秀' in r['quality_status'])
        good_count = sum(1 for r in results if '良好' in r['quality_status'])
        
        print(f"\n质量分布:")
        print(f"  优秀: {excellent_count}/{len(results)}")
        print(f"  良好: {good_count}/{len(results)}")
        
        if avg_ssim > 0.95 and abs(avg_size_change) < 10:
            print("\n🎉 JPG质量保护策略工作良好！")
        elif avg_ssim > 0.90:
            print("\n✅ JPG质量保护基本有效")
        else:
            print("\n⚠️ JPG质量保护需要进一步优化")
    else:
        print("❌ 没有有效的测试结果")
    
    print(f"\n处理后的图像保存在: {output_dir}")

if __name__ == "__main__":
    main()