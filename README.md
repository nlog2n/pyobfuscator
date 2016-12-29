# pyobfuscator is a source-code level Python obfuscator

    pyfuscate uses the services of the tokenize module in Python and some
    simple rules to decide which names have been assigned by the user (and
    not dictated by, say a third-party module) and mangles them appropriately.
    Everything else gets spat out (essentially) unchanged.

## Usage

Option 1: compyne.py + pyfuscate.py   # combine into one and obfuscate

Option 2: pyminfier.py  # remove python comments

    pyfuscate works pretty much as-is on small, stand-alone programs.  On
    larger works its success relies upon some simple rules being followed:

1. All third-party modules are imported and used with their full names.
       In other words:

>           import os

>           os.access(...)
  
2. No 'from' imports of third-party modules.  In other words, do *not* use:

>           from os import *

>           access(...)
  
3. If your project is split into multiple files, perform *all* imports from
       your own code as 'from' imports.  In other words, *do* use:

>           from mymodule import myfunction

>           myfunction(...)
  
4. Once you are ready to 'pyfuscate' your code, use compyne.py (small
       helper script included with this package) to put all your source files
       together, and then run pyfuscate on the result.  In other words:

>           compyne.py /myproj/lib/* /myproj/main_runtime.py > onefile_output.py

>           pyfuscate.py -f onefile_output.py -o /myproj/pyfuscated_runtime.py




## Background

    With tools such as 'decompyle' available, the 'barrier to entry' involved
    in reverting someones commercial proprietary Python program from bytecode
    back to usable source-code is ridiculously low.  pyfuscate reduces the
    'payoff' involved in doing this, by stripping a program of as much human
    'context' as possible.  In other words, your variable names, function
    names, and class declarations are mangled into a series of generic 'names'
    that no longer reflect the true purpose of the code.

    Every other effort to obfuscate Python source-code is redundant and doomed
    to failure; ridiculous indentation, odd spacing, run-on lines, strings
    converted to chr()s, etc: all of these fail in the face of the tokenizer
    built in to Python itself; I'm sure that there has been more than one
    person (un)pleasantly surprised to find that source-code comes out prettier
    from decompyle than when they first wrote it!  The only aspect of Python
    code that can not be automatically reverted is the context of the naming
    itself.  On large programs, loss of sensible names for variables can be a
    showstopper (as any maintenance programmer can testify), so it makes sense
    to destroy these if possible without mangling the function of the program
    itself.


## Warning

    Because Python is such a rich and wonderful programming language, there are
    certain situations that are extremely difficult to determine if a name is a
    user-assigned one, or is imposed from a third-party module.  Examples of
    this would be when functions are called with key-word arguments (ie
    myfunction(foo='bar'), or when variables are created 'magically', such as
    when one plays games with the locals() or globals() or __dict__ (optparse
    is a good example of this).  For this reason, pyfuscate supplies a method
    of overriding the decision of the algorithm and allowing you to specify
    a list of names that should never be mangled.  In practice, on all but the
    largest of programs, this list should be pretty short, and you'll find the
    exceptions quickly enough (they will turn up in the same situations often
    enough that you'll probably realise beforehand where you are going to run
    into one).  At least the keyword-arguments problem is top of the list for
    the next release (any compiler or Python gurus out there that care to
    help?? :).

    Well, the usual Caveat Emptor applies; pyfuscate has been tested on some
    pretty big programs, but if it eats all the food in your fridge, scribbles
    on your walls, or does anything else you don't like or didn't expect, then
    you're on your own.  To see some example output, pyfuscate successfully
    'pyfuscates' itself with the command-line:

>        ./pyfuscate.py -f pyfuscate.py -o mashed_pyfuscate.py -p "usage options"

