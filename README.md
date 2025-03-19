## TS2 GMDC Importer/Exporter for Blender 3.60+

This add-on supports rigging data, two UV layers, morphs, and bounding geometry.

#### Installation
1. Run Blender and change area to Preferences;
2. Choose "Add-ons" and press "Install...";
3. Install by selecting the io\_ts2\_gmdc.zip file;
4. Finally, enable "Import-Export: TS2 GMDC Importer/Exporter". (For easier navigation you may filter the list of add-ons by selecting "Import-Export" from the drop down list.

[![Screenshot](images/thumb_install.png "Installation")](images/install.png)

#### Importing
The importer works in two modes, Geometry and Skeleton.
To view the options, press the top right toggle button in the file selection window (if not already shown).
Geometry mode is used to import meshes from GMDC files, i.e., new mesh objects are added to the scene.
In Skeleton mode the importer loads data from CRES file, creates an armature object, and assigns armature modifiers to mesh objects.
In general, armature is not necessary for mesh editing, but may be helpful.

Key features:
* Bones are imported as vertex groups and initially named as "bone#{bone\_idx}", that is, bone index is written after the number sign. Although bone names can be changed, **do not delete or modify bone indices!** Otherwise, the exporter will most likely throw errors, since bone indices are extracted from vertex group names.
* Morphs are imported as shape keys.
* Inverse transforms from GMDC files are saved in scene properties. This data is used by the exporter and included into generated GMDC file.
* Seams can be removed by geometry reindexing (the "Remove doubles" option).
* Base normals are automatically imported as custom/per corner normals.
* Morph normals and Pet EP data are imported as custom mesh attributes.

[![Screenshot](images/thumb_image3.png "Screenshot")](images/image3.png)

#### Exporting
The exporter focuses on Geometry. 
It can handle all imported data, including bone weights, morphs, per corner normals, and the GMDC format's custom data.

Key features:
* Options to export rigging data, normal tangents, Pet EP data, mesh morphs (and their normals).
* "Align Normals" feature, which match base normals to that of a given other mesh.
* Separate handling of bounding geometry, which must exist as its own mesh.
* Option to write additional resouce info into the resulting GMDC, such as name and object properties.

#### Links:
* [DjAlex88's Original ModTheSims Post](https://modthesims.info/d/656032/the-sims-2-gmdc-importer-exporter-for-blender-2-80.html)
* [Official Blender Website](https://www.blender.org/)
