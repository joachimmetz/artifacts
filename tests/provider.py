# -*- coding: utf-8 -*-
"""Tests for the provider type objects."""

import unittest

from artifacts import provider


# pylint: disable=unexpected-keyword-arg


class ProviderDefinitionTest(unittest.TestCase):
  """Class to test the artifact provider type."""

  def testInitialize(self):
    """Tests the __init__ function."""
    provider.ProviderDefinition(
        'code_page', description='The system codepage.')

    with self.assertRaises(TypeError):
      provider.ProviderDefinition(
          'code_page', bogus=u'bogus')

    with self.assertRaises(TypeError):
      provider.ProviderDefinition(
          'code_page', description='The system codepage.', bogus=u'bogus')
