# -*- coding: utf-8 -*-
"""
Created on Sat Apr 08 20:56:11 2017
===========Full Field=======
import kml/kmz downloaded from ESA Sentinel-1 obirt mission.Convert 
it to GeoDatabase, manage its table and fields. Then split each record
of feature class/shapefile before transforming them to polygon. 
Combining into a single file with appropriate format
@author: lt
"""

import arcpy
from os.path import join
import re
#%% test arcpy.KMLToLayer_conversion()
# Set workspace (where all the KMLs are)
parameter = arcpy.GetParameterAsText(0)
parameter2 = arcpy.Describe(parameter)
work_space = parameter2.path
kml_name = parameter2.basename+'.'+parameter2.extension
#work_space = r"C:\Users\lt\Downloads\20470404-ArcPy-Line2Polygon S1 KML"
#kml_name = 'Sentinel-1B_MP_20170214T180000_20170222T180000.kml'
gdb_space = '.'.join([kml_name.split('.')[0],'gdb'])
final_shp = re.sub(r'[-: ]',r'','.'.join([kml_name.split('.')[0],'shp']))
final_shp_out = join(work_space, final_shp)
arcpy.env.workspace = work_space
arcpy.env.overwriteOutput = True
# Convert KML files to geodatabase
kml = join(work_space, kml_name)
arcpy.KMLToLayer_conversion(kml, work_space)
#%% test table field
gdb_space = '.'.join([kml_name.split('.')[0],'gdb'])
feature_name = 'Placemarks\Polylines'
#feature_namefull = join(work_space, gdb_space, feature_name)
arcpy.env.workspace = join(work_space, gdb_space)

field_list = arcpy.ListFields(feature_name)
save_field = ['OID','Shape','SensingTime','SensingMode','Shape_Length', 'EndTime']

time_format_in = 'yyyy-MM-dd HH:mm:ss'
# mysteriously the time_format_out seems did not change anything in new field!!
time_format_out = 'YYYY/MM/dd hh:mm:ss'
arcpy.ConvertTimeField_management(feature_name,"BeginTime",time_format_in,
                                  save_field[2], 'DATE',time_format_out)
  
arcpy.AddField_management(feature_name, save_field[3], 'String')
# using code-block as single expression in calculate field
expression = "getMode(!SymbolID!)"
codeblock = """def getMode(SymbolID):
    mode_dict = {0:'IW',1:'EW',2:'SM'}
    return mode_dict[SymbolID]"""
arcpy.CalculateField_management(feature_name, save_field[3], expression, 
                                "PYTHON_9.3",codeblock)
for field in field_list:
    if field.name not in save_field:
        print '{0} is a type of {1}'.format(field.name, field.type)
        arcpy.DeleteField_management(feature_name, field.name)
    else:
        continue
#%% test Extract Each Record 
spatial_ref = arcpy.Describe(feature_name).spatialReference
temp_fcset = 'temp_fcset'
arcpy.CreateFeatureDataset_management(join(work_space, gdb_space), temp_fcset, spatial_ref)
nn = 0
with arcpy.da.SearchCursor(feature_name, ["SensingTime",'SensingMode',"SHAPE@"]) as cursor:
    for row in cursor:
        nn += 1
        print nn
        out_name = 't' + str(row[0]) # Define the output shapefile name
        out_name = re.sub(r'[-: ]',r'',out_name)[:15]
        time_where = 'SensingTime = date \''+str(row[0])[:19] + '\''
        each_line = join(temp_fcset, out_name)
        each_gon = join(temp_fcset,'p'+out_name)
        arcpy.Select_analysis(feature_name, each_line ,time_where)
        arcpy.FeatureToPolygon_management(each_line, each_gon,attributes = True)
        if nn==1:
            first_gon = each_gon
        else:
            arcpy.Append_management(each_gon, first_gon, "TEST","","")
            arcpy.Delete_management(each_gon)
            arcpy.Delete_management(each_line)
arcpy.CopyFeatures_management(first_gon, final_shp_out)

#==============================================================================
# arcpy.env.workspace = join(work_space, gdb_space, temp_fcset)
# each_line_list = arcpy.ListFeatureClasses('t*','Polyline')
# 
# for each_line in each_line_list:
#     nn = nn+1
#     arcpy.FeatureToPolygon_management(each_line, 'p'+each_line,attributes = True)
#     if nn >1:
#         arcpy.Append_management('p'+each_line, 'p'+each_line_list[0], "TEST","","")
#         arcpy.Delete_management('p'+each_line)
#         arcpy.Delete_management(each_line)
# #        only works on records in featuers, result in an empty file
# #        arcpy.DeleteFeatures_management('p'+each_line)
# #arcpy.FeatureClassToFeatureClass_conversion('p'+each_line_list[0], out_path, out_name)
# arcpy.CopyFeatures_management('p'+each_line_list[0], final_shp_out)
#==============================================================================

