# Aegis Folder Watch 配置文件说明

本文件夹包含 Aegis Folder Watch 的所有配置文件，软件会自动保存和加载这些配置，确保您的设置在重启后保持不变。

## 配置文件说明

### 📱 app_config.json - 应用程序配置
```json
{
  "auto_start_monitoring": false,    // 启动时自动开始监控
  "minimize_to_tray": false,         // 最小化到系统托盘
  "auto_save_logs": true,            // 自动保存日志
  "log_level": "INFO"                // 日志级别 (DEBUG/INFO/WARNING/ERROR)
}
```

### 🎨 advanced_config.json - 高级清理设置
```json
{
  "enabled": true,                   // 启用高级清理
  "hue_center": 120,                 // 色调中心值 (0-179)
  "hue_tolerance": 10,               // 色调容差 (0-90)
  "min_saturation": 50,              // 最小饱和度 (0-255)
  "min_value": 50,                   // 最小亮度 (0-255)
  "median_blur_kernel": 5,           // 中值滤波核大小 (奇数)
  "morphology_iterations": 2         // 形态学操作迭代次数
}
```

### 📁 backup_config.json - 备份设置
```json
{
  "backup_folder": "路径",           // 备份文件夹路径
  "auto_cleanup": false,             // 自动清理旧备份
  "max_backup_days": 30              // 备份保留天数
}
```

### 📂 monitored_folders.json - 监控文件夹列表
```json
[
  "文件夹路径1",
  "文件夹路径2"
]
```

### 🖥️ ui_settings.json - 界面设置
```json
{
  "window_geometry": {               // 窗口位置和大小
    "x": 100, "y": 100,
    "width": 800, "height": 600
  },
  "splitter_sizes": [350, 450],     // 分割器比例
  "theme": "blue"                    // 主题颜色
}
```

## 配置管理特性

### ✨ 自动保存
- 所有设置更改都会立即保存到对应的配置文件
- 无需手动保存，确保配置不丢失

### 🔄 自动加载
- 软件启动时自动加载所有配置
- 恢复上次的窗口位置、大小和设置

### 🛡️ 容错处理
- 配置文件损坏时自动使用默认值
- 缺失的配置项会自动补充默认值

### 📋 配置备份
- 建议定期备份此文件夹
- 可以通过复制此文件夹在不同设备间同步配置

## 注意事项

1. **不要手动删除配置文件**：软件会自动重新创建，但会丢失自定义设置
2. **路径格式**：Windows 系统中路径使用反斜杠 `\` 或正斜杠 `/` 都可以
3. **JSON 格式**：手动编辑时请确保 JSON 格式正确，否则可能导致配置加载失败
4. **权限要求**：确保软件对此文件夹有读写权限

## 故障排除

如果遇到配置相关问题：

1. **配置不生效**：检查 JSON 格式是否正确
2. **设置丢失**：检查文件夹权限，确保软件可以写入
3. **启动异常**：删除对应配置文件，软件会重新创建默认配置

---

*此配置系统确保您的所有设置都能持久保存，提供更好的用户体验。*