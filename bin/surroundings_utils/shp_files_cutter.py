import os
from subprocess import Popen

import fiona

# USEFUL TO PARTITION SWISSTOPO FILES!!!!


def cut_shp_file(inputfile: str, outputfolder: str, n_I: int, n_J: int):
    """Cuts a shp file into smaller parts

    Args:
        inputfile (str): path of original shp file
        outputfolder (str): Folder path where to write the smallere parts to
        n_I (int): number of horizontal parts
        n_J (int): number of vertical parts
    """
    with fiona.open(inputfile) as entities:
        bounds = entities.bounds
    xmin = round(bounds[0], 2)
    ymin = round(bounds[1], 2)
    xmax = round(bounds[2], 2)
    ymax = round(bounds[3], 2)

    delta_x = (xmax - xmin) / n_I
    delta_y = (ymax - ymin) / n_J

    for i in range(0, n_I):
        for j in range(0, n_J):
            x1 = xmin + i * delta_x
            x2 = xmin + (i + 1) * delta_x
            y1 = ymin + j * delta_y
            y2 = ymin + (j + 1) * delta_y
            output_name = "box_%s_%s" % (i, j)
            outputfile = outputfolder + output_name + ".shp"

            p = Popen(
                [
                    "ogr2ogr",
                    "-clipsrc",
                    "-" + str(x1),
                    str(y1),
                    str(x2),
                    str(y2),
                    outputfile,
                    inputfile,
                ]
            )
            p.wait()


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    n_I = 10
    n_J = 10

    inputfile = os.path.join(
        dir_path
        + "/../data/2019_SWISSTLM3D_SHAPE_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_STEHENDES_GEWAESSER.shp"
    )
    outputfolder = os.path.join(
        dir_path + "/../data/2019_SWISSTLM3D_SHAPE_CHLV95_LN02/TLM_GEWAESSER/clipped/"
    )

    cut_shp_file(inputfile=inputfile, outputfolder=outputfolder, n_I=n_I, n_J=n_J)
