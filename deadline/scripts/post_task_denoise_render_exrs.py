import os
import sys
import nuke
import time


def setColorspaceEnvironemnt(colorspace):

    if colorspace.startswith('ACES'):
        ### set OCIO environment
        rootNode = nuke.toNode('root')
        rootNode['colorManagement'].setValue('OCIO')
        rootNode['OCIO_config'].setValue('custom')
        rootNode['customOCIOConfigPath'].setValue(
            os.environ["NETWORK_COLOR"].replace("\\", "/") + '/OCIO/aces_1.0.3/config.ocio')
    else:
        print("Keeping defaults...")


def getInfoAndMerge(input_file, denoised_file, bitdepth, passes):

    file01 = input_file
    file02 = denoised_file

    ### get folders from files
    folder01, fileName01 = os.path.split(file01)
    folder02, fileName02 = os.path.split(file01)
    utilityBitDepth = int(bitdepth)
    utilityLayers = [x.strip() for x in passes.split(',')]

    ### get frame number
    curFrame = file01.rsplit('.', 2)[1]

    ### set script frame-range
    rootNode = nuke.toNode('root')
    rootNode['first_frame'].setValue(int(curFrame))
    rootNode['last_frame'].setValue(int(curFrame))
    rootNode['lock_range'].setValue(True)

    ########## set colorspace ##########
    readColorspace = nuke.nodes.Read()
    readColorspace['file'].fromUserText(file01)
    colorspace = readColorspace.metadata('exr/arnold/color_space')

    if colorspace == None:
        colorspace = "linear"

    setColorspaceEnvironemnt(colorspace)
    nuke.delete(readColorspace)
    ####################################

    ######################## CREATE NODES ################################

    ### create Read nodes
    readNoise = nuke.nodes.Read()
    readNoise['file'].fromUserText(file01)
    readNoise['first'].setValue(int(curFrame))
    readNoise['last'].setValue(int(curFrame))
    readNoise['origfirst'].setValue(int(curFrame))
    readNoise['origlast'].setValue(int(curFrame))
    readNoise['colorspace'].setValue(colorspace)

    # set project format from Read
    rootNode['format'].setValue(readNoise['format'].value())

    # crete deNoise Read node
    readDeNoise = nuke.nodes.Read()
    readDeNoise['file'].fromUserText(file02)
    readDeNoise['first'].setValue(int(curFrame))
    readDeNoise['last'].setValue(int(curFrame))
    readDeNoise['origfirst'].setValue(int(curFrame))
    readDeNoise['origlast'].setValue(int(curFrame))
    readDeNoise['colorspace'].setValue(colorspace)

    # set alpha to 1 on Shuffle
    shuffle = nuke.nodes.Shuffle()
    shuffle.setInput(0, readDeNoise)
    shuffle['alpha'].setValue('white')

    # merge original and denoised passes
    merge = nuke.nodes.Merge2()
    merge.setInput(0, readNoise)
    merge.setInput(1, shuffle)
    merge['also_merge'].setValue('all')

    # return original alpha
    copyMAIN = nuke.nodes.Copy()
    copyMAIN.setInput(0, merge)
    copyMAIN.setInput(1, readDeNoise)
    copyMAIN['from0'].setValue('rgba.alpha')
    copyMAIN['to0'].setValue('rgba.alpha')

    return fileName01, fileName02, folder01, folder02, utilityBitDepth, utilityLayers, curFrame, copyMAIN, colorspace


