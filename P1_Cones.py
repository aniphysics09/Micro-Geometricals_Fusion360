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

        # ========== Add 500 Random Cones ========== #
        z_base = 5  # Top of base
        move_feats = rootComp.features.moveFeatures
        combine_feats = rootComp.features.combineFeatures
        revolves = rootComp.features.revolveFeatures

        for _ in range(500):
            # Random radius and height
            r = random.uniform(0.1, 0.25)
            h = random.uniform(0.1, 0.5)

            # Random position ensuring the cone base fits within 20 mm x 20 mm
            x = random.uniform(-10 + r, 10 - r)
            y = random.uniform(-10 + r, 10 - r)

            # Sketch triangle for cone on X-Y plane
            sketch_cone = sketches.add(xyPlane)
            lines = sketch_cone.sketchCurves.sketchLines
            center = adsk.core.Point3D.create(0, 0, 0)
            radius_pt = adsk.core.Point3D.create(r, 0, 0)
            apex = adsk.core.Point3D.create(0, 0, h)
            line1 = lines.addByTwoPoints(center, radius_pt)
            line2 = lines.addByTwoPoints(radius_pt, apex)
            line3 = lines.addByTwoPoints(apex, center)

            prof_cone = sketch_cone.profiles.item(0)

            # Revolve to create cone
            axis = line3
            angle = adsk.core.ValueInput.createByString("360 deg")
            rev_input = revolves.createInput(prof_cone, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_input.setAngleExtent(False, angle)
            rev_feature = revolves.add(rev_input)
            cone_body = rev_feature.bodies.item(0)

            # Move cone to (x, y, z_base)
            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(x, y, z_base)
            move_objs = adsk.core.ObjectCollection.create()
            move_objs.add(cone_body)
            move_input = move_feats.createInput(move_objs, transform)
            move_feats.add(move_input)

            # Join cone to base
            combine_input = combine_feats.createInput(base_body, move_objs)
            combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            combine_feats.add(combine_input)
            
            
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

        ui.messageBox("Model created:\nCuboid base + wall + 500 random cones + 3 corner cubes.")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
