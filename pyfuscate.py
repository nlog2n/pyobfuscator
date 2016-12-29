#!/usr/bin/python

# We grab these here before the namespace gets polluted:
global_names = globals().keys()

import tokenize, keyword, sys, os, optparse


class cmdline_parse:
    """Class that holds all information necessary for parsing the commandline for
correctness."""

    def __init__(self, app_version):
        self.version = app_version
        self.parser = optparse.OptionParser(usage='%prog [OPTION]...', version='%prog '+self.version)
        self.add_options()

    def parse(self):
        (self.options, self.args) = self.parser.parse_args()
        self.__handle_exceptions()

    def add_options(self):
        self.parser.add_option('-c',
                               '--count',
                               action='store',
                               type='int',
                               dest='count_index',
                               help='Specify a starting value for the name counter',
                               default=0)
        self.parser.add_option('-p',
                               '--preserve-names',
                               action='store',
                               type='string',
                               dest='preserve_names',
                               help='Specify a space-delimited list of special names to preserve',
                               default='')
        self.parser.add_option('-f',
                               '--file',
                               action='store',
                               type='string',
                               dest='input_file',
                               metavar='FILE',
                               help='The FILE to be used as input for the obfuscator',
                               default='')
        self.parser.add_option('-o',
                               '--output',
                               action='store',
                               type='string',
                               dest='output_file',
                               metavar='FILE',
                               help='The FILE to write the obfuscated output to [default=stdout]',
                               default='')

    def __handle_exceptions(self):
        if not self.options.input_file:
            self.parser.error("an input file must be specified with -f")
        else:
            if not os.access(self.options.input_file, os.R_OK):
                self.parser.error("the file '%s' specified with -f is not able to be read" % self.options.input_file)


