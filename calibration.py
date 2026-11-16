"""手机相机标定。直接运行可获得内参、畸变和像素误差。
测得方格边长后，可运行 python calibration.py --square-mm 实测数值，以毫米输出平移量。
"""
import argparse
from pathlib import Path

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")  # 实验图直接存盘，在 PyCharm 和命令行中都可运行。
import matplotlib.pyplot as plt


# 1. 项目路径与棋盘参数
ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "images"
RESULTS = ROOT / "results"
PATTERN = (9, 6)  # 每行、每列的内部角点数；打印板共有 10×7 个方格。
MIN_VIEWS = 10  # 本实验沿用原流程的有效照片数的下限。


def read_photo(path):
    # 手机会在 EXIF 中记录显示方向。统一使用文件存储的像素方向，
    # 使横拍和竖拍的照片共用同一像素坐标系和内参矩阵。
    return cv2.imread(str(path), cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)


def save_image(path, image):
    if not cv2.imwrite(str(path), image):
        raise OSError(f"无法写入图片 {path}")


# 2. 棋盘角点检测：先在缩小的图上定位，再回到原分辨率精化
def find_corners(gray):
    h, w = gray.shape
    scale = min(1.0, 1400 / max(h, w))
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    found, corners = cv2.findChessboardCornersSB(small, PATTERN)
    if not found:
        # 远处的小棋盘缩小后可能丢失细节，使用原图再检测一次。
        found, corners = cv2.findChessboardCornersSB(gray, PATTERN)
        return corners if found else None

    # 按实际缩放后的宽高映射像素中心，消除尺寸取整造成的偏差。
    ratio = np.array([w / small.shape[1], h / small.shape[0]], dtype=np.float32)
    corners = (corners + 0.5) * ratio - 0.5
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 40, 0.001)
    return cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), criteria)


