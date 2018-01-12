import inspect
import sys
import os
import time


def get_id():
    id = 0
    while True:
        yield id
        id += 1


get_id = get_id()  # initialize the generator


class Node:
    def __init__(self, frame_hash, parent_frame, frame):
        self.frame_hash = frame_hash
        self.parent = parent_frame
        self.frame = frame
        self.children = []
        self.calls = []
        self.func_args = dict(self.frame.f_locals)  # dict freezes it just after function call, before any other local variables can be created!
        self.start_time = None
        self.elapsed_time = None
        self.id = next(get_id)

    def __hash__(self):
        return self.frame_hash

    def s(self):
        pre = ''
        if 'self' in self.func_args:
            pre = self.func_args['self'].__class__.__name__ + '.'
        elif 'cls' in self.func_args:
            pre = self.func_args['cls'].__name__ + '.'

        args = ', '.join(
            fr'{arg} = {repr(val)}'.replace('\n', '')
            for arg, val
            in reversed(tuple(self.func_args.items()))
            if arg not in ('cls',)
        )

        own_time = self.elapsed_time - sum(child.elapsed_time for child in self.children)

        return fr'{pre}{get_function_name(self.frame)}({args}) | {self.elapsed_time:6f} s | {own_time:6f} s'

    def html(self):
        pre = ''
        if 'self' in self.func_args:
            pre = self.func_args['self'].__class__.__name__ + '.'
        elif 'cls' in self.func_args:
            pre = self.func_args['cls'].__name__ + '.'

        args = 'Arguments: ' + ', '.join(
            fr'{arg} = {repr(val)}'.replace('\n', '')
            for arg, val
            in reversed(tuple(self.func_args.items()))
            if arg not in ('self', 'cls')
        ).replace('"', '&quot;').replace("'", '&apos;').replace('<', '&lt;').replace('>', '&gt;')

        postfix = ''
        if 'self' in self.func_args:
            postfix += f'(self = {repr(self.func_args["self"])})'

        own_time = self.elapsed_time - sum(child.elapsed_time for child in self.children)
        time_str = f'Elapsed: {self.elapsed_time:6f} s | Own: {own_time:6f} s'

        inner = f'{pre}{get_function_name(self.frame)}{postfix}'.replace('<', '&lt;').replace('>', '&gt;')
        return fr'<span title = "{time_str}&#013;{args}">{inner}</span>'

    def report(self):
        lines = self._lines()
        lines = self._cleanup(lines)
        return '\n'.join(lines)

    def report_html(self, depth = 0):
        lines = self._lines_html(depth = depth)
        lines = self._cleanup(lines)
        return '\n'.join(lines)

    def _lines(self):
        lines = []
        for child, report in ((child, child.report()) for child in self.children):
            lines.append(f'├─ {child.s()}')
            if report != '':
                lines.extend(f'│  {line}' for line in report.split('\n'))

        return lines

    # https://codepen.io/anchen/pen/rGDjI
    def _lines_html(self, depth = 0):
        lines = []
        for child, report in ((child, child.report_html(depth = depth + 1)) for child in self.children):
            if report != '':
                lines.append(f'<li>')
                lines.append(f'  <label for={self.id}>{child.html()}</label>')
                lines.append(f'  <input type="checkbox" id={self.id}/>')
                lines.append(f'  <ol>')
                lines.extend(f'  {line}' for line in report.split('\n'))
                lines.append(f'  </ol>')
                lines.append(f'</li>')
            else:
                lines.append(f'<li class="file"> {child.html()}</li>')

        lines = ['  ' + line for line in lines]
        return lines

    def _cleanup(self, lines):
        for index, line in reversed(list(enumerate(lines))):
            # print(line)
            if line[0] == '├':  # this is the last branch on this level, replace it with endcap and break
                lines[index] = line.replace('├', '└')
                break
            else:  # not yet at last branch, continue cleanup
                lines[index] = line.replace('│', ' ', 1)
        # print()
        return lines


def get_parent_frame(frame):
    return frame.f_back


def get_function_name(frame):
    return frame.f_code.co_name


def get_file_name(frame):
    return os.path.basename(frame.f_code.co_filename)