class pyfuscate:
    """This is the class that actually takes the pristine Python sourcecode and
spits back out the obfuscated result.  Execution flow begins when self.run()
is called, which in turn calls tokenize.tokenize() with one of its own
functions (self.token_collector) specified as the output for the token stream.
Once a full line of tokens has been collected, self.token_collector calls
self.obfu(), which processes that line and prints it before clearing the token
list and returning."""

    def __init__(self, known_names=globals().keys()):
        self.indent_list = ['',]
        self.token_line = []
        self.name_dict = {}
        self.obfu_names = []
        self.counter = 0
        self.file_in = None
        self.file_out = sys.stdout
        self.known_names = known_names #Hopefully we are supplied a clean list
        self.known_names += [x for x in dir(__builtins__) if x not in self.known_names]
        self.known_names += [x for x in dir({}) if x not in self.known_names]
        self.known_names += [x for x in dir([]) if x not in self.known_names]
        self.known_names += [x for x in dir('') if x not in self.known_names]
        self.known_names += [x for x in dir(('',)) if x not in self.known_names]
        self.known_names += keyword.kwlist
        for i in self.known_names:
            try:
                x = dir(eval(i))
                self.known_names += [y for y in x if y not in self.known_names]
                for z in x:
                    try:
                        a = dir(eval(z))
                        self.known_names += [p for p in a if p not in self.known_names]
                    except NameError:
                        pass
            except (NameError, SyntaxError):
                pass

    def run(self):
        self.file_out.write('#!/usr/bin/python\n')
        tokenize.tokenize(self.file_in.readline, self.token_collector)
   
    def token_collector(self, tok_type, tok_string, tok_tuple_scoord, tok_tuple_ecoord, tok_lineno):
        if tok_type == tokenize.COMMENT:
            return
        elif tok_type == tokenize.NL:
            return
        elif tok_type == tokenize.INDENT:
            self.indent_list.append(tok_string)
            return
        elif tok_type == tokenize.DEDENT:
            self.indent_list.pop()
            return
        elif tok_type == tokenize.NEWLINE:
            self.obfu()
        else:
            self.token_line.append((tok_type, tok_string, tok_tuple_scoord, tok_tuple_ecoord, tok_lineno))
    
    def obfu(self):
        """This function does the bulk of the work in the class.  It operates on
self.token_line and prints out the obfuscated result before returning."""
        import_line = False
        bracket_stack = []
        obfu_line = ''
        if self.token_line[0][1] == 'import':
            import_line = True
        elif self.token_line[0][1] == 'from':
            return
        pop_list = self.token_line[:]
        pop_list.reverse()
        while pop_list:
            curr_item = pop_list.pop()
            tok_type = curr_item[0]
            tok_string = curr_item[1]
            if tok_type == tokenize.NAME:
                total_name_list, name_count = self.get_full_name(self.token_line[len(self.token_line)-len(pop_list)-1:])
                [pop_list.pop() for i in range(name_count-1)]
                prepped_names = []
                if import_line:
                    if len(total_name_list) > 1:
                        name = '.'.join(total_name_list)
                    else:
                        name = total_name_list[0]
                    if name not in self.known_names:
                        self.known_names.append(name)
                        try:
                            exec('import '+name)
                            try:
                                dirlist = dir(eval(name))
                                self.known_names += [y for y in dirlist if y not in self.known_names]
                                for entry in dirlist:
                                    if name+'.'+entry == 'wx.TheClipboard':
                                        # One-off special case
                                        continue
                                    try:
                                        entrylist = dir(eval(name+'.'+entry))
                                        self.known_names += [y for y in entrylist if y not in self.known_names]
                                    except NameError:
                                        pass
                            except NameError:
                                pass
                        except ImportError:
                            sys.stderr.write("Import error for: %s\n" % tok_string)
                    tok_string = name+' '
                else:
                    known_name = False
                    for name in total_name_list:
                        if name == 'self':
                            known_name = False
                        if known_name:
                            if name not in self.known_names:
                                self.known_names.append(name)
                        elif name in self.known_names:
                            known_name = True
                        elif name in self.obfu_names:
                            name = self.name_dict[name]
                        else:
                            if name[:2] == '__':
                                self.name_dict[name] = '__name'+hex(self.counter)
                            elif name[:1] == '_':
                                self.name_dict[name] = '_name'+hex(self.counter)
                            else:
                                self.name_dict[name] = 'name'+hex(self.counter)
                            self.obfu_names.append(name)
                            self.counter += 1
                            name = self.name_dict[name]
                        prepped_names.append(name)
                    tok_string = '.'.join(prepped_names)+' '
            elif tok_type == tokenize.OP:
                if tok_string == '(':
                    bracket_stack.append(tok_string)
                    tok_string += ' '
                elif tok_string == ')':
                    bracket_stack.pop()
                    tok_string += ' '
                tok_string += ' ' 
            else:
                tok_string += ' '
            obfu_line += tok_string
        self.file_out.write(self.indent_list[-1] + obfu_line + '\n')
        self.token_line = []
        
    def get_full_name(self, token_list):
        ret_names = []
        count = 0
        next = tokenize.NAME
        for item in token_list:
            if item[0] == next:
                if item[0] == tokenize.NAME:
                    ret_names.append(item[1])
                    next = tokenize.OP
                    count += 1
                elif item[0] == tokenize.OP:
                    if item[1] == '.':
                        next = tokenize.NAME
                        count += 1
                    else:
                        break
                else:
                    break
            else:
                break
        return ret_names, count
    

if __name__ == "__main__":
    prs = cmdline_parse("0.1")
    prs.parse()
    obfu = pyfuscate(global_names)
    obfu.file_in = open(prs.options.input_file, 'r')
    if prs.options.output_file:
        obfu.file_out = open(prs.options.output_file, 'w')
    obfu.counter = prs.options.count_index
    if prs.options.preserve_names:
        obfu.known_names += prs.options.preserve_names.split()
    obfu.run()

