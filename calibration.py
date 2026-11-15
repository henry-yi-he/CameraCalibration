"""手机棋盘格相机标定主程序。

后续在此实现角点检测、相机标定、重投影误差和图像去畸变。
输入目录：images/
输出目录：results/
标定板实测尺寸记录：board/board_info.md
"""
import cv2
import numpy as np
import matplotlib.pyplot as plt

print("OpenCV版本：", cv2.__version__)
print("NumPy版本：", np.__version__)
print(plt, cv2.__version__)