class FBaseFilter(object):
    arg_names = []

    def __init__(self, *args, **kwargs):
        assert len(args) == len(self.arg_names), "Expected arguments: {}".format(", ".join(self.arg_names))
        self.args = {}
        for key, value in zip(self.arg_names, args):
            self.args[key] = value
        self.kwargs = kwargs

    def keys(self):
        return self.args.keys() + ["kwargs"]

    def __getitem__(self, key):
        if key == "kwargs":
            if not self.kwargs:
                return ""
            return ":".join([
                    "{}={}".format(key, self.kwargs[key]) for key in self.kwargs
                ])
        return self.args[key]


class FilterChain(object):
    def __init__(self, *args):
        self.filters = list(args)

    def __len__(self):
        return len(self.filters)

    def add(self, *args):
        for f in args:
            self.filters.append(f)

    def render(self):
        return ";".join([f.render() for f in self.filters])

#
#
#


class FSource(FBaseFilter):
    arg_names = ["path", "output"]
    def render(self):
        result = "movie='{path}'".format(**self)
        if self.kwargs:
            result += ":{kwargs}".format(**self)
        result += "[{output}]".format(**self)
        return result


class FOverlay(FBaseFilter):
    arg_names = ["background", "foreground", "output"]
    def render(self):
        result = "[{background}][{foreground}]overlay".format(**self)
        if self.kwargs:
            resulta += "={kwargs}".format(**self)
        result += "[{output}]".format(**self)
        return result

class FDrawText(FBaseFilter):
    arg_names = ["input", "output"]
    def render(self):
        result = "[{input}]drawtext={kwargs}[{output}]".format(**self)
        return result

