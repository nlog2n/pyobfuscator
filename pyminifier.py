#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Meta
__version__ = '1.1'
__license__ = "GNU General Public License (GPL) Version 3"
__version_info__ = (1, 1)
__author__ = 'James Pond <nlog2n@outlook.com>'

import os, sys, re
from pyparsing import QuotedString, Suppress, Keyword, Optional, Word, Literal, ZeroOrMore, alphanums, restOfLine, replaceWith, pythonStyleComment, printables

"""
Python Minifier:  Reduces the size of Python code for use on embedded platforms.

Performs the following:
    1) Removes docstrings.
    2) Removes comments.
    3) Minimizes code indentation.
    4) Joins multiline pairs of parentheses, braces, and brackets (and removes extraneous whitespace within).
    5) Preserves shebangs and encoding info (e.g. "# -- coding: utf-8 --").
"""

# Compile our regular expressions for speed
multiline_quoted_string_regex = re.compile(r'(\'\'\'|\"\"\")')
not_quoted_string_regex = re.compile(r'(\".*\'\'\'.*\"|\'.*\"\"\".*\')')
double_quoted_string_regex = re.compile(r'((?<!\\)".*?(?<!\\)")')
single_quoted_string_regex = re.compile(r"((?<!\\)'.*?(?<!\\)')")
whitespace = re.compile('\s*')
trailing_newlines = re.compile(r'\n\n')
shebang = re.compile('^#\!.*$')
encoding = re.compile(".*coding[:=]\s*([-\w.]+)")
comment = re.compile("(?!(\'|\")*#.*(\'|\"))\s*#.*")
blank_lines = re.compile("\n\s*\n")
#parens = re.compile("\((?P<parens>[^()]|\(\))*\)", re.MULTILINE|re.DOTALL)
multiline_indicator = re.compile('\\\\(\s*#.*)?\n') # Also removes trailing comments: "test = 'blah \ # comment here"
# Operators (for future use)
#commas = re.compile("(?!\'.*\')\s*\,\s*\n*\s*") # To be replaced with ","
#plus_signs = re.compile("(?!\'.*\')\s*\+\s*\n*\s*") # To be replaced with "+"
#minus_signs = re.compile("(?!\'.*\')\s*\-\s*\n*\s*") # To be replaced with "-"
#multiply_signs = re.compile("(?!\'.*\')\s*\*\s*\n*\s*") # To be replaced with "*"
#divide_signs = re.compile("(?!\'.*\')\s*\/\s*\n*\s*") # To be replaced with "/"
#less_signs = re.compile("(?!\'.*\')\s*\<\s*\n*\s*") # To be replaced with "<"
#greater_signs = re.compile("(?!\'.*\')\s*\>\s*\n*\s*") # To be replaced with ">"
#equal_signs = re.compile("(?!\'.*\')\s*\s*\=\s*\n*\s*") # To be replaced with "="
#equals_signs = re.compile("(?!\'.*\')\s*\=\=\s*\n*\s*") # To be replaced with "=="
#not_equal_signs = re.compile("(?!\'.*\')\s*\!\=\s*\n*\s*") # To be replaced with "!="
#add_assign = re.compile("(?!\'.*\')\s*\+\=\s*\n*\s*") # To be replaced with "+="
#sub_assign = re.compile("(?!\'.*\')\s*\-\=\s*\n*\s*") # To be replaced with "-="
#modulus_assign = re.compile("(?!\'.*\')\s*\%\=\s*\n*\s*") # To be replaced with "%="
#multiply_assign = re.compile("(?!\'.*\')\s*\*\=\s*\n*\s*") # To be replaced with "*="
#powers_assign = re.compile("(?!\'.*\')\s*\*\*\=\s*\n*\s*") # To be replaced with "**="
#divide_assign = re.compile("(?!\'.*\')\s*\/\=\s*\n*\s*") # To be replaced with "/="
#truncate_divide_assign = re.compile("(?!\'.*\')\s*\/\/\=\s*\n*\s*") # To be replaced with "*//="
#truncated_divide_signs = re.compile("(?!\'.*\')\s*\/\/\s*\n*\s*") # To be replaced with "//"
#powers_signs = re.compile("(?!\'.*\')\s*\*\*\s*\n*\s*") # To be replaced with "**"
#left_shift_signs = re.compile("(?!\'.*\')\s*\<\<\s*\n*\s*") # To be replaced with "<<"
#right_shift_signs = re.compile("(?!\'.*\')\s*\*>\>\s*\n*\s*") # To be replaced with ">>"
#modulos_signs = re.compile("(?!\'.*\')\s*\%\s*\n*\s*") # To be replaced with "%"
#and_signs = re.compile("(?!\'.*\')\s*\&\s*\n*\s*") # To be replaced with "&"
#or_signs = re.compile("(?!\'.*\')\s*\|\s*\n*\s*") # To be replaced with "|"
#xor_signs = re.compile("(?!\'.*\')\s*\^\s*\n*\s*") # To be replaced with "^"
#negation_signs = re.compile("(?!\'.*\')\s*\~\s*\n*\s*") # To be replaced with "~"

