import os
import sys
import nuke


def splitFix(folder01, folder02):
    write_nodes = []
    passes = "coat, coat_direct, coat_indirect, diffuse, diffuse_direct, diffuse_indirect, direct, emission, indirect, specular, specular_direct, specular_indirect, sss, sss_direct, sss_indirect, transmission, transmission_direct, transmission_indirect"

    ### get files
    origin_files = []
    for file in os.listdir(folder01):
        if file.endswith(".exr"):
            origin_files.append(file)
    
    origin_files = sorted(origin_files)

    first_file = origin_files[0]
    last_file = origin_files[-1]

    ### get first and last frame
    firstFrame = first_file.split('.')[1]
    lastFrame = last_file.split('.')[1]

    filename = first_file.split('.')[0] + "." + "####" + ".exr"
    
    file01 = os.path.join(folder01, filename)
    file02 = os.path.join(folder02, filename)

    ###
    deNoisePasses = []
    for i in passes.split(', '):
        deNoisePasses.append(i.strip())
    deNoisePasses.append("rgba")

    ##### NUKE #####

    ### set OCIO environment
    rootNode = nuke.toNode('root')
    rootNode['colorManagement'].setValue('OCIO')
    rootNode['OCIO_config'].setValue('custom')
    rootNode['customOCIOConfigPath'].setValue(
        'Q:/color/OCIO/aces_1.0.3/config.ocio')

    for i in nuke.allNodes():
        if i.Class() == "Viewer":
            if i['viewerProcess'].value() != 'sRGB (ACES)':
                name = i['name'].value()
                viewerInputs = nuke.dependencies(i)
                xpos = i.xpos()
                ypos = i.ypos()
                viewer = nuke.nodes.Viewer()
                nuke.delete(i)
                viewer['name'].setValue(name)
                viewer.setXYpos(xpos, ypos)
                viewer['viewerProcess'].setValue('sRGB (ACES)')
                for count, input in enumerate(viewerInputs):
                    viewer.setInput(count, input)
                nuke.show(viewer)

    ### set script frame-range
    rootNode['first_frame'].setValue(int(firstFrame))
    rootNode['last_frame'].setValue(int(lastFrame))
    rootNode['lock_range'].setValue(True)

    ### parameters for write nodes
    fileType = 'exr'
    #padding = "%04d"
    folderOutput = folder01 + "_passes"
    #create folder if doesnt exist
    if not os.path.exists(folderOutput):
        os.makedirs(folderOutput)

    ######################## NOISE ################################

    ### create Read node
    readNoise = nuke.nodes.Read()
    readNoise['file'].fromUserText(file01)
    readNoise['first'].setValue(int(firstFrame))
    readNoise['last'].setValue(int(lastFrame))
    readNoise['origfirst'].setValue(int(firstFrame))
    readNoise['origlast'].setValue(int(lastFrame))

    ### set project format from Read
    rootNode['format'].setValue(readNoise['format'].value())

    ### layers for noise input
    layersNoise = nuke.layers(readNoise)
    layersDeNoise = []

    for layer in layersNoise:
        for deNoisePass in deNoisePasses:
            if layer == deNoisePass:
                layersDeNoise.append(layer)

    for i in layersDeNoise:
        layersNoise.remove(i)

    ### remove crypto layers
    cryptoPasses = ['crypto_asset', 'crypto_material', 'crypto_object']
    hasCrypto = False

    layersToRemove = []
    for layer in layersNoise:
        for crypto in cryptoPasses:
            if layer.startswith(crypto):
                layersToRemove.append(layer)
                hasCrypto = True

    for i in layersToRemove:
       layersNoise.remove(i)

    ### create Shufffle and Write Nodes
    for layer in layersNoise:
        shuffle = nuke.nodes.Shuffle()
        shuffle.setInput(0, readNoise)
        shuffle['in'].setValue(layer)
        write = nuke.nodes.Write()
        write.setInput(0, shuffle)
        write['file_type'].setValue(fileType)
        write['file'].setValue(folderOutput+"/"+layer +
                               "." + "####" + "." + fileType)
        write['channels'].setValue('rgba')
        write_nodes.append(write)

    ######################## CRYPTO ################################

    if hasCrypto:
        for crypto in cryptoPasses:
            remove = nuke.nodes.Remove()
            remove.setInput(0, readNoise)
            remove['operation'].setValue('keep')
            remove['channels'].setValue(crypto)
            remove['channels2'].setValue(crypto + "00")
            remove['channels3'].setValue(crypto + "01")
            remove['channels4'].setValue(crypto + "02")
            write = nuke.nodes.Write()
            write.setInput(0, remove)
            write['file_type'].setValue('exr')
            write['file'].setValue(folderOutput+"/"+crypto +
                                   "." + "####" + "." + fileType)
            write['channels'].setValue('all')
            write['datatype'].setValue('32 bit float')
            write['metadata'].setValue('all metadata')
            write_nodes.append(write)

        #deselectAll()
        for k in nuke.allNodes():
            k.knob("selected").setValue(False)

    ######################## DENOISE ################################

    ### create Read node
    readNoise = nuke.nodes.Read()
    readNoise['file'].fromUserText(file02)
    readNoise['first'].setValue(int(firstFrame))
    readNoise['last'].setValue(int(lastFrame))
    readNoise['origfirst'].setValue(int(firstFrame))
    readNoise['origlast'].setValue(int(lastFrame))

    ### create Shufffle and Write Nodes
    for layer in layersDeNoise:
        shuffle = nuke.nodes.Shuffle()
        shuffle.setInput(0, readNoise)
        shuffle['in'].setValue(layer)
        write = nuke.nodes.Write()
        write.setInput(0, shuffle)
        write['file_type'].setValue(fileType)
        write['file'].setValue(folderOutput+"/"+layer +
                               "." + "####" + "." + fileType)
        write['channels'].setValue('rgba')
        write_nodes.append(write)

    #deselectAll()
    for k in nuke.allNodes():
        k.knob("selected").setValue(False)

    # render all
    # c = len(write_nodes)
    # for i, node in enumerate(write_nodes):
    #     # execute node
    #     nuke.execute(node, int(firstFrame), int(lastFrame))
    #     print("%d of %d, %s is done" % (i, c, node.name()))

### EXECUTE ###
folder01 = sys.argv[1].replace("\\", "/")
folder02 = sys.argv[2].replace("\\", "/")

splitFix(folder01, folder02)
