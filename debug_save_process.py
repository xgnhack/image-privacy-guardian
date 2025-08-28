#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保存过程调试脚本
用于追踪ImageSanitizer的保存过程
"""

import os
from PIL import Image
from sanitizer_engine import ImageSanitizer

class DebugImageSanitizer(ImageSanitizer):
    """调试版本的ImageSanitizer"""
    
    def _save_cleaned_image(self, pil_image: Image.Image, output_path: str, target_format=None):
        """
        调试版本的保存方法
        """
        print(f"\n=== 保存过程调试 ===")
        print(f"输出路径: {output_path}")
        print(f"目标格式: {target_format}")
        print(f"图像模式: {pil_image.mode}")
        print(f"图像尺寸: {pil_image.size}")
        
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            # 检查目标格式或文件扩展名
            if target_format:
                ext = target_format.lower() if target_format.startswith('.') else '.' + target_format.lower()
                print(f"使用目标格式: '{ext}'")
            else:
                _, ext = os.path.splitext(output_path.lower())
                print(f"从文件路径推断格式: '{ext}'")
            
            if ext in ['.jpg', '.jpeg']:
                print(f"进入JPG保存分支")
                # JPEG不支持透明度，转换为RGB
                if pil_image.mode in ('RGBA', 'LA'):
                    print(f"图像包含透明度，转换为RGB")
                    # 创建白色背景
                    background = Image.new('RGB', pil_image.size, (255, 255, 255))
                    if pil_image.mode == 'RGBA':
                        background.paste(pil_image, mask=pil_image.split()[-1])
                    else:
                        background.paste(pil_image)
                    pil_image = background
                else:
                    print(f"图像模式为{pil_image.mode}，无需转换")
                
                print(f"保存为JPEG，质量=95")
                pil_image.save(output_path, 'JPEG', quality=95, optimize=True)
                print(f"JPG保存完成")
                
            elif ext == '.png':
                print(f"进入PNG保存分支")
                pil_image.save(output_path, 'PNG', optimize=True)
                
            elif ext in ['.bmp']:
                print(f"进入BMP保存分支")
                if pil_image.mode in ('RGBA', 'LA'):
                    pil_image = pil_image.convert('RGB')
                pil_image.save(output_path, 'BMP')
                
            elif ext in ['.tiff', '.tif']:
                print(f"进入TIFF保存分支")
                pil_image.save(output_path, 'TIFF')
                
            elif ext == '.webp':
                print(f"进入WebP保存分支")
                # WebP支持透明度和高质量压缩
                pil_image.save(output_path, 'WEBP', quality=95, method=6)
                
            else:
                print(f"进入默认PNG保存分支 (扩展名: '{ext}')")
                # 默认保存为PNG
                pil_image.save(output_path, 'PNG')
            
            print(f"保存完成，检查文件...")
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"文件大小: {file_size:,} 字节")
                
                # 检查文件头
                with open(output_path, 'rb') as f:
                    header = f.read(10)
                    print(f"文件头: {header.hex()}")
                    
                    if header[:2] == b'\xff\xd8':
                        print(f"✅ JPEG文件头正确")
                    elif header[:8] == b'\x89PNG\r\n\x1a\n':
                        print(f"❌ 这是PNG文件头！")
                    else:
                        print(f"⚠️  未知文件格式")
            else:
                print(f"❌ 文件保存失败")
                
        except Exception as e:
            print(f"❌ 保存过程出错: {str(e)}")
            raise Exception(f"保存图像失败: {str(e)}")

def debug_save_process():
    """调试保存过程"""
    # 测试文件路径
    test_jpg = r"d:\tmp\adobe\test\jpg\1-张艳华.jpg"
    output_jpg = r"d:\tmp\adobe\test\debug_save_process.jpg"
    
    print("保存过程调试测试")
    print("=" * 50)
    
    # 检查原始文件
    if not os.path.exists(test_jpg):
        print(f"测试文件不存在: {test_jpg}")
        return
    
    # 使用调试版sanitizer处理
    debug_sanitizer = DebugImageSanitizer()
    print(f"\n使用调试版ImageSanitizer处理...")
    success = debug_sanitizer.clean_image(test_jpg, output_jpg)
    
    print(f"\n处理结果: {'成功' if success else '失败'}")

if __name__ == "__main__":
    debug_save_process()