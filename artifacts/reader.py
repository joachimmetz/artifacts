# -*- coding: utf-8 -*-
"""The artifact reader objects."""

import abc
import glob
import os

from artifacts import artifact
from artifacts import definitions
from artifacts import errors
from artifacts import provider

import yaml


class ArtifactsReader(object):
  """Class that implements the artifacts reader interface."""

  @abc.abstractmethod
  def ReadFileObject(self, file_object):
    """Reads artifact definitions from a file-like object.

    Args:
      file_object: the file-like object to read from.

    Yields:
      Artifact definitions (instances of ArtifactDefinition).
    """

  @abc.abstractmethod
  def ReadFile(self, filename):
    """Reads artifact definitions from a file.

    Args:
      filename: the name of the file to read from.

    Yields:
      Artifact definitions (instances of ArtifactDefinition).
    """

  @abc.abstractmethod
  def ReadDirectory(self, path, extension=None, ignore_list=None):
    """Reads artifact definitions from a directory.

    This function does not recurse sub directories.

    Args:
      path: the path of the directory to read from.
      extension: optional extension of the filenames to read.
                 The default is None.
      ignore_list: optional list of filenames to ignore. The default is None.

    Yields:
      Artifact definitions (instances of ArtifactDefinition).
    """


class YamlArtifactsReader(ArtifactsReader):
  """Class that implements the YAML artifacts reader."""

  def _ReadArtifactDefinition(self, yaml_definition):
    """Reads an artifact definition.

    Args:
      yaml_definition: the YAML artifact definition.

    Returns:
      An artifact definition (instance of ArtifactDefinition).

    Raises:
      FormatError: if the format of the YAML artifact definition is not set
                   or incorrect.
    """
    if not yaml_definition:
      raise errors.FormatError(u'Missing YAML definition.')

    name = yaml_definition.get(u'name', None)
    if not name:
      raise errors.FormatError(u'Invalid artifact definition missing name.')

    # The description is assumed to be mandatory.
    description = yaml_definition.get(u'doc', None)
    if not description:
      raise errors.FormatError(
          u'Invalid artifact definition: {0:s} missing description.'.format(
              name))

    artifact_definition = artifact.ArtifactDefinition(
        name, description=description)

    if yaml_definition.get(u'collectors', []):
      raise errors.FormatError(
          u'Invalid artifact definition: {0:s} still uses collectors.'.format(
              name))

    for source in yaml_definition.get(u'sources', []):
      type_indicator = source.get(u'type', None)
      if not type_indicator:
        raise errors.FormatError(
            u'Invalid artifact definition: {0:s} source type.'.format(name))

      attributes = source.get(u'attributes', None)
      try:
        source_type = artifact_definition.AppendSource(
            type_indicator, attributes)
      except errors.FormatError as exception:
        raise errors.FormatError(
            u'Invalid artifact definition: {0:s}. {1:s}'.format(
                name, exception))

      # TODO: deprecate these left overs from the collector definition.
      if source_type:
        source_type.conditions = source.get(u'conditions', [])
        source_type.returned_types = source.get(u'returned_types', [])
        self._ReadSupportedOS(yaml_definition, source_type, name)

    # TODO: check conditions.
    artifact_definition.conditions = yaml_definition.get(u'conditions', [])
    artifact_definition.provides = yaml_definition.get(u'provides', [])
    self._ReadLabels(yaml_definition, artifact_definition, name)
    self._ReadSupportedOS(yaml_definition, artifact_definition, name)
    artifact_definition.urls = yaml_definition.get(u'urls', [])

    return artifact_definition

  def _ReadLabels(self, yaml_definition, artifact_definition, name):
    """Reads the optional artifact definition labels.

    Args:
      yaml_definition: the YAML artifact definition.
      artifact_definition: the artifact definition object (instance of
                           ArtifactDefinition).
      name: string containing the name of the artifact definition.

    Raises:
      FormatError: if there are undefined labels.
    """
    labels = yaml_definition.get(u'labels', [])
    undefined_labels = [
        item for item in labels if item not in definitions.LABELS]

    if undefined_labels:
      raise errors.FormatError(
          u'Artifact definition: {0:s} label(s): {1:s} not defined.'.format(
              name, ', '.join(undefined_labels)))

    artifact_definition.labels = yaml_definition.get(u'labels', [])

  def _ReadSupportedOS(self, yaml_definition, definition_object, name):
    """Reads the optional artifact or source type supported OS.

    Args:
      yaml_definition: the YAML artifact definition.
      definition_object: the definition object (instance of ArtifactDefinition
                        or SourceType).
      name: string containing the name of the artifact definition.

    Raises:
      FormatError: if there are undefined supported operating systems.
    """
    supported_os = yaml_definition.get(u'supported_os', [])

    if not isinstance(supported_os, list):
      raise errors.FormatError(
          u'supported_os must be a list of strings, got: {0:s}'.format(
              supported_os))

    undefined_supported_os = [
        item for item in supported_os if item not in definitions.SUPPORTED_OS]

    if undefined_supported_os:
      raise errors.FormatError((
          u'Artifact definition: {0:s} supported operating system: {1:s} '
          u'not defined.').format(name, u', '.join(undefined_supported_os)))

    definition_object.supported_os = supported_os

  def ReadFileObject(self, file_object):
    """Reads artifact definitions from a file-like object.

    Args:
      file_object: the file-like object to read from.

    Yields:
      Artifact definitions (instances of ArtifactDefinition).
    """
    # TODO: add try, except?
    yaml_generator = yaml.safe_load_all(file_object)

    for yaml_definition in yaml_generator:
      yield self._ReadArtifactDefinition(yaml_definition)

  def ReadFile(self, filename):
    """Reads artifact definitions from a YAML file.

    Args:
      filename: the name of the file to read from.

    Yields:
      Artifact definitions (instances of ArtifactDefinition).
    """
    with open(filename, 'rb') as file_object:
      for artifact_definition in self.ReadFileObject(file_object):
        yield artifact_definition

  def ReadDirectory(self, path, extension=u'yaml', ignore_list=None):
    """Reads artifact definitions from YAML files in a directory.

    This function does not recurse sub directories.

    Args:
      path: the path of the directory to read from.
      extension: optional extension of the filenames to read.
                 The default is 'yaml'.
      ignore_list: optional list of filenames to ignore. The default is None.

    Yields:
      Artifact definitions (instances of ArtifactDefinition).
    """
    if extension:
      glob_spec = os.path.join(path, u'*.{0:s}'.format(extension))
    else:
      glob_spec = os.path.join(path, u'*')

    for yaml_file in glob.glob(glob_spec):
      if ignore_list and yaml_file in ignore_list:
        continue

      for artifact_definition in self.ReadFile(yaml_file):
        yield artifact_definition


