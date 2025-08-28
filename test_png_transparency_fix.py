#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG透明图像处理测试脚本
测试新的PNG透明度保护处理方案
"""

import os
import numpy as np
from PIL import Image, ImageDraw
from sanitizer_engine import ImageSanitizer
from png_transparency_processor import PNGTransparencyProcessor
import shutil

def create_test_images():
    """创建各种类型的PNG测试图像"""
    test_dir = "test_transparency_images"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    test_images = []
    
    # 1. RGBA模式 - 渐变透明度
    print("创建RGBA渐变透明度图像...")
    rgba_img = Image.new('RGBA', (200, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(rgba_img)
    
    # 创建渐变透明效果
    for y in range(200):
        alpha = int(255 * (y / 200))
        for x in range(200):
            color = (255 - x, x, 128, alpha)
            draw.point((x, y), color)
    
    rgba_path = os.path.join(test_dir, "rgba_gradient.png")
    rgba_img.save(rgba_path, 'PNG')
    test_images.append((rgba_path, 'RGBA渐变透明度'))
    
    # 2. RGBA模式 - 部分透明图形
    print("创建RGBA部分透明图像...")
    rgba_shapes = Image.new('RGBA', (200, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(rgba_shapes)
    
    # 半透明圆形
    draw.ellipse([50, 50, 150, 150], fill=(255, 0, 0, 128))
    # 不透明矩形
    draw.rectangle([25, 25, 75, 75], fill=(0, 255, 0, 255))
    # 高透明三角形
    draw.polygon([(100, 25), (175, 175), (25, 175)], fill=(0, 0, 255, 64))
    
    rgba_shapes_path = os.path.join(test_dir, "rgba_shapes.png")
    rgba_shapes.save(rgba_shapes_path, 'PNG')
    test_images.append((rgba_shapes_path, 'RGBA部分透明图形'))
    
    # 3. LA模式 - 灰度透明
    print("创建LA灰度透明图像...")
    la_img = Image.new('LA', (200, 200), (128, 0))
    draw = ImageDraw.Draw(la_img)
    
    # 创建灰度渐变和透明度渐变
    for i in range(5):
        gray_value = 50 + i * 40
        alpha_value = 50 + i * 40
        draw.rectangle([i*40, i*40, (i+1)*40, (i+1)*40], fill=(gray_value, alpha_value))
    
    la_path = os.path.join(test_dir, "la_gradient.png")
    la_img.save(la_path, 'PNG')
    test_images.append((la_path, 'LA灰度透明度'))
    
    # 4. P模式 - 调色板透明
    print("创建P模式调色板透明图像...")
    # 创建RGB图像
    rgb_img = Image.new('RGB', (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(rgb_img)
    
    # 创建彩色图案
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    for i, color in enumerate(colors):
        draw.rectangle([i*40, 20, (i+1)*40, 180], fill=color)
    
    # 添加特定颜色作为透明色
    transparent_color = (128, 128, 128)
    draw.ellipse([50, 50, 150, 150], fill=transparent_color)  # 将被设为透明的区域
    
    # 转换为调色板模式
    p_img = rgb_img.convert('P', palette=Image.ADAPTIVE)
    
    # 找到透明色在调色板中的索引
    palette = p_img.getpalette()
    transparent_index = None
    if palette:
        for i in range(0, len(palette), 3):
            r, g, b = palette[i:i+3]
            if (r, g, b) == transparent_color:
                transparent_index = i // 3
                break
    
    if transparent_index is not None:
        p_img.info['transparency'] = transparent_index
    
    p_path = os.path.join(test_dir, "palette_transparent.png")
    p_img.save(p_path, 'PNG')
    test_images.append((p_path, 'P模式调色板透明'))
    
    # 5. 复杂透明图像 - 模拟真实场景
    print("创建复杂透明图像...")
    complex_img = Image.new('RGBA', (300, 300), (255, 255, 255, 0))
    draw = ImageDraw.Draw(complex_img)
    
    # 背景渐变
    for y in range(300):
        alpha = int(100 + 155 * (y / 300))
        draw.line([(0, y), (300, y)], fill=(100, 150, 200, alpha))
    
    # 添加各种透明度的图形
    draw.ellipse([50, 50, 150, 150], fill=(255, 100, 100, 180))
    draw.ellipse([100, 100, 200, 200], fill=(100, 255, 100, 120))
    draw.ellipse([150, 150, 250, 250], fill=(100, 100, 255, 200))
    
    # 添加文字（如果可能的话）
    try:
        draw.text((10, 10), "透明测试", fill=(0, 0, 0, 255))
    except:
        pass
    
    complex_path = os.path.join(test_dir, "complex_transparency.png")
    complex_img.save(complex_path, 'PNG')
    test_images.append((complex_path, '复杂透明场景'))
    
    return test_images

def analyze_transparency(image_path, description):
    """分析图像的透明度信息"""
    try:
        with Image.open(image_path) as img:
            print(f"\n📊 {description} 分析:")
            print(f"   模式: {img.mode}")
            print(f"   尺寸: {img.size}")
            
            if img.mode == 'RGBA':
                alpha_channel = np.array(img)[:, :, 3]
                print(f"   透明度范围: {alpha_channel.min()} - {alpha_channel.max()}")
                print(f"   透明度均值: {alpha_channel.mean():.2f}")
                print(f"   唯一透明度值: {len(np.unique(alpha_channel))}")
                
                # 统计透明度分布
                fully_transparent = np.sum(alpha_channel == 0)
                fully_opaque = np.sum(alpha_channel == 255)
                semi_transparent = alpha_channel.size - fully_transparent - fully_opaque
                
                print(f"   完全透明像素: {fully_transparent}")
                print(f"   完全不透明像素: {fully_opaque}")
                print(f"   半透明像素: {semi_transparent}")
                
            elif img.mode == 'LA':
                alpha_channel = np.array(img)[:, :, 1]
                print(f"   透明度范围: {alpha_channel.min()} - {alpha_channel.max()}")
                print(f"   透明度均值: {alpha_channel.mean():.2f}")
                
            elif img.mode == 'P' and 'transparency' in img.info:
                print(f"   透明色索引: {img.info['transparency']}")
                print(f"   调色板大小: {len(img.getpalette()) // 3}")
                
            return True
            
    except Exception as e:
        print(f"   ❌ 分析失败: {str(e)}")
        return False

def compare_images(original_path, processed_path, description):
    """比较原始图像和处理后图像"""
    print(f"\n🔍 {description} 对比分析:")
    
    try:
        with Image.open(original_path) as orig, Image.open(processed_path) as proc:
            # 基本信息对比
            print(f"   原始: {orig.mode} {orig.size}")
            print(f"   处理: {proc.mode} {proc.size}")
            
            if orig.size != proc.size:
                print("   ⚠️ 尺寸发生变化!")
                return False
                
            if orig.mode != proc.mode:
                print("   ⚠️ 颜色模式发生变化!")
                return False
            
            # 透明度对比
            if orig.mode == 'RGBA':
                orig_alpha = np.array(orig)[:, :, 3]
                proc_alpha = np.array(proc)[:, :, 3]
                
                alpha_diff = np.abs(orig_alpha.astype(int) - proc_alpha.astype(int))
                max_diff = alpha_diff.max()
                mean_diff = alpha_diff.mean()
                
                print(f"   透明度最大差异: {max_diff}")
                print(f"   透明度平均差异: {mean_diff:.2f}")
                
                if max_diff > 10:  # 允许小幅差异
                    print("   ⚠️ 透明度差异较大!")
                    return False
                    
            # 内容对比
            orig_rgb = np.array(orig.convert('RGB'))
            proc_rgb = np.array(proc.convert('RGB'))
            
            rgb_diff = np.abs(orig_rgb.astype(int) - proc_rgb.astype(int))
            max_rgb_diff = rgb_diff.max()
            mean_rgb_diff = rgb_diff.mean()
            
            print(f"   RGB最大差异: {max_rgb_diff}")
            print(f"   RGB平均差异: {mean_rgb_diff:.2f}")
            
            if max_rgb_diff > 20:  # 允许适度的处理差异
                print("   ⚠️ 图像内容差异较大!")
                return False
                
            print("   ✅ 透明度和内容保持良好")
            return True
            
    except Exception as e:
        print(f"   ❌ 对比失败: {str(e)}")
        return False

def test_png_transparency_processing():
    """测试PNG透明图像处理"""
    print("🚀 开始PNG透明图像处理测试\n")
    
    # 创建测试图像
    test_images = create_test_images()
    
    # 创建输出目录
    output_dir = "test_transparency_output"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # 初始化处理器
    sanitizer = ImageSanitizer()
    png_processor = PNGTransparencyProcessor()
    
    results = []
    
    for image_path, description in test_images:
        print(f"\n{'='*60}")
        print(f"🧪 测试: {description}")
        print(f"文件: {os.path.basename(image_path)}")
        
        # 分析原始图像
        analyze_transparency(image_path, "原始图像")
        
        # 使用新的透明度保护处理
        output_path = os.path.join(output_dir, f"processed_{os.path.basename(image_path)}")
        
        print(f"\n🔧 使用透明度保护处理器...")
        success = png_processor.process_png_with_transparency(
            image_path, 
            output_path, 
            preserve_quality=True
        )
        
        if success and os.path.exists(output_path):
            # 分析处理后图像
            analyze_transparency(output_path, "处理后图像")
            
            # 对比分析
            comparison_result = compare_images(image_path, output_path, description)
            results.append((description, True, comparison_result))
            
            # 获取透明度信息
            transparency_info = png_processor.get_transparency_info(output_path)
            print(f"\n📋 透明度信息: {transparency_info}")
            
        else:
            print(f"   ❌ 处理失败")
            results.append((description, False, False))
            
        # 测试标准处理器作为对比
        print(f"\n🔧 使用标准处理器对比...")
        standard_output = os.path.join(output_dir, f"standard_{os.path.basename(image_path)}")
        standard_success = sanitizer.clean_image(image_path, standard_output)
        
        if standard_success:
            print(f"   标准处理器: 成功")
            analyze_transparency(standard_output, "标准处理结果")
        else:
            print(f"   标准处理器: 失败")
    
    # 输出测试总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    
    total_tests = len(results)
    successful_processing = sum(1 for _, success, _ in results if success)
    successful_comparison = sum(1 for _, _, comparison in results if comparison)
    
    print(f"总测试数: {total_tests}")
    print(f"处理成功: {successful_processing}/{total_tests}")
    print(f"质量保持: {successful_comparison}/{total_tests}")
    
    for description, processing_success, comparison_success in results:
        status_processing = "✅" if processing_success else "❌"
        status_comparison = "✅" if comparison_success else "❌"
        print(f"  {status_processing} {status_comparison} {description}")
    
    if successful_processing == total_tests and successful_comparison == total_tests:
        print("\n🎉 所有测试通过！PNG透明度处理方案工作正常。")
    elif successful_processing == total_tests:
        print("\n⚠️ 处理成功但质量有损失，需要进一步优化。")
    else:
        print("\n❌ 部分测试失败，需要检查处理逻辑。")
    
    return successful_processing == total_tests and successful_comparison == total_tests

if __name__ == "__main__":
    test_png_transparency_processing()