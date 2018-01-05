import os
import os.path
#from pathlib import Path

def insert_fault_code(fileLoc, faultLoc, codeline1, codeline2):
    bkupFile = fileLoc+'.bkup'
    if os.path.isfile(bkupFile) != True:
      cmd = 'cp ' + fileLoc + ' ' + bkupFile
      os.system(cmd)
    else:
      print 'Bkup file already exists!!'

    src_fp = open(fileLoc, 'w')
    bkup_fp = open(bkupFile, 'r')

    for line in bkup_fp:
      src_fp.write(line)

      if faultLoc in line:
        leadSp = len(line) - len(line.lstrip(' ')) # calculate the leading spaces

        for i in range(1, leadSp+1):
          src_fp.write(' ')
        src_fp.write(codeline1+'\n')

        for i in range(1, leadSp+3):
          src_fp.write(' ')
        src_fp.write(codeline2)

    src_fp.close()
    bkup_fp.close()

def inject_fault(fileName):
    in_file = fileName+'.txt'
    outfile_path = 'selfdrive/test/tests/plant/out/longitudinal/'

    with open(in_file, 'r') as fp:
        print in_file
        line = fp.readline() # title line
        title = line.split(':')
        title[1] = title[1].replace('\n','')

        hazardFile = open('output_files/'+title[1]+'/Hazards.txt','w')
        alertFile = open('output_files/'+title[1]+'/Alerts.txt','w')
        hazardFile.close()
        alertFile.close()

        hazardFile = open('output_files/'+title[1]+'/Hazards.txt','a+')
        alertFile = open('output_files/'+title[1]+'/Alerts.txt','a+')

        line = fp.readline() # fault location line
        lineSeg = line.split('//')
        fileLoc = lineSeg[1]
        faultLoc = lineSeg[2]
        #print fileLoc
        #print faultLoc
        for line in fp:
          #print line
          lineSeg = line.split('//')
          startWord = lineSeg[0].split(' ')
          if startWord[0]=='fault':
            insert_fault_code(fileLoc, faultLoc, lineSeg[1], lineSeg[2])
            os.system('./run_docker_tests.sh') # run the openpilot simulator

            output_dir = 'output_files/'+title[1]+'/'+startWord[1]
            if os.path.isdir(output_dir) != True:
              os.makedirs(output_dir)

            '''Copy all output files in a common directory'''
            cmd = 'cp -a ' + outfile_path+'/.' + ' ' + output_dir
            os.system(cmd)

            '''Write all hazards in single file '''
            with open(output_dir+'/hazards.txt') as hzFile:
              hazLine = hzFile.readline()  # first line
              hazardFile.write('\nHazards for fault '+startWord[1]+'::\n')
              for hazLine in hzFile:
                hazardFile.write(hazLine)

            '''Write all alerts in single file '''
            with open(output_dir+'/alerts.txt') as alFile:
              alLine = alFile.readline()  # first line
              alertFile.write('\nAlerts for fault '+startWord[1]+'::\n')
              for alLine in alFile:
                alertFile.write(alLine)

            #break

        hazardFile.close()
        alertFile.close()


inject_fault('dRelPlant')

