"""This file acts as the main module for this script."""

import traceback
import adsk.core
import adsk.fusion
import math
import random
# import adsk.cam

# Initialize the global variables for the Application and UserInterface objects.
app = adsk.core.Application.get()
ui  = app.userInterface


def run(_context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        rootComp = design.rootComponent

        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        extrudes = rootComp.features.extrudeFeatures
        moveFeats = rootComp.features.moveFeatures

        # ===== Base Cuboid =====
        sketch_base = sketches.add(xyPlane)
        sketch_base.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-20, -20, 0),
            adsk.core.Point3D.create(20, 20, 0)
        )
        prof_base = sketch_base.profiles.item(0)
        ext_input_base = extrudes.createInput(prof_base, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_input_base.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5))
        ext_base = extrudes.add(ext_input_base)
        base_body = ext_base.bodies.item(0)

        # ===== Boundary Wall =====
        sketch_wall = sketches.add(xyPlane)
        sketch_wall.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-22.5, -22.5, 0),
            adsk.core.Point3D.create(22.5, 22.5, 0)
        )
        sketch_wall.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-20, -20, 0),
            adsk.core.Point3D.create(20, 20, 0)
        )
        prof_wall = sketch_wall.profiles.item(0)
        ext_input_wall = extrudes.createInput(prof_wall, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_input_wall.setDistanceExtent(False, adsk.core.ValueInput.createByReal(10))
        extrudes.add(ext_input_wall)

        # ===== Flat Cylinders (Half X-Z, Half Y-Z) =====
        for _ in range(500):
            diameter = random.uniform(0.2, 0.8)
            height = random.uniform(0.2, 0.5)
            
            # Generate x, y such that cylinders don't overflow outside 20x20 mm
            x = random.uniform(-10 + height/2, 10 - height/2)
            y = random.uniform(-10 + diameter/2, 10 - diameter/2)
            
            sketch_cyl = sketches.add(xyPlane)
            sketch_cyl.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(0, 0, 0), diameter / 2
            )
            
            prof_cyl = sketch_cyl.profiles.item(0)
            ext_input_cyl = extrudes.createInput(prof_cyl, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_input_cyl.setDistanceExtent(False, adsk.core.ValueInput.createByReal(height))
            ext_cyl = extrudes.add(ext_input_cyl)
            cyl_body = ext_cyl.bodies.item(0)
            
            # Create transformation: rotate + translate
            transform = adsk.core.Matrix3D.create()
            
            if x < 0:
                # Left half → rotate around Y → lies along X-Z
                axis = adsk.core.Vector3D.create(0, 1, 0)
            else:
                # Right half → rotate around X → lies along Y-Z
                axis = adsk.core.Vector3D.create(1, 0, 0)
                
            rotation = adsk.core.Matrix3D.create()
            rotation.setToRotation(math.pi / 2, axis, adsk.core.Point3D.create(0, 0, 0))
            transform.transformBy(rotation)
            
            transform.translation = adsk.core.Vector3D.create(x, y, 5)
            
            move_objs = adsk.core.ObjectCollection.create()
            move_objs.add(cyl_body)
            move_input = moveFeats.createInput(move_objs, transform)
            moveFeats.add(move_input)
            
            # Join cylinder to base
            tool_bodies = adsk.core.ObjectCollection.create()
            tool_bodies.add(cyl_body)
            combine_input = rootComp.features.combineFeatures.createInput(base_body, tool_bodies)
            combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            rootComp.features.combineFeatures.add(combine_input)
            
            
        # ===== Add 3 Small Cubes at Corners =====
        cube_positions = [
            (-10, -10),
            (9, -10),
            (-10, 9)
        ]

        for x, y in cube_positions:
            sketch_cube = sketches.add(xyPlane)
            sketch_cube.sketchCurves.sketchLines.addTwoPointRectangle(
                adsk.core.Point3D.create(x, y, 0),
                adsk.core.Point3D.create(x + 1, y + 1, 0)
            )
            prof_cube = sketch_cube.profiles.item(0)
            ext_input_cube = extrudes.createInput(prof_cube, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_input_cube.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1))
            cube_feature = extrudes.add(ext_input_cube)
            cube_body = cube_feature.bodies.item(0)

            # Move to top of base
            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(0, 0, 5)
            bodies = adsk.core.ObjectCollection.create()
            bodies.add(cube_body)
            move_input = rootComp.features.moveFeatures.createInput(bodies, transform)
            rootComp.features.moveFeatures.add(move_input)

            # Join to base
            tool_bodies = adsk.core.ObjectCollection.create()
            tool_bodies.add(cube_body)
            combine_input = rootComp.features.combineFeatures.createInput(base_body, tool_bodies)
            combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            rootComp.features.combineFeatures.add(combine_input)

        ui.messageBox("Flat (sideways) cylinders added. Done!")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))