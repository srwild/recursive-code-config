"""
    A script to generate Recursive fonts for code with Regular, Italic, Bold, & Bold Italic,
    as configured in config.yaml. See Readme for usage instructions.
"""

import os
import pathlib
from fontTools import ttLib
from fontTools.varLib import instancer
from opentype_feature_freezer import cli as pyftfeatfreeze
import subprocess
import shutil
from dlig2calt import dlig2calt
import yaml

# read yaml config
with open('./config.yaml') as file:
    fontOptions = yaml.load(file, Loader=yaml.FullLoader)

# GET / SET NAME HELPER FUNCTIONS

def getFontNameID(font, ID, platformID=3, platEncID=1):
    name = str(font["name"].getName(ID, platformID, platEncID))
    return name


def setFontNameID(font, ID, newName):

    print(f"\n\t• name {ID}:")
    macIDs = {"platformID": 3, "platEncID": 1, "langID": 0x409}
    winIDs = {"platformID": 1, "platEncID": 0, "langID": 0x0}

    oldMacName = font["name"].getName(ID, *macIDs.values())
    oldWinName = font["name"].getName(ID, *winIDs.values())

    if oldMacName != newName:
        print(f"\n\t\t Mac name was '{oldMacName}'")
        font["name"].setName(newName, ID, *macIDs.values())
        print(f"\n\t\t Mac name now '{newName}'")

    if oldWinName != newName:
        print(f"\n\t\t Win name was '{oldWinName}'")
        font["name"].setName(newName, ID, *winIDs.values())
        print(f"\n\t\t Win name now '{newName}'")


# ----------------------------------------------
# MAIN FUNCTION

oldName = "Recursive"

fontPath = "./font-data/Recursive_VF_1.054.ttf"

def splitFont(
        outputDirectory=f"RecMono-{fontOptions['Family Name']}",
        newName="Rec Mono",
        ttc=False,
        zip=False,
):

    # access font as TTFont object
    varfont = ttLib.TTFont(fontPath)

    fontFileName = os.path.basename(fontPath)


    outputSubDir = f"{outputDirectory}"

    for instance in fontOptions["Fonts"]:

        print(instance)

        instanceFont = instancer.instantiateVariableFont(
            varfont,
            {
                "wght": fontOptions["Fonts"][instance]["wght"],
                "CASL": fontOptions["Fonts"][instance]["CASL"],
                "MONO": fontOptions["Fonts"][instance]["MONO"],
                "slnt": fontOptions["Fonts"][instance]["slnt"],
                "CRSV": fontOptions["Fonts"][instance]["CRSV"],
            },
        )

        # UPDATE NAME ID 6, postscript name
        currentPsName = getFontNameID(instanceFont, 6)
        newPsName = (currentPsName.replace("Sans", f"{fontOptions['Family Name']}").replace(
            oldName,
            newName.replace(" ", "")).replace("LinearLight",
                                                instance.replace(" ", "")))
        setFontNameID(instanceFont, 6, newPsName)

        # UPDATE NAME ID 4, full font name
        currentFullName = getFontNameID(instanceFont, 4)
        newFullName = (currentFullName.replace("Sans", "").replace(
            oldName, newName).replace(" Linear Light", fontOptions["Family Name"]))
        setFontNameID(instanceFont, 4, newFullName)

        # UPDATE NAME ID 3, unique font ID
        currentUniqueName = getFontNameID(instanceFont, 3)
        newUniqueName = (currentUniqueName.replace("Sans", f"{fontOptions['Family Name']}").replace(
            oldName,
            newName.replace(" ", "")).replace("LinearLight",
                                                instance.replace(" ", "")))
        setFontNameID(instanceFont, 3, newUniqueName)

        # ADD name 2, style linking name
        newStyleLinkingName = instance
        setFontNameID(instanceFont, 2, newStyleLinkingName)
        setFontNameID(instanceFont, 17, newStyleLinkingName)

        # UPDATE NAME ID 1, unique font ID
        currentFamName = getFontNameID(instanceFont, 1)
        newFamName = (currentFamName.replace(" Sans", "").replace(oldName, newName).replace(
            "Linear Light",
            fontOptions["Family Name"].replace(" " + fontOptions["Family Name"], ""),
        ))
        setFontNameID(instanceFont, 1, newFamName)
        setFontNameID(instanceFont, 16, newFamName)

        newFileName = fontFileName.replace(oldName, newName.replace(
            " ", "")).replace("_VF_",
                                "-" + instance.replace(" ", "") + "-")

        # make dir for new fonts
        pathlib.Path(outputSubDir).mkdir(parents=True, exist_ok=True)

        # -------------------------------------------------------
        # OpenType Table fixes

        # drop STAT table to allow RIBBI style naming & linking on Windows
        del instanceFont["STAT"]

        # In the post table, isFixedPitched flag must be set in the code fonts
        instanceFont['post'].isFixedPitch = 1

        # In the OS/2 table Panose bProportion must be set to 9
        instanceFont["OS/2"].panose.bProportion = 9

        # Also in the OS/2 table, xAvgCharWidth should be set to 600 rather than 612 (612 is an average of glyphs in the "Mono" files which include wide ligatures).
        instanceFont["OS/2"].xAvgCharWidth = 600

        # -------------------------------------------------------
        # save instance font

        outputPath = f"{outputSubDir}/{newFileName}"

        # save font
        instanceFont.save(outputPath)

        # -------------------------------------------------------
        # Code font special stuff in post processing

        # freeze in rvrn features with pyftfeatfreeze: serifless 'f', unambiguous 'l', '6', '9'
        pyftfeatfreeze.main(["--features=rvrn,ss03,ss05,ss07,ss09", outputPath, outputPath])

        # swap dlig2calt to make code ligatures work in old code editor apps
        dlig2calt(outputPath, inplace=True)

    # -----------------------------------------------------------
    # make TTC (truetype collection) of fonts – doesn't currently work on Mac very well :(

    if ttc:
        # make list of fonts in subdir
        fontPaths = [
            os.path.abspath(outputSubDir + "/" + x)
            for x in os.listdir(outputSubDir)
        ]

        # form command
        command = f"otf2otc {' '.join(fontPaths)} -o {outputDirectory}/RecMono-{package}.ttc"
        print("▶", command, "\n")

        # run command in shell
        subprocess.run(command.split(), check=True, text=True)

        # remove dir with individual fontpaths
        shutil.rmtree(os.path.abspath(outputSubDir))

splitFont()

# if __name__ == "__main__":
#     fire.Fire(splitFont)