def splitMultiExr(fileName01, fileName02, folder01, folder02, utilityBitDepth, utilityLayers, curFrame, copyMAIN, colorspace):

    ### parameters for write nodes
    write_nodes = []
    fileType = 'exr'
    folderOutput = folder01 + "_passes"

    #create folder if doesnt exist
    if not os.path.exists(folderOutput):
        os.makedirs(folderOutput)

    ##### split all layers #####
    layersLDEV = nuke.layers(copyMAIN)
    layersUtility = []
    layersCrypto = []
    layersVariance = []

    # remove variance layers from ldev
    for layer in layersLDEV:
        # remove main variance layer
        if layer == "variance":
            layersVariance.append(layer)

        # remove light AOV variance layers
        if layer.endswith("_1"):
            if layer[:-2] in layersLDEV:
                layersVariance.append(layer)

    for i in layersVariance:
        layersLDEV.remove(i)

    # remove utility layers from ldev
    for layer in layersLDEV:
        for utility in utilityLayers:
            if layer == utility:
                layersUtility.append(layer)

    for i in layersUtility:
        layersLDEV.remove(i)

    # remove crypto from ldev
    for layer in layersLDEV:
        if layer.startswith('crypto'):
            layersCrypto.append(layer)

    for i in layersCrypto:
        layersLDEV.remove(i)

    ##### LDEV #####

    ### create Shufffle and Write Nodes
    for layer in layersLDEV:
        shuffle = nuke.nodes.Shuffle()
        shuffle.setInput(0, copyMAIN)
        shuffle['in'].setValue(layer)
        write = nuke.nodes.Write()
        write.setInput(0, shuffle)
        write['file_type'].setValue(fileType)
        if layer == 'rgba':
            layer = 'beauty'
        folderPerLayer = folderOutput + "/" + layer
        write['file'].setValue(folderPerLayer + "/" +
                               layer + "." + curFrame + ".exr")
        write['channels'].setValue('rgba')
        write['colorspace'].setValue(colorspace)

        #create layer folder and append write node to rendering list
        if not os.path.exists(folderPerLayer):
            os.makedirs(folderPerLayer)
        write_nodes.append(write)

    ##### UTILITY #####

    if len(layersUtility) != 0:
        ### create Shufffle and Write Nodes
        for layer in layersUtility:
            shuffle = nuke.nodes.Shuffle()
            shuffle.setInput(0, copyMAIN)
            shuffle['in'].setValue(layer)
            write = nuke.nodes.Write()
            write.setInput(0, shuffle)
            write['file_type'].setValue(fileType)
            folderPerLayer = folderOutput + "/" + layer
            write['file'].setValue(
                folderPerLayer + "/" + layer + "." + curFrame + ".exr")
            write['channels'].setValue('rgba')
            write['metadata'].setValue('all metadata')
            write['colorspace'].setValue(colorspace)
            if utilityBitDepth == 32:
                write['datatype'].setValue('32 bit float')

            #create layer folder and append write node to rendering list
            if not os.path.exists(folderPerLayer):
                os.makedirs(folderPerLayer)
            write_nodes.append(write)

    ##### CRYPTO #####

    if len(layersCrypto) != 0:
        ### remove viska layers from Crypto branch
        removeCrypto = layersLDEV + layersUtility
        connectInput = copyMAIN

        for layer in removeCrypto:
            remove = nuke.nodes.Remove()
            remove.setInput(0, connectInput)
            remove['operation'].setValue('remove')
            remove['channels'].setValue(layer)
            #remove['label'].setValue(layer)
            connectInput = remove

        # write node
        write = nuke.nodes.Write()
        write.setInput(0, connectInput)
        write['file_type'].setValue('exr')
        folderPerLayer = folderOutput + "/crypto"
        write['file'].setValue(folderPerLayer + '/' +
                               "crypto" + "." + curFrame + ".exr")
        write['channels'].setValue('all')
        write['metadata'].setValue('all metadata')
        write['interleave'].setValue('channels')
        write['write_full_layer_names'].setValue(True)
        write['datatype'].setValue('32 bit float')
        write['colorspace'].setValue(colorspace)

        #create layer folder and append write node to rendering list
        if not os.path.exists(folderPerLayer):
            os.makedirs(folderPerLayer)
        write_nodes.append(write)

    #deselectAll()
    for k in nuke.allNodes():
        k.knob("selected").setValue(False)

    return write_nodes