class TraceFunction:
    def __init__(self, tracer, ignored_funcnames = (), ignored_filenames = (), timing_func = time.perf_counter):
        self.tracer = tracer
        self.ignored_funcnames = ignored_funcnames
        self.ignored_filenames = ('hephaestus.py',) + ignored_filenames
        self.timing_func = timing_func

    def __call__(self, frame, event, arg):
        if get_function_name(frame) in self.ignored_funcnames:
            return
        if get_file_name(frame) in self.ignored_filenames:
            return

        if event == 'call':
            parent = frame.f_back

            try:
                node = self.tracer.frame_hash_to_node[hash(frame)]
            except KeyError:
                node = Node(hash(frame), parent, frame)
                self.tracer.frame_hash_to_node[hash(frame)] = node

            self.tracer.frame_hash_to_node[hash(parent)].children.append(node)

            node.start_time = self.timing_func()

        if event == 'return':
            node = self.tracer.frame_hash_to_node[hash(frame)]
            node.elapsed_time = self.timing_func() - node.start_time


class Tracer:
    def __init__(self):
        self.frame_hash_to_node = {}

    def __enter__(self):
        parent = get_parent_frame(inspect.currentframe())

        sys.setprofile(TraceFunction(self))

        self.root_node = Node(hash(parent), get_parent_frame(parent), parent)
        self.frame_hash_to_node[hash(parent)] = self.root_node

        return self

    start = __enter__

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def stop(self):
        sys.setprofile(None)

    def get_report_lines(self):
        proto_report = self.root_node.report()

        # make sure we've got a solid line on far left
        rep_lines = ['│' + line[1:] for line in proto_report.split('\n')]
        num_lines = len(str(len(rep_lines)))
        rep_lines = [f'{str(n).rjust(num_lines, "0")} {line}' for n, line in enumerate(rep_lines)]

        return rep_lines

    def get_report_lines_html(self):
        proto_report = self.root_node.report_html()

        # make sure we've got a solid line on far left
        rep_lines = ['│' + line[1:] for line in proto_report.split('\n')]
        num_lines = len(str(len(rep_lines)))
        rep_lines = [f'{str(n).rjust(num_lines, "0")} {line}' for n, line in enumerate(rep_lines)]

        return rep_lines

    def report(self):
        rep_lines = self.get_report_lines()
        num_lines = len(str(len(rep_lines)))

        rep = '\n'.join((
            ' ' * (num_lines + 1) + '┌─<START>',
            *rep_lines,
            ' ' * (num_lines + 1) + '└─<END>',
        ))

        return rep

    def report_html(self):
        body = self.root_node.report_html()
        # rep = rep.replace(' ', '&ensp;')
        # rep = rep.replace('\n', '<br>')
        # rep = '<body>\n<h1>Hephaestus Report</h1>\n<ol class="tree">\n' + rep + '\n</ol>\n</body>'

        # rep = HEADER + STYLE + SCRIPT + rep + FOOTER
        rep = '\n'.join((
            HEADER,
            STYLE,
            SCRIPT,
            '<body>',
            '<h1>Hephaestus Report</h1><br>',
            '<ol class="tree">',
            body,
            '</ol>',
            '</body>',
            FOOTER,
        ))

        # rep = rep.replace(' ', '&nbsp;')

        return rep


HEADER = """
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Hephaestus Report</title>
"""

STYLE = """
<style type="text/css">
* {
  margin: 0;
  padding: 0;
  white-space: nowrap;
}
body {
  padding-top: 20px;
  padding-left: 20px;
  font-size: 100%;
  font-family: "Courier New", Courier, monospace;
}
input {
  font-size: 1em;
}
ol.tree {
  padding-left: 20px;
}
li {
  list-style-type: none;
  position: relative;
  margin-left: -15px;
}
li label {
  padding-left: 20px;
  cursor: pointer;
  display: block;
}
li input {
  width: 1em;
  height: 1em;
  position: absolute;
  left: -0.5em;
  top: 0;
  opacity: 0;
  cursor: pointer;
}
li input + ol {
  height: 1em;
  margin: -16px 0 0 -44px;
  background: url("https://www.thecssninja.com/demo/css_tree/toggle-small-expand.png")
    no-repeat 40px 0;
}
li input + ol > li {
  display: none;
  margin-left: -14px !important;
  padding-left: 1px;
}
li.file {
  padding-left: 20px;
}
li input:checked + ol {
  height: auto;
  margin: -21px 0 0 -44px;
  padding: 25px 0 0 80px;
  background: url("https://www.thecssninja.com/demo/css_tree/toggle-small.png")
    no-repeat 40px 5px;
}
li input:checked + ol > li {
  display: block;
  margin: 0 0 0.063em;
}
li input:checked + ol > li:first-child {
  margin: 0 0 0.125em;
}

</style>
"""

SCRIPT = """
<script>
    function toggle(element) {
        var children = element.children;
        var child;
        for (i = 1; i < children.length; i++) {
            child = children[i];
            if (child.style.display != 'inline') {
                child.style.display = 'inline';
            } else {
                child.style.display = 'none';
            }
        }
    }
</script>
"""

FOOTER = """
</html>
"""
