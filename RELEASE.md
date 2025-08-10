# 🛡️ Image Privacy Guardian v1.0.0 发布说明

## 📦 发布包内容

### 🖥️ Windows 绿色版 (推荐)
- **文件**: `windows/v1.0.0/ImagePrivacyGuardian.exe`
- **大小**: 99.6 MB
- **特性**: 免安装、离线运行、便携式
- **系统要求**: Windows 7/8/10/11 (64位)

### 🐍 Python 源码版
- **适用于**: 开发者、Linux/macOS用户
- **要求**: Python 3.7+ 和依赖包
- **安装**: `pip install -r requirements.txt`

## ✨ 主要功能

### 🎯 智能监控
- 实时文件夹监控，自动检测图像文件变化
- 支持多文件夹同时监控
- 定时自动扫描功能
- 一键手动扫描

### 🔬 高级清理
- **两阶段清理**：元数据清理 + 高级图像清理
- **支持格式**：JPEG、PNG、BMP、TIFF、WebP、HEIF/HEIC
- **智能检测**：HSV颜色空间精确检测跟踪点
- **可视化配置**：实时预览清理效果

### 🛡️ 安全保障
- 自动备份原文件
- 失败文件错误日志
- 文件完整性检查
- 安全的原地替换

## 🚀 快速开始

### Windows 用户 (推荐)
1. 下载 `windows/v1.0.0/ImagePrivacyGuardian.exe`
2. 双击运行，无需安装
3. 添加要监控的文件夹
4. 点击"开始监控"

### 开发者/源码用户
```bash
git clone https://github.com/YOUR_USERNAME/image-privacy-guardian.git
cd image-privacy-guardian
pip install -r requirements.txt
python main.py
```

## 📋 更新日志

### v1.0.0 (2024-12-19)
- ✅ 首次正式发布
- ✅ 完整的图像隐私清理功能
- ✅ 实时文件夹监控
- ✅ 高级清理配置界面
- ✅ 自动备份和错误处理
- ✅ Windows 绿色版打包
- ✅ 主界面添加"关于"链接

## 🔧 技术规格

### 支持的图像格式
- ✅ JPEG/JPG - 完全支持
- ✅ PNG - 完全支持  
- ✅ BMP - 完全支持
- ✅ TIFF/TIF - 完全支持
- ✅ WebP - 完全支持
- ✅ HEIF/HEIC - 完全支持

### 系统要求
- **操作系统**: Windows 7/8/10/11 (64位)
- **内存**: 建议 4GB 以上
- **存储**: 至少 100MB 可用空间
- **Python**: 3.7+ (仅源码版需要)

## 📞 支持与反馈

如果您遇到问题或有建议，请：
1. 查看 README.md 中的故障排除部分
2. 在 GitHub Issues 中提交问题
3. 检查 `errorbak` 目录中的错误日志

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

---

**感谢使用 Image Privacy Guardian！** 🛡️