def mergeDenoisedMultiExr(fileName01, fileName02, folder01, folder02, utilityBitDepth, utilityLayers, curFrame, copyMAIN, colorspace):

    ### parameters for write nodes
    write_nodes = []
    folderOutput = folder01 + "_merged"
    #create folder if doesnt exist
    if not os.path.exists(folderOutput):
        os.makedirs(folderOutput)

    ##### split all layers #####
    layersLDEV = nuke.layers(copyMAIN)
    layersUtility = []
    layersCrypto = []

    # remove utility from ldev
    for layer in layersLDEV:
        for utility in utilityLayers:
            if layer == utility:
                layersUtility.append(layer)

    for i in layersUtility:
        layersLDEV.remove(i)

    # remove crypto from ldev
    for layer in layersLDEV:
        if layer.startswith('crypto'):
            layersCrypto.append(layer)

    for i in layersCrypto:
        layersLDEV.remove(i)

    ##### LDEV #####

    ### remove viska layers from LDEV branch
    removeLDEV = layersUtility + layersCrypto
    connectInput = copyMAIN

    for layer in removeLDEV:
        remove = nuke.nodes.Remove()
        remove.setInput(0, connectInput)
        remove['operation'].setValue('remove')
        remove['channels'].setValue(layer)
        #remove['label'].setValue(layer)
        connectInput = remove

    # write node
    write = nuke.nodes.Write()
    write.setInput(0, connectInput)
    write['file_type'].setValue('exr')
    write['file'].setValue(folderOutput + "/" + fileName01)
    write['channels'].setValue('all')
    write['metadata'].setValue('all metadata')
    write['interleave'].setValue('channels')
    write['write_full_layer_names'].setValue(True)
    write['colorspace'].setValue(colorspace)
    write_nodes.append(write)

    ##### UTILITY #####

    if len(layersUtility) != 0:
        ### remove viska layers from Utility branch
        removeUtility = layersLDEV + layersCrypto
        connectInput = copyMAIN

        for layer in removeUtility:
            remove = nuke.nodes.Remove()
            remove.setInput(0, connectInput)
            remove['operation'].setValue('remove')
            remove['channels'].setValue(layer)
            #remove['label'].setValue(layer)
            connectInput = remove

        # write node
        write = nuke.nodes.Write()
        write.setInput(0, connectInput)
        write['file_type'].setValue('exr')
        write['file'].setValue(folderOutput + "/" + fileName01.rsplit('.', 2)[0] + "_Utility" +
                               "." + fileName01.rsplit('.', 2)[1] + "." + fileName01.rsplit('.', 2)[2])
        write['channels'].setValue('all')
        write['metadata'].setValue('all metadata')
        write['interleave'].setValue('channels')
        write['write_full_layer_names'].setValue(True)
        write['colorspace'].setValue(colorspace)
        if utilityBitDepth == 32:
            write['datatype'].setValue('32 bit float')
        write_nodes.append(write)

    ##### CRYPTO #####

    if len(layersCrypto) != 0:
        ### remove viska layers from Crypto branch
        removeCrypto = layersLDEV + layersUtility
        connectInput = copyMAIN

        for layer in removeCrypto:
            remove = nuke.nodes.Remove()
            remove.setInput(0, connectInput)
            remove['operation'].setValue('remove')
            remove['channels'].setValue(layer)
            #remove['label'].setValue(layer)
            connectInput = remove

        # write node
        write = nuke.nodes.Write()
        write.setInput(0, connectInput)
        write['file_type'].setValue('exr')
        write['file'].setValue(folderOutput + "/" + fileName01.rsplit('.', 2)[0] + "_Crypto" +
                               "." + fileName01.rsplit('.', 2)[1] + "." + fileName01.rsplit('.', 2)[2])
        write['channels'].setValue('all')
        write['metadata'].setValue('all metadata')
        write['interleave'].setValue('channels')
        write['write_full_layer_names'].setValue(True)
        write['datatype'].setValue('32 bit float')
        write['colorspace'].setValue(colorspace)
        write_nodes.append(write)

    # return write_nodes, folder01, fileName01
    return write_nodes


def executeWriteNodes(write_nodes):

    # render all
    t = ()
    c = len(write_nodes)
    for i, node in enumerate(write_nodes):
        f = int(node['first'].value())
        l = int(node['last'].value())

        #execute node
        nuke.execute(node, f, l, 1)
        print("%d of %d, %s is done" % (i+1, c, node.name()))
        t = t + ((f, l, 1),)


#####################################################################
############################## EXECUTE ##############################
#####################################################################

### MAIN ###
if __name__ == '__main__':

    # input_file = "Y:/PRODUCTIONS/EDV/RHY/04_COMP/SC900/Sh01/CG/LDEV/v0022/SC10_Sh01_LDEV_v0022.1002.exr"
    # denoised_file = "Y:/PRODUCTIONS/EDV/RHY/04_COMP/SC900/Sh01/CG/LDEV/v0022_denoised/SC10_Sh01_LDEV_v0022.1002.exr"
    # utility_bd = '32'
    # utility_p = 'depth, P, N'
    # singlePasses = 'True'

    input_file = sys.argv[1].replace("\\", "/")
    denoised_file = sys.argv[2].replace("\\", "/")
    utility_bd = sys.argv[3]
    utility_p = sys.argv[4]
    singlePasses = sys.argv[5]

    # # # MAIN # # #

    #get variables
    fileName01, fileName02, folder01, folder02, utilityBitDepth, utilityLayers, curFrame, copyMAIN, colorspace = getInfoAndMerge(input_file, denoised_file, utility_bd, utility_p)

    #chose multiExr or singleExrs
    if singlePasses == 'True':
        write_nodes = splitMultiExr(
            fileName01, fileName02, folder01, folder02,utilityBitDepth, utilityLayers, curFrame, copyMAIN, colorspace)
    else:
        write_nodes = mergeDenoisedMultiExr(
            fileName01, fileName02, folder01, folder02, utilityBitDepth, utilityLayers, curFrame, copyMAIN, colorspace)

    #render
    executeWriteNodes(write_nodes)
