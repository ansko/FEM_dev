import os
import shutil

from task import clean


clean(None)
print('WARNING! You may remove some valuable results')
answer = input('really? (y/Y/yes/YES/Yes): ')
if answer in ['y', 'Y', 'yes', 'YES', 'Yes']:
    shutil.rmtree('logs', ignore_errors=True)
    shutil.rmtree('geo', ignore_errors=True)
