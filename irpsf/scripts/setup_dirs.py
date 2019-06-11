import os 

from irpsf.settings.settings import *

IR_filters = ['F105W', 'F110W', 'F125W', 'F140W', 'F160W', 'F098M', 'F127M', 'F139M', 'F153M',
			  'F126N', 'F128N', 'F130N', 'F132N', 'F164N', 'F167N']

def setup_dirs():
	for f in IR_filters:
		if not os.path.isdir(SETTINGS['output_dir']+'/'+f):
			print('Making directory {}'.format(SETTINGS['output_dir']+'/'+f))
			os.makedirs(SETTINGS['output_dir']+'/'+f)

if __name__ == '__main__':
	setup_dirs()