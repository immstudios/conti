class FBaseFilter(object):
    arg_names = []

    def __init__(self, *args, **kwargs):
        assert len(args) == len(self.arg_names), \
            f"Expected arguments: {', '.join(self.arg_names)}"
        self.args = {}
        for key, value in zip(self.arg_names, args):
            self.args[key] = value
        self.kwargs = kwargs

    def keys(self):
        return list(self.args.keys()) + ["kwargs"]

    def __getitem__(self, key):
        if key == "kwargs":
            if not self.kwargs:
                return ""
            return ":".join([
                    f"{key}={self.kwargs[key]}"
                    for key in self.kwargs
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
# Filters
#


class RawFilter(FBaseFilter):
    arg_names = ["string"]

    def render(self):
        return self["string"]


class FNull(FBaseFilter):
    arg_names = ["input", "output"]

    def render(self):
        return "[{input}]null[{output}]".format(**self)


class FANull(FBaseFilter):
    arg_names = ["input", "output"]

    def render(self):
        return "[{input}]anull[{output}]".format(**self)


class FApad(FBaseFilter):
    arg_names = ["input", "output"]

    def render(self):
        if self.kwargs:
            return "[{input}]apad={kwargs}[{output}]".format(**self)
        return "[{input}]apad[{output}]".format(**self)


class FAtrim(FBaseFilter):
    arg_names = ["input", "output"]

    def render(self):
        if self.kwargs:
            return "[{input}]atrim={kwargs}[{output}]".format(**self)
        return "[{input}]atrim[{output}]".format(**self)


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
            result += "={kwargs}".format(**self)
        result += "[{output}]".format(**self)
        return result


class FDrawText(FBaseFilter):
    arg_names = ["input", "output"]

    def render(self):
        result = "[{input}]drawtext={kwargs}[{output}]".format(**self)
        return result


class FSetField(FBaseFilter):
    arg_names = ["input", "output", "order"]

    def render(self):
        result = "[{input}]setfielded={order}[{output}]".format(**self)
        return result


class FSplit(FBaseFilter):
    arg_names = ["input", "outputs"]

    def render(self):
        result = "[{}]".format(self["input"])
        result += "split={}".format(len(self["outputs"]))
        result += "".join(["[{}]".format(o) for o in self["outputs"]])
        return result
