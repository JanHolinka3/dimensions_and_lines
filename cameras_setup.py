import bpy # type: ignore

class CAMERA_DIMSELECT(bpy.types.Operator):
    """
    Set selected object as camera.
    """
    bl_idname = "camera.dimselect"
    bl_label = "Set object as camera"
    bl_description = "Set selected object as camera"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'
    
    def execute(self, context):  

        countObjektu = 0
        selectedObject = None
        for object in context.selected_objects:
            countObjektu = countObjektu + 1
            selectedObject = object

        if countObjektu == 0:
            self.report({'ERROR'}, "No object selected.")
            return {'CANCELLED'}
        
        if countObjektu > 1:
            self.report({'ERROR'}, "Too many objects selected, select only one camera.")
            return {'CANCELLED'}

        if selectedObject.type != 'CAMERA':
            self.report({'ERROR'}, "Selected object is not camera.")
            return {'CANCELLED'}

        bpy.context.scene.DIMENSION.cameraOb = selectedObject.name
        
        return {'FINISHED'}
    
class CAMERA_DimSetupCam(bpy.types.Operator):
    """
    Set camera to paper
    """
    bl_idname = "camera.dimsetupcam"
    bl_label = "Set camera to paper"
    bl_description = "Set camera to paper"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'
    
    def execute(self, context):

        try:
            objectCam = context.scene.objects[context.scene.DIMENSION.cameraOb]
            if objectCam.type != 'CAMERA':
                self.report({'ERROR'}, "Something is wrong with selected camera. Setup camera.")
                context.scene.DIMENSION.cameraOb = ''
                return {'CANCELLED'}
            #print(objectCam.name)

        except:
            self.report({'ERROR'}, "Something is wrong with selected camera. Setup camera.")
            context.scene.DIMENSION.cameraOb = ''
            return {'CANCELLED'}
        
        xRozmer = int(0)
        yRozmer = int(0)
        if context.scene.DIMENSION.paperFormats == 'A5':
            xRozmer = 210
            yRozmer = 148
        if context.scene.DIMENSION.paperFormats == 'A4':
            xRozmer = 297
            yRozmer = 210
        if context.scene.DIMENSION.paperFormats == 'A3':
            xRozmer = 420
            yRozmer = 297
        if context.scene.DIMENSION.paperFormats == 'A2':
            xRozmer = 594
            yRozmer = 420
        if context.scene.DIMENSION.paperFormats == 'A1':
            xRozmer = 841
            yRozmer = 594
        if context.scene.DIMENSION.paperFormats == 'A0':
            xRozmer = 1189
            yRozmer = 841
        if context.scene.DIMENSION.paperFormats == 'Letter':
            xRozmer = 279.4
            yRozmer = 215.9
        if context.scene.DIMENSION.paperFormats == 'Legal':
            xRozmer = 355.6
            yRozmer = 215.9
        if context.scene.DIMENSION.paperFormats == 'Ledger':
            xRozmer = 431.8
            yRozmer = 279.4
        if context.scene.DIMENSION.paperFormats == 'ARCH A':
            xRozmer = 304.8
            yRozmer = 228.6
        if context.scene.DIMENSION.paperFormats == 'ARCH B':
            xRozmer = 457.2
            yRozmer = 304.8
        if context.scene.DIMENSION.paperFormats == 'ARCH C':
            xRozmer = 609.6
            yRozmer = 457.2
        if context.scene.DIMENSION.paperFormats == 'ARCH D':
            xRozmer = 914.4
            yRozmer = 609.6
        if context.scene.DIMENSION.paperFormats == 'ARCH E':
            xRozmer = 1219.2
            yRozmer = 914.4
        if context.scene.DIMENSION.paperFormats == 'ANSI A':
            xRozmer = 279.4
            yRozmer = 215.9
        if context.scene.DIMENSION.paperFormats == 'ANSI B':
            xRozmer = 431.8
            yRozmer = 279.4
        if context.scene.DIMENSION.paperFormats == 'ANSI C':
            xRozmer = 558.8
            yRozmer = 431.8
        if context.scene.DIMENSION.paperFormats == 'ANSI D':
            xRozmer = 863.6
            yRozmer = 558.8
        if context.scene.DIMENSION.paperFormats == 'ANSI E':
            xRozmer = 1117.6
            yRozmer = 863.6
        vetsiRozmer = xRozmer
        if context.scene.DIMENSION.widePaper == False:
            tmp = xRozmer
            xRozmer = yRozmer
            yRozmer = tmp
            vetsiRozmer = yRozmer

        #297/25.4 * 300 = 3 507.874
        context.scene.render.resolution_x = int(xRozmer/25.4 * context.scene.DIMENSION.dpi)
        context.scene.render.resolution_y = int(yRozmer/25.4 * context.scene.DIMENSION.dpi)

        #camera orto vetsi rozmer x scale?
        camObject = context.scene.objects[context.scene.DIMENSION.cameraOb]
        camObject.rotation_euler[0] = 0
        camObject.rotation_euler[1] = 0
        camObject.rotation_euler[2] = 0
        camObject.data.type = 'ORTHO'
        camObject.data.ortho_scale = (vetsiRozmer/1000) * context.scene.DIMENSION.scale

        return {'FINISHED'}