"""This file acts as the main module for this script."""

import traceback
import adsk.core
import adsk.fusion
import random
import math
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

        # ========== Create the Cuboid Base ==========
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

        # ========== Create the Boundary Wall ==========
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

        # ========== Add 500 Hemispheres ==========
        surface_z = 5  # Top of base

        for _ in range(500):
            r = random.uniform(0.1, 0.5)
            x = random.uniform(-10 + r, 10 - r)
            y = random.uniform(-10 + r, 10 - r)

            sketch_hemi = sketches.add(xyPlane)

            center = adsk.core.Point3D.create(x, y, surface_z)
            start = adsk.core.Point3D.create(x, y + r, surface_z)
            arc = sketch_hemi.sketchCurves.sketchArcs.addByCenterStartSweep(center, start, math.pi)
            end_point = arc.endSketchPoint.geometry

            line1 = sketch_hemi.sketchCurves.sketchLines.addByTwoPoints(center, start)
            line2 = sketch_hemi.sketchCurves.sketchLines.addByTwoPoints(center, end_point)

            revolves = rootComp.features.revolveFeatures
            rev_input = revolves.createInput(
                sketch_hemi.profiles.item(0),
                line1,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            )
            rev_input.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
            rev = revolves.add(rev_input)

            # Join hemisphere with base
            hemisphere_body = rev.bodies.item(0)
            tool_bodies = adsk.core.ObjectCollection.create()
            tool_bodies.add(hemisphere_body)
            combine_input = rootComp.features.combineFeatures.createInput(base_body, tool_bodies)
            combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            rootComp.features.combineFeatures.add(combine_input)

        # ========== Add 3 Small Cubes at Corners of Hemisphere Area ==========
        cube_positions = [
            (-10, -10),  # Bottom-left
            (10 - 1, -10),  # Bottom-right (shifted so cube fits inside 20×20 mm)
            (-10, 10 - 1)   # Top-left
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
            
            # Move cube up to sit on top of base (z = 5)
            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(0, 0, 5)
            
            bodies_to_move = adsk.core.ObjectCollection.create()
            bodies_to_move.add(cube_body)
            
            move_input = rootComp.features.moveFeatures.createInput(bodies_to_move, transform)
            rootComp.features.moveFeatures.add(move_input)
            
            # Join cube with base
            tool_bodies = adsk.core.ObjectCollection.create()
            tool_bodies.add(cube_body)
            combine_input = rootComp.features.combineFeatures.createInput(base_body, tool_bodies)
            combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            rootComp.features.combineFeatures.add(combine_input)


        ui.messageBox("Model created:\nCuboid + wall + 500 hemispheres + 3 corner cubes.")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

