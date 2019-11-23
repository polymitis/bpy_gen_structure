#!/usr/bin/env python3
#
# This script is exporting a 1-level 3-D structure model according to the input floorplan specification.
#
# Example usage for this test:
#  Running the generator with blender in background mode:
#    blender --background --factory-startup \
#    --python $HOME/bpy_gen_structure.py -- \
#    --floorplan=$specs/room.dat\
#    --panel=$primitives/panel.glb \
#    --save=$models/room.blend
#
#  Running the generator using Blender as a Python module:
#    python $HOME/bpy_gen_structure.py \
#    --floorplan=$specs/room.dat \
#    --panel=$primitives/panel.glb \
#    --save=$models/room.blend
#
# Notice:
# '--factory-startup' is used to avoid the user default settings from
#                     interfering with automated scene generation.
#
# '--' causes blender to ignore all following arguments so python can use them.
#
# See blender --help for details.
import bpy
import numpy as np
import os


def assemble_level(plan, panel):
    for x in range(len(plan) - 1):
        for y in range(len(plan[0]) - 1):
            # add a top panel
            if x == 0 and (plan[x][y] == 1 or plan[x][y] == -1) and plan[x][y + 1] == 1:
                bpy.ops.object.select_all(action='DESELECT')
                panel.select_set(True)
                bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'},
                                              TRANSFORM_OT_translate={"value": (x, 2 * y, 0)})
            # add a right panel
            if (plan[x][y] == 1 or plan[x][y] == -1) and plan[x + 1][y] == 1:
                bpy.ops.object.select_all(action='DESELECT')
                panel.select_set(True)
                bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
                bpy.ops.transform.rotate(value=-1.5708, orient_axis='Z')
                bpy.ops.transform.translate(value=(2 * x + 1, 2 * y - 1, 0))
            # add a left panel
            if (plan[x][y + 1] == 1 or plan[x][y + 1] == -1) and plan[x + 1][y + 1] == 1:
                bpy.ops.object.select_all(action='DESELECT')
                panel.select_set(True)
                bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
                bpy.ops.transform.rotate(value=-1.5708, orient_axis='Z')
                bpy.ops.transform.translate(value=(2 * x + 1, 2 * y + 1, 0))
            # add a bottom panel
            if (plan[x + 1][y] == 1 or plan[x + 1][y] == -1) and plan[x + 1][y + 1] == 1:
                bpy.ops.object.select_all(action='DESELECT')
                panel.select_set(True)
                bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'},
                                              TRANSFORM_OT_translate={"value": (2 * x + 2, 2 * y, 0)})


def gen_structure(plan, panel):
    # assemble structure
    assemble_level(plan, panel)

    # remove template
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[panel.name].select_set(True)
    bpy.ops.object.delete()

    # join all panels
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.join()


def add_bump_voronoi_material(panel):
    mat_name = 'bump_voronoi'
    material = bpy.data.materials.get(mat_name)
    # create the material if it doesn't already exist
    if not material:
        # create an empty material
        material = bpy.data.materials.new(mat_name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # clear all default nodes
        while nodes:
            nodes.remove(nodes[0])

        # connect a default bump shader to a default Voronoi texture shader and to the output
        shd_bump = nodes.new("ShaderNodeBump")
        shd_tex_voronoi = nodes.new("ShaderNodeTexVoronoi")
        shd_out_mat = nodes.new("ShaderNodeOutputMaterial")
        links.new(shd_tex_voronoi.inputs['Vector'], shd_bump.outputs['Normal'])
        links.new(shd_out_mat.inputs['Surface'], shd_tex_voronoi.outputs['Color'])

    # add material to panel
    panel.data.materials.append(material)


def get_cmd_input():
    import sys  # to get command line args
    import argparse  # to parse options for us and print a nice help message

    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" in argv:
        argv = argv[argv.index("--"):]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = (
            "Run blender in background mode with this script:"
            "  blender --background --python " + __file__ + " -- [options]"
                                                            " --floorplan=$specs/room.dat"
                                                            " --panel=$primitives/panel.glb"
                                                            " --save=$models/room.blend "
            "or run it directly if blender as module is installed:"
            "  python " + __file__ + " --[options]"
            "                          --floorplan=/specs/room.dat"
            "                          --panel=/models/panel.glb"
            "                          --save=/models/room.blend "
    )

    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument(
        "-f", "--floorplan", dest="floorplan_path", metavar='FILE', required=True,
        help="This is the input floorplan filepath",
    )

    parser.add_argument(
        "-p", "--panel", dest="panel_path", metavar='FILE', required=True,
        help="This is the input panel object filepath",
    )

    parser.add_argument(
        "-s", "--save", dest="save_path", metavar='FILE', required=True,
        help="Save the generated file to the specified path",
    )

    args = parser.parse_args(argv[1:])  # In this example we won't use the args

    if not argv:
        parser.print_help()
        exit(-1)

    if not args.floorplan_path:
        print("Error: --floorplan=<Floorplan file path> argument not given, aborting.")
        parser.print_help()
        exit(-1)

    if not args.panel_path:
        print("Error: --panel_path=<Panel object file path> argument not given, aborting.")
        parser.print_help()
        exit(-1)

    if not args.save_path:
        print("Error: --save_path=<Output blender file path> argument not given, aborting.")
        parser.print_help()
        exit(-1)

    return args.floorplan_path, args.panel_path, args.save_path


def main():
    # get command line inputs
    [plan_path, panel_path, save_path] = get_cmd_input()

    # clear existing objects
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # load specification
    with open(os.path.abspath(plan_path), 'r') as plan_file:
        # noinspection PyTypeChecker
        plan = np.loadtxt(plan_file)

    # load panel object
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(panel_path))
    panel = bpy.context.selected_objects[0]

    # add panel material
    add_bump_voronoi_material(panel)

    # generate level structure
    gen_structure(plan, panel)

    # save blender file
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save_path))

    print("batch job finished, exiting")


if __name__ == "__main__":
    main()