def substitute_matches(matchlist, opener_regex, closer_regex, opener_sub, closer_sub):
    """Replaces 'opener' and 'closer' in 'matchlist' with 'opener_sub' and 'closer_sub'"""
    preoutput = ""
    for item in matchlist:
        if item:
            if item[0] == '"':
                # Sub out all the matching pairs with something so they don't match later on (we'll change them back at the end)
                item = opener_regex.sub('%s' % opener_sub, item)
                item = closer_regex.sub('%s' % closer_sub, item)
                preoutput += item
            else:
                preoutput += item
    line = "".join(preoutput)
    return line

def join_multiline_pairs(text, pair="()"):
    """Finds and removes newlines in multiline matching pairs of characters in 'text'.
    For example, "(.*\n.*), {.*\n.*}, or [.*\n.*]").
    By default it joins parens () but it will join any two characters it is passed in the 'pair' variable.
    """
    # Readability variables
    opener = pair[0]
    closer = pair[1]

    # Tracking variables
    inside_pair = False
    inside_quotes = False
    inside_double_quotes = False
    inside_single_quotes = False
    quoted_string = False
    openers = 0
    closers = 0
    linecount = 0

    # Static variables
    opener_sub = '###OPENER###'
    closer_sub = '###CLOSER###'

    # Regular expressions
    opener_regex = re.compile('\%s' % opener)
    closer_regex = re.compile('\%s' % closer)
    opener_sub_regex = re.compile('(?!(\'|\"))%s(?!(\'|\"))' % opener_sub)
    closer_sub_regex = re.compile('(?!(\'|\"))%s(?!(\'|\"))' % closer_sub)

    output = ""

    for line in text.split('\n'):
        escaped = False
        multline_match = multiline_quoted_string_regex.search(line)
        not_quoted_string_match = not_quoted_string_regex.search(line)
        if multline_match and not not_quoted_string_match and not quoted_string:
            output += line + '\n'
            quoted_string = True
        elif quoted_string and multiline_quoted_string_regex.search(line) and not quoted_string:
            output += line + '\n'
            quoted_string = False
        elif opener_regex.search(line) or closer_regex.search(line) or inside_pair:
            for character in line:
                if character == opener:
                    if not escaped:
                        openers += 1
                        inside_pair = True
                        output += character
                    else:
                        escaped = False
                        output += character
                elif character == closer:
                    if not escaped:
                        if openers == (closers + 1) and openers != 0:
                            closers = 0
                            openers = 0
                            inside_pair = False
                            output += character
                        else:
                            closers += 1
                            output += character
                    else:
                        escaped = False
                        output += character
                elif character == '\\':
                    if escaped:
                        escaped = False
                        output += character
                    else:
                        escaped = True
                        output += character
                elif character == '"' and escaped:
                    output += character
                    escaped = False
                elif character == "'" and escaped:
                    output += character
                    escaped = False
                elif character == '"' and inside_quotes:
                    if inside_single_quotes:
                        output += character
                    else:
                        inside_quotes = False
                        inside_double_quotes = False
                        output += character
                elif character == "'" and inside_quotes:
                    if inside_double_quotes:
                        output += character
                    else:
                        inside_quotes = False
                        inside_single_quotes = False
                        output += character
                elif character == '"' and not inside_quotes:
                    inside_quotes = True
                    inside_double_quotes = True
                    output += character
                elif character == "'" and not inside_quotes:
                    inside_quotes = True
                    inside_single_quotes = True
                    output += character
                elif character == ' ' and inside_pair and not inside_quotes:
                    pass
                else:
                    if escaped:
                        escaped = False
                    output += character
            if inside_pair == False:
                output += '\n'
        else:
            output += line + '\n'

    # Clean up
    output = opener_sub_regex.sub('%s' % opener, output)
    output = closer_sub_regex.sub('%s' % closer, output)
    output = trailing_newlines.sub('\n', output)

    return output

