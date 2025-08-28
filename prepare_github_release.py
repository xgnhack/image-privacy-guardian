#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 发布准备脚本
自动整理和打包项目文件，准备发布到 GitHub
"""

import os
import shutil
import json
from pathlib import Path

def prepare_github_release():
    """准备 GitHub 发布包"""
    
    print("🚀 准备 GitHub 发布包...")
    
    # 当前目录
    current_dir = Path(__file__).parent
    
    # 创建发布目录
    release_dir = current_dir / "github_release"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    print(f"📁 创建发布目录: {release_dir}")
    
    # 需要包含的文件和目录
    include_files = [
        "main.py",
        "monitoring_manager.py", 
        "sanitizer_engine.py",
        "advanced_settings_ui.py",
        "requirements.txt",
        "README.md",
        "RELEASE.md",
        "LICENSE",
        ".gitignore",
        "GITHUB_RELEASE_GUIDE.md"
    ]
    
    include_dirs = [
        "aegis_config",
        "windows"
    ]
    
    # 复制文件
    print("\n📋 复制项目文件...")
    for file_name in include_files:
        src_file = current_dir / file_name
        if src_file.exists():
            dst_file = release_dir / file_name
            shutil.copy2(src_file, dst_file)
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} (文件不存在)")
    
    # 复制目录
    print("\n📁 复制项目目录...")
    for dir_name in include_dirs:
        src_dir = current_dir / dir_name
        if src_dir.exists():
            dst_dir = release_dir / dir_name
            shutil.copytree(src_dir, dst_dir)
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (目录不存在)")
    
    # 创建发布信息文件
    release_info = {
        "project_name": "Image Privacy Guardian",
        "version": "1.0.0",
        "release_date": "2024-12-19",
        "description": "专业的图像隐私保护工具",
        "author": "Your Name",
        "license": "MIT",
        "repository": "https://github.com/YOUR_USERNAME/image-privacy-guardian",
        "files_included": include_files + [f"{d}/" for d in include_dirs],
        "executable_size": "99.6 MB",
        "supported_formats": ["JPEG", "PNG", "BMP", "TIFF", "WebP", "HEIF/HEIC"]
    }
    
    with open(release_dir / "release_info.json", "w", encoding="utf-8") as f:
        json.dump(release_info, f, indent=2, ensure_ascii=False)
    
    # 统计文件信息
    total_files = 0
    total_size = 0
    
    for root, dirs, files in os.walk(release_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.exists():
                total_files += 1
                total_size += file_path.stat().st_size
    
    print(f"\n📊 发布包统计:")
    print(f"  📄 文件数量: {total_files}")
    print(f"  💾 总大小: {total_size / 1024 / 1024:.1f} MB")
    
    # 生成发布说明
    release_notes = f"""
🎉 GitHub 发布包已准备完成！

📁 发布目录: {release_dir}
📄 文件数量: {total_files}
💾 总大小: {total_size / 1024 / 1024:.1f} MB

📋 下一步操作:
1. 在 GitHub 创建新仓库 'image-privacy-guardian'
2. 将 {release_dir} 目录中的所有文件上传到仓库
3. 创建 v1.0.0 Release 并上传 windows/v1.0.0/ImagePrivacyGuardian.exe
4. 参考 GITHUB_RELEASE_GUIDE.md 完成发布

🔗 详细指南: GITHUB_RELEASE_GUIDE.md
"""
    
    print(release_notes)
    
    # 保存发布说明
    with open(release_dir / "RELEASE_NOTES.txt", "w", encoding="utf-8") as f:
        f.write(release_notes)
    
    print("✅ GitHub 发布包准备完成！")
    return release_dir

if __name__ == "__main__":
    try:
        release_dir = prepare_github_release()
        print(f"\n🎯 发布包位置: {release_dir}")
        print("📖 请查看 GITHUB_RELEASE_GUIDE.md 了解详细发布步骤")
    except Exception as e:
        print(f"❌ 错误: {e}")
        input("按回车键退出...")