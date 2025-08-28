#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JPG质量测试脚本
用于测试JPG图片处理前后的质量对比，分析失真原因
"""

import os
import sys
import numpy as np
from PIL import Image, ExifTags
import cv2
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
import matplotlib.pyplot as plt
from sanitizer_engine import ImageSanitizer

class JPGQualityTester:
    def __init__(self, test_dir="d:\\tmp\\adobe\\test"):
        self.test_dir = test_dir
        self.jpg_dir = os.path.join(test_dir, "jpg")
        self.output_dir = os.path.join(test_dir, "output_jpg_test")
        self.sanitizer = ImageSanitizer()
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_image_info(self, image_path):
        """获取图像详细信息"""
        try:
            with Image.open(image_path) as img:
                # 获取基本信息
                info = {
                    'path': image_path,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'file_size': os.path.getsize(image_path),
                }
                
                # 获取DPI信息
                dpi = img.info.get('dpi', (72, 72))
                info['dpi'] = dpi
                
                # 获取EXIF信息
                exif_data = img.getexif()
                info['has_exif'] = bool(exif_data)
                info['exif_count'] = len(exif_data) if exif_data else 0
                
                # 获取质量信息（如果可用）
                if hasattr(img, 'quantization'):
                    info['quantization_tables'] = len(img.quantization)
                
                return info
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_image_metrics(self, original_path, processed_path):
        """计算图像质量指标"""
        try:
            # 加载图像
            original = cv2.imread(original_path)
            processed = cv2.imread(processed_path)
            
            if original is None or processed is None:
                return {'error': '无法加载图像'}
            
            # 确保图像尺寸一致
            if original.shape != processed.shape:
                processed = cv2.resize(processed, (original.shape[1], original.shape[0]))
            
            # 转换为灰度图计算SSIM
            original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            processed_gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            
            # 计算SSIM
            ssim_value = ssim(original_gray, processed_gray)
            
            # 计算PSNR
            psnr_value = psnr(original, processed)
            
            # 计算MSE
            mse = np.mean((original.astype(float) - processed.astype(float)) ** 2)
            
            # 计算像素差异统计
            diff = np.abs(original.astype(float) - processed.astype(float))
            max_diff = np.max(diff)
            mean_diff = np.mean(diff)
            std_diff = np.std(diff)
            
            return {
                'ssim': ssim_value,
                'psnr': psnr_value,
                'mse': mse,
                'max_pixel_diff': max_diff,
                'mean_pixel_diff': mean_diff,
                'std_pixel_diff': std_diff
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def test_single_image(self, image_path):
        """测试单个图像"""
        print(f"\n测试图像: {os.path.basename(image_path)}")
        print("=" * 50)
        
        # 获取原始图像信息
        original_info = self.get_image_info(image_path)
        print(f"原始图像信息:")
        print(f"  格式: {original_info.get('format')}")
        print(f"  模式: {original_info.get('mode')}")
        print(f"  尺寸: {original_info.get('size')}")
        print(f"  文件大小: {original_info.get('file_size'):,} 字节")
        print(f"  DPI: {original_info.get('dpi')}")
        print(f"  EXIF数据: {original_info.get('exif_count', 0)} 个标签")
        
        # 处理图像
        output_path = os.path.join(self.output_dir, f"processed_{os.path.basename(image_path)}")
        
        try:
            # 使用sanitizer处理图像
            self.sanitizer.clean_image(
                input_path=image_path,
                output_path=output_path,
                advanced_config={'enabled': False}
            )
            
            # 获取处理后图像信息
            processed_info = self.get_image_info(output_path)
            print(f"\n处理后图像信息:")
            print(f"  格式: {processed_info.get('format')}")
            print(f"  模式: {processed_info.get('mode')}")
            print(f"  尺寸: {processed_info.get('size')}")
            print(f"  文件大小: {processed_info.get('file_size'):,} 字节")
            print(f"  DPI: {processed_info.get('dpi')}")
            print(f"  EXIF数据: {processed_info.get('exif_count', 0)} 个标签")
            
            # 计算质量指标
            metrics = self.calculate_image_metrics(image_path, output_path)
            print(f"\n质量指标:")
            if 'error' not in metrics:
                print(f"  SSIM (结构相似性): {metrics['ssim']:.4f}")
                print(f"  PSNR (峰值信噪比): {metrics['psnr']:.2f} dB")
                print(f"  MSE (均方误差): {metrics['mse']:.2f}")
                print(f"  最大像素差异: {metrics['max_pixel_diff']:.2f}")
                print(f"  平均像素差异: {metrics['mean_pixel_diff']:.2f}")
                print(f"  像素差异标准差: {metrics['std_pixel_diff']:.2f}")
            else:
                print(f"  计算失败: {metrics['error']}")
            
            # 文件大小变化
            size_change = processed_info.get('file_size', 0) - original_info.get('file_size', 0)
            size_change_percent = (size_change / original_info.get('file_size', 1)) * 100
            print(f"\n文件大小变化: {size_change:+,} 字节 ({size_change_percent:+.1f}%)")
            
            # 分析潜在问题
            self.analyze_potential_issues(original_info, processed_info, metrics)
            
            return {
                'original_info': original_info,
                'processed_info': processed_info,
                'metrics': metrics,
                'output_path': output_path
            }
            
        except Exception as e:
            print(f"处理失败: {str(e)}")
            return {'error': str(e)}
    
    def analyze_potential_issues(self, original_info, processed_info, metrics):
        """分析潜在的质量问题"""
        print(f"\n潜在问题分析:")
        issues = []
        
        # 检查SSIM
        if 'ssim' in metrics and metrics['ssim'] < 0.95:
            issues.append(f"SSIM较低 ({metrics['ssim']:.4f})，可能存在结构失真")
        
        # 检查PSNR
        if 'psnr' in metrics and metrics['psnr'] < 30:
            issues.append(f"PSNR较低 ({metrics['psnr']:.2f} dB)，图像质量下降明显")
        
        # 检查像素差异
        if 'max_pixel_diff' in metrics and metrics['max_pixel_diff'] > 50:
            issues.append(f"最大像素差异过大 ({metrics['max_pixel_diff']:.2f})")
        
        # 检查DPI变化
        orig_dpi = original_info.get('dpi', (72, 72))
        proc_dpi = processed_info.get('dpi', (72, 72))
        if orig_dpi != proc_dpi:
            issues.append(f"DPI发生变化: {orig_dpi} -> {proc_dpi}")
        
        # 检查文件大小变化
        orig_size = original_info.get('file_size', 0)
        proc_size = processed_info.get('file_size', 0)
        size_change_percent = ((proc_size - orig_size) / orig_size) * 100 if orig_size > 0 else 0
        if abs(size_change_percent) > 20:
            issues.append(f"文件大小变化过大 ({size_change_percent:+.1f}%)")
        
        if issues:
            for issue in issues:
                print(f"  ⚠️  {issue}")
        else:
            print(f"  ✅ 未发现明显质量问题")
    
    def run_batch_test(self, max_files=5):
        """批量测试JPG文件"""
        print("JPG质量测试开始")
        print("=" * 60)
        
        # 获取JPG文件列表
        jpg_files = []
        if os.path.exists(self.jpg_dir):
            for file in os.listdir(self.jpg_dir):
                if file.lower().endswith(('.jpg', '.jpeg')):
                    jpg_files.append(os.path.join(self.jpg_dir, file))
        
        if not jpg_files:
            print(f"在 {self.jpg_dir} 中未找到JPG文件")
            return
        
        # 限制测试文件数量
        jpg_files = jpg_files[:max_files]
        print(f"找到 {len(jpg_files)} 个JPG文件进行测试")
        
        results = []
        for jpg_file in jpg_files:
            result = self.test_single_image(jpg_file)
            results.append(result)
        
        # 生成总结报告
        self.generate_summary_report(results)
        
        return results
    
    def generate_summary_report(self, results):
        """生成总结报告"""
        print("\n" + "=" * 60)
        print("测试总结报告")
        print("=" * 60)
        
        valid_results = [r for r in results if 'error' not in r and 'metrics' in r and 'error' not in r['metrics']]
        
        if not valid_results:
            print("没有有效的测试结果")
            return
        
        # 计算平均指标
        avg_ssim = np.mean([r['metrics']['ssim'] for r in valid_results])
        avg_psnr = np.mean([r['metrics']['psnr'] for r in valid_results])
        avg_mse = np.mean([r['metrics']['mse'] for r in valid_results])
        avg_max_diff = np.mean([r['metrics']['max_pixel_diff'] for r in valid_results])
        avg_mean_diff = np.mean([r['metrics']['mean_pixel_diff'] for r in valid_results])
        
        print(f"平均质量指标 (基于 {len(valid_results)} 个有效样本):")
        print(f"  平均SSIM: {avg_ssim:.4f}")
        print(f"  平均PSNR: {avg_psnr:.2f} dB")
        print(f"  平均MSE: {avg_mse:.2f}")
        print(f"  平均最大像素差异: {avg_max_diff:.2f}")
        print(f"  平均像素差异: {avg_mean_diff:.2f}")
        
        # 质量评估
        print(f"\n质量评估:")
        if avg_ssim >= 0.98:
            print(f"  ✅ SSIM优秀 ({avg_ssim:.4f})")
        elif avg_ssim >= 0.95:
            print(f"  ⚠️  SSIM良好 ({avg_ssim:.4f})")
        else:
            print(f"  ❌ SSIM较差 ({avg_ssim:.4f})，存在明显失真")
        
        if avg_psnr >= 35:
            print(f"  ✅ PSNR优秀 ({avg_psnr:.2f} dB)")
        elif avg_psnr >= 30:
            print(f"  ⚠️  PSNR良好 ({avg_psnr:.2f} dB)")
        else:
            print(f"  ❌ PSNR较差 ({avg_psnr:.2f} dB)，质量下降明显")
        
        # 建议
        print(f"\n改进建议:")
        if avg_ssim < 0.95 or avg_psnr < 30:
            print(f"  1. 考虑提高JPEG保存质量（当前95）")
            print(f"  2. 优化OpenCV处理算法参数")
            print(f"  3. 保持原始DPI信息")
            print(f"  4. 考虑对JPG使用更温和的处理策略")
        else:
            print(f"  当前处理质量良好，无需特别调整")

def main():
    """主函数"""
    tester = JPGQualityTester()
    
    print("开始JPG质量测试...")
    results = tester.run_batch_test(max_files=5)
    
    print(f"\n测试完成！处理后的图像保存在: {tester.output_dir}")
    print("请检查输出图像的视觉质量")

if __name__ == "__main__":
    main()