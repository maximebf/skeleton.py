# skeleton.py

Create directory structures out of templates

    pip install skeleton

## Usage

skeleton.py comes with a command line utility called *skeleton*.
skeleton.py templates are python packages. The tool will automatically
add the current dir in `sys.path`.

It takes as argument a list of template packages and a target path.
Some templates may need parameters. All environment variables starting
with *SKEL* will be used as parameters.

Very simple usage:

    $ skeleton mypkg.template .

With parameters:

    $ SKELMODULE=test skeleton flaskskel.base .

With multiple templates:

    $ SKELMODULE=test skeleton flaskskel.base flaskskel.assets .

## Templates

A template is a python package (without the *__init__.py*) which files
will be copied to the target path. Some processing is done during the copying.

### Parameters

Parameters can be used in filenames or inside files. They must start
with *SKEL* and be in upper case (alphanumerics and underscores only).

Example:

    mymodule/
        SKELMODULE/
            __init__.py
            utils.py
        run.sh

Generating the skeleton:

    $ SKELMODULE=foo skeleton mymodule .

Will generate:

    foo/
        __init__.py
        utils.py
    run.sh

## Merging files

Multiple templates can be used at the same time thus some merging may
be necessary.

The default operation is to overwrite a file. A different merge operation
can be specified in upper case before the extension. The operation name
to append is *__APPEND__* and to prepend is *__PREPEND__*.

    mymodule/
        SKELMODULE/
            __init__.__APPEND__.py

Note that python imports will be move to the top of the file. If this is not
the desired outcome, add a blank line as the first line.

Files can also contains placeholders, called blocks, to have contact
inserted at a specific position. Note that these placeholders will be removed
from files where generated. Thus it is impossible to later merge a file inside
a generated skeleton if it relies on that method.

To define a block, use *SKELBLOCK_{NAME}* inside your file. The name of the
block can then be used as the merge operation in the filename.

In *mymodule* template's *__init__.py*:

    from flask import Flask
    app = Flask(__name__)
    SKELBLOCK_INIT
    app.run()

Our second template:

    myothermodule/
        SKELMODULE/
            __init__.INIT.py
