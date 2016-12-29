#!/usr/bin/python

import re, sys

import_line = re.compile("^import.*$", re.S|re.M)
from_line = re.compile("^from.*$", re.S|re.M)
all_lines = []
all_imports = []
final_string = "#!/usr/bin/python\n"

for i in sys.argv[1:]:
    fileh = open(i, 'r')
    lines = fileh.readlines()
    fileh.close()
    for line in lines:
        if import_line.match(line):
            items = line.split()
            for item in items[1:]:
                all_imports += [x for x in item.split(',') if x and x not in all_imports]
        elif from_line.match(line):
            continue
        else:
            all_lines.append(line)

import_string = ', '.join(all_imports)
temp_string = ''.join(all_lines)
final_string += "import "+import_string+"\n"+temp_string
print final_string
