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

        # ========== Create the Cuboid Base ========== #
        sketch_base = sketches.add(xyPlane)
        sketch_base.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-20, -20, 0),
            adsk.core.Point3D.create(20, 20, 0)
        )

        prof_base = sketch_base.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        ext_input_base = extrudes.createInput(prof_base, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_input_base.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5))
        ext_base = extrudes.add(ext_input_base)
        base_body = ext_base.bodies.item(0)

        # ========== Create the Boundary Wall ========== #
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

        # ========== Add 500 Randomly Oriented Cuboids on Top ========== #
        surface_z = 5  # Top of base
        
        for _ in range(500):
            # Random size
            w = random.uniform(0.1, 0.5)
            d = random.uniform(0.1, 0.5)
            h = random.uniform(0.1, 0.5)
            
            # Random rotation angle (in radians)
            angle = random.uniform(0, 2 * math.pi)
            
            # Compute effective bounding box after rotation to stay within 20x20 area
            dx = abs(math.cos(angle)) * w / 2 + abs(math.sin(angle)) * d / 2
            dy = abs(math.sin(angle)) * w / 2 + abs(math.cos(angle)) * d / 2
            
            x = random.uniform(-10 + dx, 10 - dx)
            y = random.uniform(-10 + dy, 10 - dy)
            
            # Create rectangle at origin
            sketch_cuboid = sketches.add(xyPlane)
            sketch_cuboid.sketchCurves.sketchLines.addTwoPointRectangle(
                adsk.core.Point3D.create(-w / 2, -d / 2, 0),
                adsk.core.Point3D.create(w / 2, d / 2, 0)
            )
            
            # Extrude vertically to form the cuboid
            prof_cuboid = sketch_cuboid.profiles.item(0)
            ext_input = extrudes.createInput(prof_cuboid, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(h))
            ext_result = extrudes.add(ext_input)
            cuboid_body = ext_result.bodies.item(0)
            
            # Apply rotation about Z-axis and translate to (x, y, surface_z)
            transform = adsk.core.Matrix3D.create()
            
            # Rotate about Z
            rotZ = adsk.core.Matrix3D.create()
            rotZ.setToRotation(angle, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
            transform.transformBy(rotZ)
            
            # Then translate
            transform.translation = adsk.core.Vector3D.create(x, y, surface_z)
            
            # Apply transformation
            move_objs = adsk.core.ObjectCollection.create()
            move_objs.add(cuboid_body)
            move_input = rootComp.features.moveFeatures.createInput(move_objs, transform)
            rootComp.features.moveFeatures.add(move_input)
            
            # Join with base
            tool_bodies = adsk.core.ObjectCollection.create()
            tool_bodies.add(cuboid_body)
            combine_input = rootComp.features.combineFeatures.createInput(base_body, tool_bodies)
            combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            rootComp.features.combineFeatures.add(combine_input)
            
            
        # ========== Add 3 Small Cubes at Corners ========== #
        cube_positions = [
            (-10, -10),   # Corner 1
            (10 - 1, -10), # Corner 2
            (-10, 10 - 1)  # Corner 3
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

            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(0, 0, 5)
            bodies = adsk.core.ObjectCollection.create()
            bodies.add(cube_body)
            move_input = rootComp.features.moveFeatures.createInput(bodies, transform)
            rootComp.features.moveFeatures.add(move_input)

            tool_bodies = adsk.core.ObjectCollection.create()
            tool_bodies.add(cube_body)
            combine_input = rootComp.features.combineFeatures.createInput(base_body, tool_bodies)
            combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            rootComp.features.combineFeatures.add(combine_input)

        ui.messageBox("Model created:\nCuboid base + wall + 500 random cuboids + 3 corner cubes.")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
