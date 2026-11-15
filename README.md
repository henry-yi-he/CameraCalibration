# 手机相机标定实验

本项目对应《机器视觉与三维重建》的手机相机标定上机作业。实验流程是：制作并测量棋盘格 → 用同一手机摄像头采集照片 → 检测角点 → 计算内参、畸变系数和逐张外参 → 评价重投影误差 → 对图像去畸变 → 撰写报告。

## 文件结构

```text
CameraCalibration/
├── README.md                  项目说明
├── .gitignore                 忽略本地环境和临时文件
├── requirements.txt           Python 依赖
├── board/
│   ├── board_info.md          标定板规格与实测尺寸
│   ├── checkerboard_9x6_25mm_A4.pdf  A4 横向打印版
│   └── generate_checkerboard.py     打印版生成脚本
├── images/
│   ├── README.md              拍摄与原始照片存放说明
│   └── capture_log.csv        拍摄记录
├── calibration.py             主程序入口（待实现）
├── results/
│   ├── corners/               角点检测可视化
│   ├── undistorted/           原图、去畸变图及对比图
│   ├── figures/               重投影误差等分析图
│   ├── camera_params.npz       标定参数（运行后生成）
│   └── calibration_result.txt  可读结果（运行后生成）
└── report/
    └── report.md              实验报告草稿
```

主程序目前只有说明，尚未执行标定；标明“运行后生成”的结果文件目前尚不存在。目录中的 `.gitkeep` 只用于保留空目录。

## 数据约定

- 默认计划使用 **9 × 6 个内部角点**的棋盘格，对应 **10 × 7 个方格**。方格边长以打印后实测值为准，单位为 mm，记在 `board/board_info.md`。
- 将手机原始照片直接放入 `images/`，建议按 `01.jpg`、`02.jpg` 顺序命名。保留原始文件，不覆盖或压缩。若手机输出 HEIC，后续程序需增加读取支持，或先转成不改变像素尺寸的常用格式。
- 使用同一物理摄像头、拍摄模式、焦距档位和图像分辨率。建议采集 20–30 张不同位置、倾角和距离的照片，至少保留约 15 张角点检测正确且视角有差异的照片。
- 在 `images/capture_log.csv` 记录手机、镜头、分辨率及拍摄情况；报告中使用实际测得的数据，示例数字不能当作实验结果。
- `results/` 只存程序生成的结果；实验报告放在 `report/`。参数文件中的逐张外参需要与原始照片文件名一一对应。

## 下一步

1. 准备平整的棋盘格并填写 `board/board_info.md`。
2. 拍摄并导入原始照片，填写 `images/capture_log.csv`。
3. 实现 `calibration.py`，依次完成角点检测、标定、误差计算与去畸变。
4. 将真实结果和分析写入 `report/report.md`。
