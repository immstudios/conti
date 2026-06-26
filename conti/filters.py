from typing import Any, ClassVar


class FBaseFilter:
    arg_names: ClassVar[list[str]]

    def __init__(self, *args, **kwargs) -> None:
        assert len(args) == len(self.arg_names), (
            f"Expected arguments: {', '.join(self.arg_names)}"
        )
        self.args = {}
        for key, value in zip(self.arg_names, args, strict=False):
            self.args[key] = value
        self.kwargs = kwargs

    def keys(self) -> list[str]:
        return [*list(self.args.keys()), "kwargs"]

    def __getitem__(self, key: str) -> Any:
        if key == "kwargs":
            if not self.kwargs:
                return ""
            return ":".join([f"{key}={self.kwargs[key]}" for key in self.kwargs])
        return self.args[key]


class FilterChain:
    def __init__(self, *args) -> None:
        self.filters = list(args)

    def __len__(self) -> int:
        return len(self.filters)

    def add(self, *args) -> None:
        for f in args:
            self.filters.append(f)

    def render(self) -> str:
        return ";".join(f.render() for f in self.filters)


#
# Filters
#


class RawFilter(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["string"]

    def render(self) -> str:
        return self["string"]


class FNull(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["input", "output"]

    def render(self) -> str:
        return "[{input}]null[{output}]".format(**self)


class FANull(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["input", "output"]

    def render(self) -> str:
        return "[{input}]anull[{output}]".format(**self)


class FApad(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["input", "output"]

    def render(self) -> str:
        if self.kwargs:
            return "[{input}]apad={kwargs}[{output}]".format(**self)
        return "[{input}]apad[{output}]".format(**self)


class FAtrim(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["input", "output"]

    def render(self) -> str:
        if self.kwargs:
            return "[{input}]atrim={kwargs}[{output}]".format(**self)
        return "[{input}]atrim[{output}]".format(**self)


class FSource(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["path", "output"]

    def render(self) -> str:
        result = "movie={path}".format(**self)
        if self.kwargs:
            result += ":{kwargs}".format(**self)
        result += "[{output}]".format(**self)
        return result


class FOverlay(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["background", "foreground", "output"]

    def render(self) -> str:
        result = "[{background}][{foreground}]overlay".format(**self)
        if self.kwargs:
            result += "={kwargs}".format(**self)
        result += "[{output}]".format(**self)
        return result


class FDrawText(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["input", "output"]

    def render(self) -> str:
        return "[{input}]drawtext={kwargs}[{output}]".format(**self)


class FSetField(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["input", "output", "order"]

    def render(self) -> str:
        return "[{input}]setfield={order}[{output}]".format(**self)


class FSplit(FBaseFilter):
    arg_names: ClassVar[list[str]] = ["input", "outputs"]

    def render(self) -> str:
        result = "[{}]".format(self["input"])
        result += "split={}".format(len(self["outputs"]))
        result += "".join([f"[{o}]" for o in self["outputs"]])
        return result
