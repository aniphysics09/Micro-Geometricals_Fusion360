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

                # ========== Add Random Flat-Lying Triangular Prisms ========== #
        surface_z = 5  # Top of the base

        for _ in range(500):  # Number of prisms
            s = random.uniform(0.2, 0.6)   # Triangle side length
            depth = random.uniform(0.2, 0.5)  # Prism thickness
            tri_height = s * math.sqrt(3) / 2

            # Triangle in XY plane centered at origin
            p1 = adsk.core.Point3D.create(-s/2, -tri_height/3, 0)
            p2 = adsk.core.Point3D.create(s/2, -tri_height/3, 0)
            p3 = adsk.core.Point3D.create(0, 2*tri_height/3, 0)

            sketch = sketches.add(xyPlane)
            lines = sketch.sketchCurves.sketchLines
            lines.addByTwoPoints(p1, p2)
            lines.addByTwoPoints(p2, p3)
            lines.addByTwoPoints(p3, p1)
            prof = sketch.profiles.item(0)

            # Extrude in Z direction (initially upright prism)
            ext_input = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
            prism_feature = extrudes.add(ext_input)
            prism_body = prism_feature.bodies.item(0)

            # Step 1: Rotate 90° about X-axis to lay it flat
            rotate1 = adsk.core.Matrix3D.create()
            rotate1.setToRotation(math.radians(90), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, 0, 0))
            bodies1 = adsk.core.ObjectCollection.create()
            bodies1.add(prism_body)
            move1 = rootComp.features.moveFeatures.createInput(bodies1, rotate1)
            rootComp.features.moveFeatures.add(move1)
            
            # Step 2: Rotate randomly around Z-axis
            angle_deg = random.uniform(0, 360)
            angle_rad = math.radians(angle_deg)
            rotate2 = adsk.core.Matrix3D.create()
            rotate2.setToRotation(angle_rad, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
            bodies2 = adsk.core.ObjectCollection.create()
            bodies2.add(prism_body)
            move2 = rootComp.features.moveFeatures.createInput(bodies2, rotate2)
            rootComp.features.moveFeatures.add(move2)
            
            # Step 3: Translate to top of base
            x = random.uniform(-9.5, 9.5)
            y = random.uniform(-9.5, 9.5)
            translate = adsk.core.Matrix3D.create()
            translate.translation = adsk.core.Vector3D.create(x, y, surface_z)
            bodies3 = adsk.core.ObjectCollection.create()
            bodies3.add(prism_body)
            move3 = rootComp.features.moveFeatures.createInput(bodies3, translate)
            rootComp.features.moveFeatures.add(move3)

            # Combine into base
            tool_bodies = adsk.core.ObjectCollection.create()
            tool_bodies.add(prism_body)
            combine_input = rootComp.features.combineFeatures.createInput(base_body, tool_bodies)
            combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            rootComp.features.combineFeatures.add(combine_input)


        # ========== Add 3 Small Cubes at Corners ========== #
        cube_positions = [
            (-10, -10),
            (10 - 1, -10),
            (-10, 10 - 1)
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

        ui.messageBox("Model created:\nCuboid base + wall + triangular prisms + 3 corner cubes.")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
