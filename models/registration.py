import importlib


class ModelSpec(object):
    """
    Specification for a Model
    """

    def __init__(self, model_id, entry_point=None):
        self.model_id = model_id
        model_name, class_name = entry_point.split(':')
        self._entry_point = getattr(importlib.import_module(model_name), class_name)

    def load(self):
        model = self._entry_point()
        return model


class ModelRegistry(object):
    def __init__(self):
        self.model_specs = {}

    def load(self, model_id):
        return self.model_specs[model_id].load()


model_registry = ModelRegistry()


#
# def register(model_id,entry_point):
#     return

def load(model_id):
    return model_registry.load(model_id)
