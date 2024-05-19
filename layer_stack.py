import os
from osgeo import gdal
from tqdm import tqdm

# 显式启用GDAL异常处理
gdal.UseExceptions()

def resample_to_10m(input_file, output_file):
    """将输入文件重采样到10米分辨率"""
    gdal.Warp(output_file, input_file, xRes=10, yRes=10, resampleAlg='bilinear')

def layer_stacking(input_folder, output_dat):
    # 获取所有的输入文件
    input_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith('.dat')]
    input_files.sort()  # 确保文件按顺序堆叠

    if not input_files:
        raise RuntimeError(f"在文件夹 {input_folder} 中没有找到 .dat 文件")

    # 打开第一个文件以获取元数据
    first_dataset = gdal.Open(input_files[0], gdal.GA_ReadOnly)
    if first_dataset is None:
        raise RuntimeError(f"无法打开文件 {input_files[0]}")

    # 重采样到10米分辨率
    temp_folder = os.path.join(input_folder, "temp_resampled")
    os.makedirs(temp_folder, exist_ok=True)

    resample_to_10m(input_files[0], os.path.join(temp_folder, "resampled_1.dat"))
    resampled_first_dataset = gdal.Open(os.path.join(temp_folder, "resampled_1.dat"), gdal.GA_ReadOnly)
    
    target_cols = resampled_first_dataset.RasterXSize
    target_rows = resampled_first_dataset.RasterYSize
    projection = resampled_first_dataset.GetProjection()
    geotransform = resampled_first_dataset.GetGeoTransform()
    data_type = resampled_first_dataset.GetRasterBand(1).DataType

    # 创建ENVI格式的输出文件
    driver = gdal.GetDriverByName('ENVI')
    if driver is None:
        raise RuntimeError("ENVI驱动未找到")

    output_dataset = driver.Create(output_dat, target_cols, target_rows, len(input_files), data_type)
    if output_dataset is None:
        raise RuntimeError(f"无法创建输出文件: {output_dat}")

    # 设置投影和地理变换信息
    output_dataset.SetProjection(projection)
    output_dataset.SetGeoTransform(geotransform)

    # 拷贝数据到输出文件
    print("开始层叠...")
    for idx, input_file in enumerate(tqdm(input_files, desc="层叠进度", unit="file")):
        # 重采样到目标大小
        resampled_file = os.path.join(temp_folder, f"resampled_{idx + 1}.dat")
        resample_to_10m(input_file, resampled_file)

        # 打开重采样后的文件
        input_dataset = gdal.Open(resampled_file, gdal.GA_ReadOnly)
        if input_dataset is None:
            raise RuntimeError(f"无法打开文件 {resampled_file}")

        input_band = input_dataset.GetRasterBand(1)
        output_band = output_dataset.GetRasterBand(idx + 1)
        data = input_band.ReadAsArray()
        output_band.WriteArray(data)

        # 复制波段描述和NoData值
        output_band.SetDescription(input_band.GetDescription())
        no_data_value = input_band.GetNoDataValue()
        if no_data_value is not None:
            output_band.SetNoDataValue(no_data_value)

        # 复制光谱信息
        metadata = input_band.GetMetadata()
        output_band.SetMetadata(metadata)

        # 关闭输入数据集
        input_dataset = None

    # 关闭输出数据集
    output_dataset = None

    # 删除临时文件夹及其内容
    for file in os.listdir(temp_folder):
        os.remove(os.path.join(temp_folder, file))
    os.rmdir(temp_folder)

    print(f"Layer Stacking 完成: {output_dat}")

# 输入文件夹路径和输出文件路径
input_folder = "data_ans/"
output_dat = "data_ans/output_stacked.dat"

# 进行Layer Stacking
layer_stacking(input_folder, output_dat)
