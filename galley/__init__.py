#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

GALLEYENV = None

__all__ = ['__version__']

import pbr.version

version_info = pbr.version.VersionInfo('galley')
try:
    __version__ = version_info.version_string()
except AttributeError:
    __version__ = None


def get_environment():
    global GALLEYENV
    return GALLEYENV


def set_environment(environment=None):
    global GALLEYENV
    if environment:
        GALLEYENV = environment
    return GALLEYENV
