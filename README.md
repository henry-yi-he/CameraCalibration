# CameraCalibration · 棋盘格相机标定

用手机或普通相机拍摄一组棋盘格照片，通过 Python 和 OpenCV 求解相机内参、镜头畸变和每张照片的外参。程序同时输出逐张重投影误差、角点标注图和去畸变对比图。适用于普通针孔相机模型。

## 获取与安装

可以在 GitHub 页面选择 **Code → Download ZIP** 并解压，也可以用 Git 下载：

```shell
git clone https://github.com/henry-yi-he/CameraCalibration.git
cd CameraCalibration
```

在包含 `calibration.py` 的目录中运行以下命令。已验证的 Python 版本为 3.11。已有 Python 环境时可直接执行最后一行。

```shell
conda create -n Calibration python=3.11 -y
conda activate Calibration
python -m pip install -r requirements.txt
```

## 拍摄与标定

1. 打开 [A4 棋盘格 PDF](board/checkerboard_9x6_25mm_A4.pdf)，下载这个棋盘格，横向按实际大小（100%）打印，固定在平板上。
2. 使用同一镜头、焦距档位、拍摄模式和分辨率，拍摄约 20–30 张照片。在棋盘完整入镜的前提下，改变倾角、距离和画面位置。程序需要至少 10 张检出完整角点且原始像素尺寸一致的照片。
3. 把 JPG、JPEG 或 PNG 原图放进 `images/`，可保留原文件名。
4. 运行标定。下例中的 24.8 是示例，请换成你的实测边长：

```shell
python calibration.py --square-mm 24.8
```

直接运行 `python calibration.py` 也能估计内参和畸变，此时平移量以一个方格的边长为单位。PyCharm 用户可打开项目目录、选用装有上述依赖的解释器，直接运行该脚本。

多台相机可分别指定照片目录和结果目录。脚本只扫描指定目录的第一层。重复使用同一输出目录会覆盖同名结果，请为每组数据选择独立目录。

```shell
python calibration.py --images "data/camera2" --output "results/camera2" --square-mm 24.8
```

## 读取与检查结果

| 默认路径 | 用途 |
| --- | --- |
| `results/calibration_result.txt` | 查看内参矩阵、畸变系数、每张照片的外参和误差，以及跳过照片的原因 |
| `results/camera_params.npz` | 从 Python 读取标定参数，按 `filenames` 将外参和误差对应至原图 |
| `results/corners/` | 核对彩色角点是否落在棋盘的交叉点上 |
| `results/figures/reprojection_error.png` | 比较各照片的 RMS 重投影误差，单位为像素 |
| `results/undistorted/comparison.jpg` | 首张有效照片的原图（左）与去畸变结果（右） |

```python
import numpy as np

with np.load("results/camera_params.npz") as params:
    print(params["camera_matrix"])  # fx、fy、cx、cy 均以像素计
    print(params["dist_coeffs"])    # k1, k2, p1, p2, k3
    print(params["image_size"])     # 宽、高，使用原始像素方向
```

程序读取图像时忽略 EXIF 显示旋转。将参数用于新图像时，应采用相同的镜头、分辨率、裁剪方式和像素方向。整体 RMS 反映在参与标定的照片上，预测角点与检测角点之间的偏差。

## 随附材料

- [标定板记录](board/board_info.md)、[拍摄记录空表](images/capture_log.example.csv)和[实验报告模板](report/report.md)可用于课程实验。
- 如需重新生成打印版，在环境中安装 `reportlab` 后运行 `python board/generate_checkerboard.py`。随附 PDF 可直接打印。
- 项目采用 [MIT 许可证](LICENSE)。
