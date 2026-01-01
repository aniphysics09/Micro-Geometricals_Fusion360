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

                # ========== Add Random Triangular Prisms (with Z-rotation) ========== #
        surface_z = 5  # Top of base
        for _ in range(500):  # Adjust the number as needed
            s = random.uniform(0.2, 0.6)  # Side length
            h = random.uniform(0.2, 0.5)  # Prism height (extrusion)
            tri_height = s * math.sqrt(3) / 2

            # Triangle centered at origin in XY plane
            p1 = adsk.core.Point3D.create(-s/2, -tri_height/3, 0)
            p2 = adsk.core.Point3D.create(s/2, -tri_height/3, 0)
            p3 = adsk.core.Point3D.create(0, 2*tri_height/3, 0)

            # Create sketch for triangle base
            sketch = sketches.add(xyPlane)
            lines = sketch.sketchCurves.sketchLines
            lines.addByTwoPoints(p1, p2)
            lines.addByTwoPoints(p2, p3)
            lines.addByTwoPoints(p3, p1)
            prof = sketch.profiles.item(0)

            # Extrude triangle to form prism
            ext_input = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(h))
            prism_feature = extrudes.add(ext_input)
            prism_body = prism_feature.bodies.item(0)

            # Random rotation around Z-axis
            angle_deg = random.uniform(0, 360)
            angle_rad = math.radians(angle_deg)
            rotation_axis = adsk.core.Vector3D.create(0, 0, 1)
            rotation_origin = adsk.core.Point3D.create(0, 0, 0)

            rotation_matrix = adsk.core.Matrix3D.create()
            rotation_matrix.setToRotation(angle_rad, rotation_axis, rotation_origin)

            # Random position on top central 20×20 mm area
            x = random.uniform(-9.5, 9.5)
            y = random.uniform(-9.5, 9.5)

            translation = adsk.core.Vector3D.create(x, y, surface_z)
            rotation_matrix.translation = translation  # Add translation to rotation matrix

            # Apply transform
            move_objs = adsk.core.ObjectCollection.create()
            move_objs.add(prism_body)
            move_input = rootComp.features.moveFeatures.createInput(move_objs, rotation_matrix)
            rootComp.features.moveFeatures.add(move_input)

            # Join prism to base
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