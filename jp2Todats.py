import os
from osgeo import gdal

# 显式启用GDAL异常处理
gdal.UseExceptions()

def convert_jp2_to_dat(input_jp2, output_dat):
    try:
        # 打开JP2文件
        jp2_dataset = gdal.Open(input_jp2, gdal.GA_ReadOnly)
        if jp2_dataset is None:
            raise RuntimeError(f"无法打开输入JP2文件: {input_jp2}")

        # 获取JP2文件的尺寸和波段数
        cols = jp2_dataset.RasterXSize
        rows = jp2_dataset.RasterYSize
        bands = jp2_dataset.RasterCount
        data_type = jp2_dataset.GetRasterBand(1).DataType

        # 获取投影和地理变换信息
        projection = jp2_dataset.GetProjection()
        geotransform = jp2_dataset.GetGeoTransform()

        # 创建ENVI格式的输出文件
        driver = gdal.GetDriverByName('ENVI')
        if driver is None:
            raise RuntimeError("ENVI驱动未找到")

        output_dataset = driver.Create(output_dat, cols, rows, bands, data_type)
        if output_dataset is None:
            raise RuntimeError(f"无法创建输出文件: {output_dat}")

        # 设置投影和地理变换信息
        output_dataset.SetProjection(projection)
        output_dataset.SetGeoTransform(geotransform)

        # 拷贝数据到输出文件
        for band in range(1, bands + 1):
            input_band = jp2_dataset.GetRasterBand(band)
            output_band = output_dataset.GetRasterBand(band)
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

        # 关闭数据集
        jp2_dataset = None
        output_dataset = None
        print(f"转换完成: {input_jp2} -> {output_dat}")
    except Exception as e:
        print(f"转换过程中出现错误: {e}")

def convert_all_jp2_in_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".jp2"):
            input_jp2 = os.path.join(input_folder, filename)
            output_dat = os.path.join(output_folder, os.path.splitext(filename)[0] + '.dat')
            convert_jp2_to_dat(input_jp2, output_dat)

# 输入和输出文件夹路径
input_folder = "R10m/"
output_folder = "data_ans/"

# 进行批量转换
convert_all_jp2_in_folder(input_folder, output_folder)