def collect_views(paths, corner_dir):
    names, observations, skipped = [], [], []
    image_size = None
    for path in paths:
        image = read_photo(path)
        if image is None:
            skipped.append(f"{path.name} 无法读取")
            continue
        size = (image.shape[1], image.shape[0])
        if image_size is not None and size != image_size:
            skipped.append(f"{path.name} 像素尺寸 {size} 与标定组不一致")
            continue
        corners = find_corners(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        if corners is None:
            skipped.append(f"{path.name} 未找到完整的 9×6 角点")
            continue
        image_size = size
        names.append(path.name)
        observations.append(corners)
        cv2.drawChessboardCorners(image, PATTERN, corners, True)
        save_image(corner_dir / path.name, image)
        print(f"{path.name} 检出 {len(corners)} 个角点")
    for reason in skipped:
        print(reason)
    if len(names) < MIN_VIEWS:
        raise ValueError(f"本次仅有 {len(names)} 张有效照片，实验需要至少 {MIN_VIEWS} 张。")
    return names, observations, image_size, skipped


# 3. 参数求解：棋盘位于 Z=0 平面，各照片共享内参，各有一组外参
def calibrate(observations, image_size, spacing):
    cols, rows = PATTERN
    grid = np.zeros((cols * rows, 3), dtype=np.float32)
    grid[:, :2] = np.mgrid[:cols, :rows].T.reshape(-1, 2) * spacing
    object_points = [grid for _ in observations]
    rms, K, dist, rvecs, tvecs = cv2.calibrateCamera(
        object_points, observations, image_size, None, None
    )
    return grid, rms, K, dist, rvecs, tvecs


# 4. 重投影误差：在原图上比较检测位置和模型预测位置，单位为像素
def reprojection_errors(grid, observations, K, dist, rvecs, tvecs):
    distances = []
    for detected, rotation, translation in zip(observations, rvecs, tvecs):
        predicted, _ = cv2.projectPoints(grid, rotation, translation, K, dist)
        # OpenCV 版本不同可能返回 (N,2) 或 (N,1,2)，先统一形状再逐点配对。
        residual = detected.reshape(-1, 2) - predicted.reshape(-1, 2)
        distances.append(np.linalg.norm(residual, axis=1))
    distances = np.asarray(distances, dtype=np.float64)
    # RMS 是距离平方平均后开方；平均欧氏距离直接对各点距离求平均。
    per_view_rms = np.sqrt(np.mean(distances ** 2, axis=1))
    return per_view_rms, distances.mean()


def plot_errors(names, errors, figure_path):
    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    ax.bar(names, errors)
    ax.set(xlabel="Image", ylabel="Reprojection RMS (px)")
    ax.tick_params(axis="x", labelrotation=45)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


# 5. 去畸变：使用首张有效照片，保持原分辨率和完整视野，生成左右对比图
def undistort_example(photo_path, folder, image_size, K, dist):
    original = read_photo(photo_path)
    new_K, _ = cv2.getOptimalNewCameraMatrix(K, dist, image_size, 1, image_size)
    corrected = cv2.undistort(original, K, dist, None, new_K)
    save_image(folder / "original.jpg", original)
    save_image(folder / "undistorted.jpg", corrected)
    save_image(folder / "comparison.jpg", np.hstack([original, corrected]))


# 6. 主流程与输出：外参、误差均按 filenames 的顺序保存
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, default=IMAGES, help="标定照片目录（默认 images）")
    parser.add_argument("--output", type=Path, default=RESULTS, help="结果目录（默认 results）")
    parser.add_argument("--square-mm", type=float, help="打印后实测的方格边长（毫米）")
    args = parser.parse_args()
    square_mm = args.square_mm
    source, output = args.images.resolve(), args.output.resolve()
    if not source.is_dir():
        parser.error(f"找不到照片目录 {source}")
    if source == output or output in source.parents:
        parser.error("请将输出目录设在照片目录之外，或使用单独的输出子目录")
    if square_mm is not None and (not np.isfinite(square_mm) or square_mm <= 0):
        parser.error("--square-mm 必须是有限正数")
    spacing = 1.0 if square_mm is None else square_mm
    unit = "squares" if square_mm is None else "mm"
    paths = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if len(paths) < MIN_VIEWS:
        parser.error(f"{source} 中有 {len(paths)} 张支持的照片，请放入至少 {MIN_VIEWS} 张 JPG、JPEG 或 PNG")
    for folder in ("corners", "figures", "undistorted"):
        (output / folder).mkdir(parents=True, exist_ok=True)

    names, observations, size, skipped = collect_views(paths, output / "corners")
    grid, rms, K, dist, rvecs, tvecs = calibrate(observations, size, spacing)
    errors, mean_distance = reprojection_errors(grid, observations, K, dist, rvecs, tvecs)
    plot_errors(names, errors, output / "figures" / "reprojection_error.png")
    undistort_example(source / names[0], output / "undistorted", size, K, dist)
    np.savez(output / "camera_params.npz", camera_matrix=K, dist_coeffs=dist,
             rvecs=rvecs, tvecs=tvecs, filenames=names, image_size=size,
             pattern_size=PATTERN, square_mm=np.nan if square_mm is None else square_mm,
             translation_unit=unit, rms=rms, per_view_rms=errors, mean_distance_px=mean_distance)
    scale_note = "未填写实测边长，平移单位为格" if square_mm is None else f"实测边长 {square_mm:g} mm，平移单位为 mm"
    lines = [
        f"有效照片 {len(names)}/{len(paths)}，分辨率 {size[0]}×{size[1]}（原始像素方向）",
        f"内部角点 {PATTERN[0]}×{PATTERN[1]}，{scale_note}",
        f"内参矩阵 K（焦距、主点以像素计）\n{K}",
        f"畸变参数 [k1, k2, p1, p2, k3]\n{dist.ravel()}",
        f"整体 RMS {rms:.4f} px，平均欧氏距离 {mean_distance:.4f} px",
        f"去畸变对比图使用 {names[0]}，左为原图，右为校正图",
        "逐张外参（棋盘坐标到相机坐标，rvec 为 Rodrigues 旋转向量，角度单位 rad）",
    ]
    for name, rotation, translation, error in zip(names, rvecs, tvecs, errors):
        lines.append(f"{name}  RMS={error:.4f} px  rvec={rotation.ravel()}  tvec={translation.ravel()}")
    lines.extend(skipped)
    (output / "calibration_result.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:5]))
    print(f"结果已保存到 {output}")


if __name__ == "__main__":
    main()