class ProvidersReader(object):
  """Class that implements the providers reader interface."""

  @abc.abstractmethod
  def ReadFileObject(self, file_object):
    """Reads providers definitions from a file-like object.

    Args:
      file_object: the file-like object to read from.

    Yields:
      Provider definitions (instances of ProviderDefinition).
    """

  @abc.abstractmethod
  def ReadFile(self, filename):
    """Reads provider definitions from a file.

    Args:
      filename: the name of the file to read from.

    Yields:
      Provider definitions (instances of ProviderDefinition).
    """


class YamlProvidersReader(ProvidersReader):
  """Class that implements the YAML providers reader."""

  def _ReadMetadata(self, yaml_definition):
    """Reads the metadata.

    Args:
      yaml_definition: the YAML metadata definition.

    Raises:
      FormatError: if the format of the YAML metadata definition is not set
                   or not supported.
    """
    if not yaml_definition:
      raise errors.FormatError(u'Missing YAML definition.')

    format_version = yaml_definition.get(u'_format_version', None)
    if format_version != 20150618:
      raise errors.FormatError(u'Unsupported format version: {0!s}.'.format(
          format_version))

    definition_type = yaml_definition.get(u'_definition_type', None)
    if definition_type != 'provider':
      raise errors.FormatError(u'Unsupported definition type: {0!s}.'.format(
          definition_type))

  def _ReadProviderDefinition(self, yaml_definition):
    """Reads an provider definition.

    Args:
      yaml_definition: the YAML provider definition.

    Returns:
      An provider definition (instance of ProviderDefinition) or None.

    Raises:
      FormatError: if the format of the YAML provider definition is not set
                   or incorrect.
    """
    if not yaml_definition:
      raise errors.FormatError(u'Missing YAML definition.')

    name = yaml_definition.get(u'name', None)
    if not name:
      raise errors.FormatError(u'Invalid provider definition missing name.')

    # The description is assumed to be mandatory.
    description = yaml_definition.get(u'doc', None)
    if not description:
      raise errors.FormatError(
          u'Invalid provider definition: {0:s} missing description.'.format(
              name))

    provider_definition = provider.ProviderDefinition(
        name, description=description)

    provider_definition.urls = yaml_definition.get(u'urls', [])

    return provider_definition

  def ReadFileObject(self, file_object):
    """Reads provider definitions from a file-like object.

    Args:
      file_object: the file-like object to read from.

    Yields:
      Provider definitions (instances of ProviderDefinition).
    """
    # TODO: add try, except?
    yaml_generator = yaml.safe_load_all(file_object)

    for index, yaml_definition in enumerate(yaml_generator):
      if index == 0:
        self._ReadMetadata(yaml_definition)
      else:
        provider_definition = self._ReadProviderDefinition(yaml_definition)
        if provider_definition:
          yield provider_definition

  def ReadFile(self, filename):
    """Reads provider definitions from a YAML file.

    Args:
      filename: the name of the file to read from.

    Yields:
      Provider definitions (instances of ProviderDefinition).
    """
    with open(filename, 'rb') as file_object:
      for provider_definition in self.ReadFileObject(file_object):
        yield provider_definition
