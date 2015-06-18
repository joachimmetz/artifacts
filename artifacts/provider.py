# -*- coding: utf-8 -*-
"""The provider definition objects.

The provider definition objects define the type of information
an artifact can provide. E.g. on Windows the Registry key:
HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion

provides the value of the environment variable: %SystemRoot%
"""


class ProviderDefinition(object):
  """Class that implements the artifact provider type interface.

  Attributes:
    description: description of the artifact definition.
    name: the name that uniquely identifiers the artifact definition.
    urls: list of URLS with additional information.
  """

  TYPE_INDICATOR = None

  def __init__(self, name, description=None):
    """Initializes the provider type object.

    Args:
      name: the name that uniquely identifiers the provider type.
      description: optional description of the provider type.
                   The default is None.
    """
    super(ProviderDefinition, self).__init__()
    self.description = description
    self.name = name
    self.urls = []

  @property
  def type_indicator(self):
    """The type indicator.

    Raises:
      NotImplementedError: if the type indicator is not defined.
    """
    if not self.TYPE_INDICATOR:
      raise NotImplementedError(
          u'Invalid source type missing type indicator.')
    return self.TYPE_INDICATOR
