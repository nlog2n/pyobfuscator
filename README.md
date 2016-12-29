# A source-code level Python obfuscator

With tools such as 'decompyle' one can easily revert Python program from bytecode back to usable source-code. pyfuscate strips a program of as much human 'context' as possible.  In other words, your variable names, function names, and class declarations are mangled into a series of generic 'names' that no longer reflect the true purpose of the code.

pyfuscate uses the services of the tokenize module in Python and some simple rules to decide which names have been assigned by the user (and not dictated by, say a third-party module) and mangles them appropriately. Everything else gets spat out (essentially) unchanged.

## Usage

Option 1: compyne.py + pyfuscate.py   # combine into one and obfuscate

Option 2: pyminfier.py  # remove python comments

 To see some example output, pyfuscate successfully 'pyfuscates' itself with the command-line:

>        ./pyfuscate.py -f pyfuscate.py -o mashed_pyfuscate.py -p "usage options"



pyfuscate works pretty much as-is on small, stand-alone programs.  On larger works its success relies upon some simple rules being followed:

- All third-party modules are imported and used with their full names. In other words:

>           import os
>           os.access(...)
  
- No 'from' imports of third-party modules.  In other words, do *not* use:

>           from os import *
>           access(...)
  
- If your project is split into multiple files, perform *all* imports from your own code as 'from' imports.  In other words, *do* use:

>           from mymodule import myfunction
>           myfunction(...)
  
- Once you are ready to 'pyfuscate' your code, use compyne.py (small helper script included with this package) to put all your source files together, and then run pyfuscate on the result.  In other words:

>           compyne.py /myproj/lib/* /myproj/main_runtime.py > onefile_output.py
>           pyfuscate.py -f onefile_output.py -o /myproj/pyfuscated_runtime.py



## Warning

There are certain situations that are extremely difficult to determine if a name is a user-assigned one, or is imposed from a third-party module.  Examples of this would be when functions are called with key-word arguments (ie myfunction(foo='bar'), or when variables are created 'magically', such as when one plays games with the locals() or globals() or __dict__ (optparse is a good example of this).  For this reason, pyfuscate supplies a method of overriding the decision of the algorithm and allowing you to specify a list of names that should never be mangled.  In practice, on all but the largest of programs, this list should be pretty short, and you'll find the exceptions quickly enough (they will turn up in the same situations often enough that you'll probably realise beforehand where you are going to run into one). At least the keyword-arguments problem is top of the list for the next release.