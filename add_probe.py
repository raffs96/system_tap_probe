#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import argparse
import lief 

stapAutogeneratedScript =  """
probe process("./{0}").function("{1}"){{
    printf("{1}\\n");
    print_usyms(ubacktrace());
    printf("\\n")
}}
"""

objcopyCommand = "objcopy --add-symbol {0}={3}:{1},function,global {2}" 

def add_probe(parser):
    listOfAddresses = parser.listOfAddresses
    debug = parser.debug
    binaryName = parser.binaryName
    outputBinaryName = parser.outputBinaryName
    autoGeneratedScriptName = parser.autoGeneratedScriptName
    section = parser.section
    os.system('cp {0} {1}'.format(binaryName,outputBinaryName)) 
    binaryName = outputBinaryName
    if(autoGeneratedScriptName):
        autoGeneratedScriptName = parser.autoGeneratedScriptName
        stapScript = open(autoGeneratedScriptName, "w")
    if( not section):
        #if section is not defined,I assume that the addresses refer to .text 
       section =".text"
    fileToPatch = lief.parse(binaryName)
    offset = 0x0
    for s in fileToPatch.sections:
        if s.name == section:
            if fileToPatch.header.file_type == lief.ELF.E_TYPE.DYNAMIC:
                #If the binary is position independent the addresses will be specified as offset from the start of the binary 
                offset = s.offset
            else:
                #if it's position dependent the addresses will be virtual 
                offset = s.virtual_address
            break;
    if(debug):
        print("Beginning of the section " + hex(offset))
    probeNumber = 0
    with open(listOfAddresses, 'r') as reader:
        for line in reader:
            if(line == "\n"):
                continue
            fields = line.split(" ")
            addr = fields[0].strip()
            probeNumber += 1   
            value = hex(int(addr,16)-offset)
            probeName = "probe"+str(probeNumber) 
            if debug:
                print("Putting "+ probeName + " in " + addr)
                print ("Offset from the beginng of the section " + value)
            if(len(fields)>=2):
                probeName = fields[1].strip()

            #Apparently the binding for lief does not allow to specify the type for a new symbol 
            #so I add it with objcopy 
            os.system(objcopyCommand.format(probeName,value,binaryName,section))
            if(autoGeneratedScriptName):
                stapScript.write(stapAutogeneratedScript.format(binaryName,probeName))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='add_probe')
    parser.add_argument('listOfAddresses', type=str, help='A file containing the list of addresses that you want probe in the format hex(address) [probe name]')
    parser.add_argument('binaryName', type=str, help='The binary to probe')
    parser.add_argument('outputBinaryName', type=str, help='The output binary')
    parser.add_argument('--autoGeneratedScriptName','-a', type=str, help='Automatically generate a system tap script to probe the functions')
    parser.add_argument('--section','-s', type=str, help='Default .text, specify if addresses refer to a different ELF section')
    parser.add_argument('--debug', '-d', action='store_true',help='enable debug logs')
    add_probe(parser.parse_args())

