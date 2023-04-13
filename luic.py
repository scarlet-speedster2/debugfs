import subprocess

python2_interpreter = '/usr/bin/python2'
python2_script = 'ext.py'
#args = ['/dev/sda3', "-s"]

class Luic:


    def __init__(self,args):
        self.args = args


i = 0
input_str = 'ls'

while(1):

    try:
        command = ['sudo', python2_interpreter, python2_script] + args
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        output, error = process.communicate(input=input_str.encode())

        outs = output.decode('utf-8')
        print(outs)
    
        if i == 2:
            break
        i += 1
        input_str = 'pwd'
        
    except Exception as e:
        pass

