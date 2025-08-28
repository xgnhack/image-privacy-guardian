#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析JPG图像的质量参数
"""

import os
from PIL import Image
from PIL.ExifTags import TAGS
import piexif

def analyze_jpg_quality(image_path):
    """
    分析JPG图像的质量参数
    """
    try:
        with Image.open(image_path) as img:
            print(f"分析图像: {os.path.basename(image_path)}")
            print(f"格式: {img.format}")
            print(f"模式: {img.mode}")
            print(f"尺寸: {img.size}")
            print(f"文件大小: {os.path.getsize(image_path):,} 字节")
            
            # 尝试获取JPEG质量信息
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    print(f"EXIF {tag}: {value}")
            
            # 尝试使用piexif获取更多信息
            try:
                exif_dict = piexif.load(image_path)
                if '0th' in exif_dict:
                    for key, value in exif_dict['0th'].items():
                        tag_name = piexif.TAGS['0th'].get(key, key)
                        print(f"EXIF 0th {tag_name}: {value}")
                        
                if 'Exif' in exif_dict:
                    for key, value in exif_dict['Exif'].items():
                        tag_name = piexif.TAGS['Exif'].get(key, key)
                        print(f"EXIF Exif {tag_name}: {value}")
            except Exception as e:
                print(f"无法读取EXIF: {e}")
                
            # 检查图像的量化表（质量指标）
            if hasattr(img, 'quantization'):
                print(f"量化表: {img.quantization}")
                
            print("-" * 50)
            
    except Exception as e:
        print(f"分析失败: {e}")

def main():
    jpg_dir = "jpg"
    
    if not os.path.exists(jpg_dir):
        print(f"目录不存在: {jpg_dir}")
        return
        
    jpg_files = [f for f in os.listdir(jpg_dir) if f.lower().endswith(('.jpg', '.jpeg'))]
    
    for jpg_file in jpg_files[:2]:  # 只分析前两个文件
        jpg_path = os.path.join(jpg_dir, jpg_file)
        analyze_jpg_quality(jpg_path)

if __name__ == "__main__":
    main()