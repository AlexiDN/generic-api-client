from types import SimpleNamespace
from typing import Any, Literal
from collections.abc import Callable
from pydantic import BaseModel, Field


class BaseConfig(BaseModel):
    model_variables: dict[str, Any] = Field(
        default={},
        description="The variables shared accross the model and its submodels. \
            This is accessible using '{config.key_to_access}'",
    )
    _config: dict[str, Any] = None
    _interpolate: bool = True

    def __init__(self, *args: tuple, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        self._propagate_model_variables()

    def model_dump(
        self,
        *,
        mode: str | Literal["json", "python"] = "python",
        include: Any | None = None,
        exclude: Any | None = None,
        context: dict | None = None,
        by_alias: Any | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        fallback: Callable | None = None,
        serialize_as_any: bool = False,
        interpolate: bool = True,
    ) -> dict[str, Any]:
        """Generate a dictionary representation of the model,
        optionally specifying which fields to include or exclude.
        """
        if isinstance(context, dict):
            interpolate = interpolate or context.get("interpolate", False)
            context["interpolate"] = interpolate
        if not context:
            context = {"interpolate": interpolate}

        data = super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )
        if interpolate:
            return BaseConfig._recursive_interpolate(data, SimpleNamespace(**self._config))
        return data

    def set_store_config(self, config: BaseModel) -> None:
        """Set the _config variable using the store config object.
        Apply it recursively to the model fields
        Note that only lists and dicts iterables are checked
        """
        # set or update self._config with the config_model
        if not self._config:
            self._config = config.model_dump(mode="json")
        else:
            # Interpolate self_config with the store config before merging everything
            interpolated_config = BaseConfig._recursive_interpolate(
                self._config, SimpleNamespace(**config.model_dump(mode="json"))
            )
            # do not use .update since config does not have priority over model_variables
            self._config = {**config.model_dump(mode="json"), **interpolated_config}
        # propagate to model fields
        for attr in vars(self).values():
            self._recursive_call_method_on_fields(attr, "set_store_config", config)

    def change_interpolation(self, interpolate: bool) -> None:
        """Set the _interpolate variable using the boolean given.
        Apply it recursively to the model fields
        Note that only lists and dicts iterables are checked
        """
        self._interpolate = interpolate
        for attr in vars(self).values():
            self._recursive_call_method_on_fields(attr, "change_interpolation", interpolate)

    def _propagate_model_variables(self, parent_model_variables: dict[str, Any] | None = None) -> None:
        """Propagate model_variables to self._config for model and submodels"""
        parent_model_variables = parent_model_variables or {}
        # model_variables are top priority then parent ones then _config
        base_config = {**(self._config or {}), **parent_model_variables}
        # try to interpolate variables that can be interpolated
        interpolated_model_variables = BaseConfig._recursive_interpolate(
            self.model_variables, SimpleNamespace(**base_config)
        )
        self._config = {
            **(self._config or {}),
            **parent_model_variables,
            **interpolated_model_variables,
        }
        # propagate to model fields
        for attr in vars(self).values():
            self._recursive_call_method_on_fields(attr, "_propagate_model_variables", self._config)

    @staticmethod
    def _recursive_call_method_on_fields(obj: Any, method_name: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        """Recursively call method on fields with the args and kwargs given.
        Only lists and dicts iterables are checked
        """
        if isinstance(obj, BaseConfig):
            method: Callable = getattr(obj, method_name)
            method(*args, **kwargs)
        elif isinstance(obj, list):
            for elem in obj:
                BaseConfig._recursive_call_method_on_fields(elem, method_name, *args, **kwargs)
        elif isinstance(obj, dict):
            for v in obj.values():
                BaseConfig._recursive_call_method_on_fields(v, method_name, *args, **kwargs)

    def __getattribute__(self, name: str) -> Any:
        """Return the attribute requested after interpolating it with  self._config"""
        res = super().__getattribute__(name)
        if (
            not name.startswith("_")  # exclude private attributes
            and name in self.__pydantic_fields__  # select only fields
            and self.__pydantic_private__.get("_interpolate")  # is interpolation active
            and self.__pydantic_private__.get("_config")  # is _config set
            and name != "model_variables"  # prevent double interpolation
        ):
            return BaseConfig._recursive_interpolate(res, SimpleNamespace(**self._config))
        return res

    @staticmethod
    def _recursive_interpolate(data: Any, config: SimpleNamespace) -> Any:
        """Recursively interpolate strings with a config object"""
        # case dict
        if isinstance(data, dict):
            return {k: BaseConfig._recursive_interpolate(v, config) for k, v in data.items()}
        # case list/tuple
        if isinstance(data, list):
            return [BaseConfig._recursive_interpolate(v, config) for v in data]
        # ensure data is string
        if isinstance(data, str) and "{config" in data:
            try:
                return data.format(config=config)
            except Exception:
                return data
        return data
