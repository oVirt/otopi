#
# otopi -- plugable installer
# Copyright (C) 2012-2013 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


"""codegen.py - generate java code out of python.

Usage: codegen.py output_dir package prefix package...

Use util.codegen decoration to mark classes.

"""


import os
import sys


def main():

    target_dir = sys.argv[1]
    prefix = sys.argv[2]

    for module in sys.argv[3:]:
        module = __import__(module, globals(), locals(), -1)

        if '__codegen__' in module.__dict__:
            for clz in module.__dict__['__codegen__']:
                name = '%s.%s' % (
                    prefix,
                    module.__name__,
                )
                file_name = '%s/%s/%s.java' % (
                    target_dir,
                    '/'.join(name.split('.')),
                    clz.__name__
                )
                try:
                    os.makedirs(os.path.dirname(file_name))
                except OSError:
                    pass
                with open(file_name, 'w') as f:
                    f.write(
                        (
                            'package %s;\n'
                            'public class %s {\n'
                        ) % (
                            name,
                            clz.__name__
                        )
                    )
                    for member in clz.__dict__:
                        if not member.startswith('_'):
                            value = clz.__dict__[member]
                            if isinstance(value, int):
                                f.write(
                                    (
                                        '\tpublic static final '
                                        'int %s = %s;\n'
                                    ) % (
                                        member,
                                        value
                                    )
                                )
                            else:
                                f.write(
                                    (
                                        '\tpublic static final '
                                        'String %s = "%s";\n'
                                    ) % (
                                        member,
                                        value
                                    )
                                )
                    f.write('}\n')

if __name__ == '__main__':
    main()


# vim: expandtab tabstop=4 shiftwidth=4