def dedent(source):
    """Minimizes indentation to save precious bytes"""
    indentation_list = []
    output = ""
    # First find all the levels of indentation
    for line in source.split('\n'):
        indentation_level = len(line.rstrip()) - len(line.strip())
        if indentation_level not in indentation_list:
            indentation_list.append(indentation_level)
    # Now we can reduce each line's indentation to the minimal value
    for line in source.split('\n'):
        indentation_level = len(line.rstrip()) - len(line.strip())
        for i,v in enumerate(indentation_list):
            if indentation_level == v:
                output += " " * i + line.lstrip() + "\n"
    return output

    #def reduce_operators(source):
    #"""Removes spaces and newlines between operators"""
    source = multiline_indicator.sub('', source)

    # The following is meant to remove space between operators but it currently has issues (working on it).
    #source = commas.sub(',', source)
    #source = plus_signs.sub('+', source)
    #source = minus_signs.sub('-', source)
    #source = multiply_signs.sub('*', source)
    #source = divide_signs.sub('/', source)
    #source = less_signs.sub('<', source)
    #source = greater_signs.sub('>', source)
    #source = equal_signs.sub('=', source)
    #source = equals_signs.sub('==', source)
    #source = not_equal_signs.sub('<!=', source)
    #source = add_assign.sub('+=', source)
    #source = sub_assign.sub('-=', source)
    #source = modulus_assign.sub('%=', source)
    #source = multiply_assign.sub('*=', source)
    #source = powers_assign.sub('**=', source)
    #source = divide_assign.sub('/=', source)
    #source = truncate_divide_assign.sub('//=', source)
    #source = truncated_divide_signs.sub('//', source)
    #source = powers_signs.sub('**', source)
    #source = left_shift_signs.sub('<<', source)
    #source = right_shift_signs.sub('>>', source)
    #source = modulos_signs.sub('%', source)
    #source = and_signs.sub('&', source)
    #source = or_signs.sub('|', source)
    #source = xor_signs.sub('^', source)
    #source = negation_signs.sub('~', source)
    #return source

def empty_method():
    """Just a test method.  This should be replaced with 'def empty_method: pass'"""

def fix_empty_methods(source):
    """Appends 'pass' to empty methods/functions (i.e. where there was nothing but a docstring before we removed docstrings =)"""
    def_indentation_level = 0
    output = ""
    just_matched = False
    previous_line = None
    method = re.compile(r'^\s*def\s*.*\(.*\):.*$')
    for line in source.split('\n'):
        if len(line.strip()) > 0: # Don't look at blank lines
            if just_matched == True:
                this_indentation_level = len(line.rstrip()) - len(line.strip())
                if def_indentation_level == this_indentation_level:
                    # This method is empty, insert a 'pass' statement
                    output += "%s pass\n%s\n" % (previous_line, line)
                else:
                    output += "%s\n%s\n" % (previous_line, line)
                just_matched = False
            elif method.match(line):
                def_indentation_level = len(line) - len(line.strip())
                just_matched = True
                previous_line = line
            else:
                output += "%s\n" % line
        else:
            output += "\n"
    return output

def remove_docstrings(source):
    """Removes docstrings from the source"""
    method = (
        Suppress(Keyword("def") +
        Word(alphanums+"_") +
        '(' + ZeroOrMore(Word(alphanums+"_")) + ')' + ":")
    )
    doc = Keyword("__doc__")
    
    # This removes multiline docstrings
    string = ( 
        (QuotedString(quoteChar='\"\"\"', escChar='\\', multiline=True) | \
        QuotedString(quoteChar="\'\'\'", escChar='\\', multiline=True))
    )
    multiLineDocstring = (Optional(doc + Literal('=') + Optional('\\')) + string)
    multiLineDocstring.setParseAction(replaceWith(""))
    source = multiLineDocstring.transformString(source)

    # This removes single line docstrings
    singleLineDocstring = (
        Suppress(method) +
        (QuotedString(quoteChar='"', escChar='\\', multiline=False) | \
        QuotedString(quoteChar="'", escChar='\\', multiline=False))
    )
    singleLineDocstring.setParseAction(replaceWith(""))

    return singleLineDocstring.transformString(source)

def minify(source):
    """Remove all docstrings, comments, blank lines, and minimize code indentation from 'source' (string)."""
    preserved_shebang = None
    preserved_encoding = None

    source = remove_docstrings(source)

    # This loop is for things that must be preserved precisely
    for line in source.split('\n')[0:2]:
        # Save the first comment line if it starts with a shebang (#!) so we can re-add it later
        if shebang.match(line):
            preserved_shebang = line

        # Save the encoding string so we can re-add it later
        if encoding.match(line):
            preserved_encoding = line

    # Remove comments
    source = comment.sub('', source)

    # TODO: This currently isn't working for some reason
    #       probably due to escape character detection in join_multiline_pairs()
    # Remove multilines (e.g. lines that end with '\' followed by a newline)
    source = multiline_indicator.sub('', source)

    # Join multiline pairs of parens, brackets, and braces
    source = join_multiline_pairs(source)
    #source = join_multiline_pairs(source, '[]')
    #source = join_multiline_pairs(source, '{}')

    # Re-add preseved items
    if preserved_encoding:
        source = preserved_encoding + "\n" + source
    if preserved_shebang:
        source = preserved_shebang + "\n" + source

    # Minimize indentation
    source = dedent(source)

    # Remove empty (i.e. single line) methods/functions
    source = fix_empty_methods(source)

    # Remove blank lines
    source = blank_lines.sub('\n', source)

    return source

def main():
    if len(sys.argv) > 1:
        source = open(sys.argv[1]).read()
        print minify(source)
    else:
        print "Usage: pyminifier.py <python source file>"

if __name__ == "__main__":
    main()