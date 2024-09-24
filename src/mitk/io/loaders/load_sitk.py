# from typing import Optional
# import SimpleITK as sitk
# from pathlib import Path
# def read_dicom_series(path: str,
#                       series_id: Optional[str] = None,
#                       recursive: bool = False, 
#                       file_names: list = None):
#     """Read DICOM series as SimpleITK Image.

#     Parameters
#     ----------
#     path
#        Path to directory containing the DICOM series.

#     recursive, optional
#        Whether to recursively parse the input directory when searching for
#        DICOM series,

#     series_id, optional
#        Specifies the DICOM series to load if multiple series are present in
#        the directory. If None and multiple series are present, loads the first
#        series found.

#     file_names, optional
#         If there are multiple acquisitions/"subseries" for an individual series,
#         use the provided list of file_names to set the ImageSeriesReader.

#     Returns
#     -------
#     The loaded image.

#     """
#     reader = sitk.ImageSeriesReader()
#     if file_names is None:
#         file_names = reader.GetGDCMSeriesFileNames(path,
#                                                    seriesID=series_id if series_id else "",
#                                                    recursive=recursive)
#         # extract the names of the dicom files that are in the path variable, which is a directory
    
#     reader.SetFileNames(file_names)
    
#     # Configure the reader to load all of the DICOM tags (public+private):
#     # By default tags are not loaded (saves time).
#     # By default if tags are loaded, the private tags are not loaded.
#     # We explicitly configure the reader to load tags, including the
#     # private ones.
#     reader.MetaDataDictionaryArrayUpdateOn()
#     reader.LoadPrivateTagsOn()

#     return reader.Execute()
