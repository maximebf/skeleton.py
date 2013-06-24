import os
import re
import sys
import json


def create(skel_modules, target_path, params=None):
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    if isinstance(skel_modules, str):
        skel_modules = [skel_modules]

    skel = Skeleton(skel_modules.pop(0), params)
    for skel_module in skel_modules:
        skel.add_extension(Skeleton(skel_module))

    skel.apply_to(target_path)


def replace_vars(content, vars):
    for k, v in vars.items():
        content = content.replace(k, v)
    return content


def clean_skel_vars(content):
    return re.sub(r'SKEL[A-Z0-9_]+\n?', '', content)


def clean_skel_vars_in_file(filename):
    with open(filename, 'r') as f:
        content = clean_skel_vars(f.read())
    with open(filename, 'w') as f:
        f.write(content)


def clean_skel_vars_in_dir(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            if f == '.skelvars':
                continue
            clean_skel_vars_in_file(os.path.join(root, f))


def load_skelvars(path):
    filename = os.path.join(path, ".skelvars")
    if os.path.exists(filename):
        with open(filename) as f:
            params = json.load(f)
        return dict([(str(k), str(v)) for k, v in params.iteritems()])
    else:
        return {}


def splitmergemethod(filename):
    (path, name) = os.path.split(filename)
    merge_method = None
    if re.match(r"(.+)\.[A-Z_]+\.[a-z]+", name):
        (name, ext) = os.path.splitext(name)
        (name, merge_method) = os.path.splitext(name)
        merge_method = merge_method.strip('.')
        filename = os.path.join(path, name + ext)
    return (filename, merge_method)


def extract_imports(content):
    lines = content.split("\n")
    end = False
    imports = set()
    final = []
    if lines[0] == "":
        del lines[0]
        final = lines
    else:
        for l in lines:
            if not end and l != "" and not re.match(r"(from (.+) )?import (.+)$", l):
                end = True
                final.append(l)
            elif not end and l!= "":
                imports.add(l)
            elif end:
                final.append(l)
    return ("\n".join(final), imports)


def merge_imports(content, imports):
    lines = content.split("\n")
    current_imports = set()
    end = False
    final = []
    for l in lines:
        if not end:
            if re.match(r"(from (.+) )?import (.+)$", l):
                current_imports.add(l)
            elif l == "" or l.startswith('#'):
                final.append(l)
            else:
                end = True
                current_imports.update(imports)
                final.extend(current_imports)
                final.append(l)
        else:
            final.append(l)
    return "\n".join(final)


class Skeleton(object):
    def __init__(self, module, params=None):
        self.module = module
        self.params = params or {}
        self.extensions = []
        self.added_objects = []

        self.path = None
        modulepath = module.replace('.', '/')
        for p in sys.path:
            fullpath = os.path.join(p, modulepath)
            if os.path.exists(fullpath):
                self.path = fullpath
                break

        if self.path is None:
            raise Exception("Module '%s' not found in sys.path" % module)

    def apply_to(self, path):
        params = load_skelvars(path)
        params.update(self.params)
        self.params = params

        self._merge_objects(path)

        for skel in self.extensions:
            skel.params = self.params
            skel._merge_objects(path)

        clean_skel_vars_in_dir(path)

    def _merge_objects(self, path):
        objects = self.objects
        for o in objects:
            if not o.is_valid(path):
                raise Exception("Skeleton cannot be merged!")
        for o in objects:
            o.merge(path)


    def add_extension(self, skel):
        self.extensions.append(skel)

    def has_extension(self, skelname):
        for s in self.extensions:
            if s.__class__.__name__ == skelname:
                return True
        return False

    def add_object(self, o):
        self.added_objects.append(o)

    @property
    def objects(self):
        objects = []
        self._walk(self.path, objects, '')
        objects.extend(self.added_objects)
        return objects

    def _walk(self, root, objects, relative_path=''):
        for filename in os.listdir(root):
            if relative_path == '' and filename in ('__init__.py', '__init__.pyc'):
                continue
            filepath = os.path.join(root, filename)
            relname = os.path.join(relative_path, filename)
            if os.path.isdir(filepath):
                objects.append(SkeletonDir(self.path, relname, self.params))
                self._walk(filepath, objects, relname)
            else:
                objects.append(SkeletonFile(self.path, relname, self.params))


class SkeletonObject(object):
    def __init__(self, root, filename, params=None):
        self.root = root
        self.filename = filename
        self.params = params or {}

    @property
    def target_filename(self):
        return replace_vars(self.filename, self.params)


class SkeletonDir(SkeletonObject):
    def is_valid(self, path):
        target_filepath = os.path.join(path, self.target_filename)
        if os.path.exists(target_filepath) and not os.path.isdir(target_filepath):
            return False
        return True

    def has_effect(self, path):
        target_filepath = os.path.join(path, self.target_filename)
        return not os.path.exists(target_filepath)

    def merge(self, path):
        target_filepath = os.path.join(path, self.target_filename)
        if not os.path.exists(target_filepath):
            os.mkdir(target_filepath)


class SkeletonFile(SkeletonObject):
    def __init__(self, root, filename, params=None):
        (self.filename_no_block, self.merge_method) = splitmergemethod(filename)
        super(SkeletonFile, self).__init__(root, filename, params)

    @property
    def target_filename(self):
        return replace_vars(self.filename_no_block, self.params)

    def open(self, mode='r'):
        return open(os.path.join(self.root, self.filename), mode)

    def process(self):
        with self.open() as f:
            content = f.read()
        content = replace_vars(content, self.params)
        return content

    def save(self, path):
        with open(os.path.join(path, self.target_filename), 'w') as f:
            f.write(self.process())

    def is_valid(self, path):
        target_filepath = os.path.join(path, self.target_filename)
        if os.path.isdir(target_filepath):
            return False
        return True

    def has_effect(self, path):
        return True

    def merge(self, path):
        target_filepath = os.path.join(path, self.target_filename)

        if not os.path.exists(target_filepath) or self.merge_method == None:
            self.save(path)
            return

        with open(target_filepath) as f:
            target_content = f.read()

        if target_filepath.endswith('.py'):
            (content, imports) = extract_imports(self.process())
        else:
            content = self.process()
            imports = None

        if self.merge_method == '__APPEND__':
            target_content += "\n" + content
        elif self.merge_method == '__PREPEND__':
            target_content = content + "\n" + target_content
        else:
            varname = 'SKELBLOCK_%s' % self.merge_method
            content += "\n" + varname
            target_content = replace_vars(target_content, {varname: content})

        if imports is not None:
            target_content = merge_imports(target_content, imports)

        with open(target_filepath, 'w') as f:
            f.write(target_content)
